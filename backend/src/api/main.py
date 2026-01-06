from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, time, date
from typing import List, Optional
import uuid
import os
import hashlib
import json
import logging

from ..database.database import get_db, init_db
from ..database import crud
from ..models.schemas import (
    ScheduleRequest,
    ScheduleResponse,
    Schedule,
    ModificationRequest,
    ModificationResponse
)
from ..scheduler.constraint_solver import ScheduleGenerator
from ..nlp_agent.tool_based_agent import ToolBasedScheduleAgent
from ..utils.visualizer import ScheduleVisualizer
from ..services.redis_service import redis_service

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Custom JSON Encoder pour gérer les objets time et date
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date, time)):
            return obj.isoformat()
        return super().default(obj)

app = FastAPI(
    title="EduPlan API v2",
    description="API améliorée pour générer et gérer des plannings scolaires avec agent IA tool-based",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialiser les services au démarrage"""
    # Base de données
    if os.getenv("DATABASE_URL"):
        try:
            init_db()
            logger.info("✅ Base de données PostgreSQL initialisée")
        except Exception as e:
            logger.error(f"❌ Erreur base de données: {e}")

    # Redis
    if redis_service.is_connected():
        info = redis_service.get_info()
        logger.info(f"✅ Redis connecté - Version: {info.get('version')}")
    else:
        logger.warning("⚠️ Redis non disponible - Mode sans cache")


@app.get("/")
def root():
    """Endpoint racine avec informations système"""
    return {
        "message": "EduPlan API v2.0",
        "status": "operational",
        "features": {
            "tool_based_agent": True,
            "redis_cache": redis_service.is_connected(),
            "postgresql": os.getenv("DATABASE_URL") is not None
        },
        "endpoints": {
            "generate_schedule": "/api/schedule/generate",
            "modify_schedule": "/api/schedule/modify/v2",
            "validate_schedule": "/api/schedule/validate",
            "health": "/health",
            "redis_info": "/api/system/redis-info"
        }
    }


@app.get("/health")
def health_check():
    """Vérifier l'état des services"""
    services_status = {
        "api": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "redis": "healthy" if redis_service.is_connected() else "unavailable",
        "database": "healthy"  # À implémenter: vérification réelle
    }

    # Si un service critique est down, retourner 503
    if services_status["database"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=services_status
        )

    return services_status


@app.get("/api/system/redis-info")
def get_redis_info():
    """Obtenir les informations Redis"""
    if not redis_service.is_connected():
        return {"error": "Redis non disponible"}

    return redis_service.get_info()


@app.post("/api/schedule/generate", response_model=ScheduleResponse)
async def generate_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Génère un planning avec cache Redis

    Workflow amélioré:
    1. Vérifier le cache Redis
    2. Générer le planning si nécessaire
    3. Mettre en cache
    4. Sauvegarder en base (état draft)
    5. Retourner avec visualisation
    """
    try:
        # Créer un hash de la configuration pour le cache
        config_hash = hashlib.md5(
            json.dumps(request.dict(), sort_keys=True, cls=DateTimeEncoder).encode()
        ).hexdigest()

        # Vérifier le cache Redis
        if redis_service.is_connected():
            cached_result = redis_service.get_cached_generation(config_hash)
            if cached_result:
                logger.info(f"✨ Planning trouvé dans le cache: {config_hash[:8]}...")
                return ScheduleResponse(**cached_result)

        # Obtenir les contraintes parsées
        parsed_constraints = []

        if request.structured_availabilities:
            from ..models.schemas import ParsedConstraint
            parsed_constraints = [
                ParsedConstraint(
                    teacher_name=avail.teacher_name,
                    availabilities=avail.availabilities
                )
                for avail in request.structured_availabilities
            ]

        # Générer le planning
        generator = ScheduleGenerator(request.configuration)
        slots = generator.generate(
            teacher_workloads=request.teacher_workloads,
            constraints=parsed_constraints
        )

        # Créer l'objet Schedule
        schedule_id = f"schedule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        schedule = Schedule(
            schedule_id=schedule_id,
            created_at=datetime.utcnow().isoformat(),
            configuration=request.configuration,
            slots=slots
        )

        # Générer la visualisation
        visualizer = ScheduleVisualizer()
        html_output = visualizer.render_html(schedule)

        # Sauvegarder en base (état draft)
        try:
            if db:
                crud.save_schedule(db, schedule, request.teacher_workloads)
                save_message = " (sauvegardé en état draft)"
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            save_message = ""

        # Préparer la réponse
        response = ScheduleResponse(
            success=True,
            message=f"Planning généré: {len(slots)} créneaux{save_message}",
            schedule=schedule,
            visual_html=html_output
        )

        # Mettre en cache Redis
        if redis_service.is_connected():
            # Convertir les objets time en strings pour la sérialisation JSON
            response_dict = json.loads(response.json())
            schedule_dict = json.loads(schedule.json())
            redis_service.cache_generation_result(config_hash, response_dict)
            redis_service.cache_schedule(schedule_id, schedule_dict)

        # Incrémenter le compteur
        if redis_service.is_connected():
            count = redis_service.increment_counter("schedules_generated")
            logger.info(f"📊 Total plannings générés: {count}")

        return response

    except Exception as e:
        logger.error(f"Erreur génération: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération: {str(e)}"
        )


# Alias pour compatibilité avec le frontend
@app.post("/api/schedule/modify", response_model=ModificationResponse)
async def modify_schedule(
    request: ModificationRequest,
    db: Session = Depends(get_db)
):
    """
    Modifie un planning via l'agent tool-based (alias pour compatibilité)

    Redirige vers modify_schedule_v2
    """
    return await modify_schedule_v2(request, db)


@app.post("/api/schedule/modify/v2", response_model=ModificationResponse)
async def modify_schedule_v2(
    request: ModificationRequest,
    db: Session = Depends(get_db)
):
    """
    Modifie un planning via l'agent tool-based

    Version 2 avec:
    - Agent basé sur des tools
    - Historique Redis des conversations
    - Cache des modifications
    """
    try:
        # Générer un session_id si non fourni
        session_id = request.dict().get("session_id") or f"session_{uuid.uuid4().hex}"

        # Initialiser l'agent tool-based
        agent = ToolBasedScheduleAgent()

        # Convertir les slots en format dict si nécessaire
        schedule_slots = []
        for slot in request.current_schedule.slots:
            if hasattr(slot, 'dict'):
                schedule_slots.append(slot.dict())
            else:
                schedule_slots.append(slot)

        # Traiter la demande avec l'agent
        success, message, modified_slots, metadata = agent.process_request(
            user_message=request.user_message,
            current_schedule=schedule_slots,
            configuration=request.current_schedule.configuration.dict() if hasattr(request.current_schedule.configuration, 'dict') else request.current_schedule.configuration,
            session_id=session_id
        )

        # Si modification réussie
        if success and modified_slots:
            # Convertir les slots dicts en objets Pydantic ScheduleSlot
            from ..models.schemas import ScheduleSlot, DayOfWeek
            pydantic_slots = []
            try:
                for slot in modified_slots:
                    if isinstance(slot, dict):
                        # Convertir dict en ScheduleSlot
                        pydantic_slot = ScheduleSlot(
                            day=DayOfWeek(slot['day']),
                            start_time=slot['start_time'],
                            end_time=slot['end_time'],
                            teacher=slot['teacher'],
                            class_name=slot['class_name'],
                            room=slot['room'],
                            subject=slot.get('subject', '')
                        )
                        pydantic_slots.append(pydantic_slot)
                    else:
                        # Déjà un objet Pydantic
                        pydantic_slots.append(slot)

                # Créer le nouveau planning avec les slots Pydantic
                new_schedule_id = f"{request.current_schedule.schedule_id}_mod_{uuid.uuid4().hex[:4]}"
                modified_schedule = Schedule(
                    schedule_id=new_schedule_id,
                    created_at=datetime.utcnow().isoformat(),
                    configuration=request.current_schedule.configuration,
                    slots=pydantic_slots
                )

                # Générer la visualisation HTML
                visualizer = ScheduleVisualizer()
                html_output = visualizer.render_html(modified_schedule)

            except Exception as e:
                logger.error(f"❌ Erreur conversion slots: {e}")
                import traceback
                logger.error(f"Stacktrace: {traceback.format_exc()}")
                raise

            # Sauvegarder en base de données
            save_message = ""
            if db:
                try:
                    # Extraire les teacher_workloads depuis les slots
                    teacher_hours = {}
                    for slot in pydantic_slots:
                        teacher = slot.teacher
                        if teacher not in teacher_hours:
                            teacher_hours[teacher] = 0.0
                        # Calculer la durée du créneau (en heures)
                        start = slot.start_time
                        end = slot.end_time
                        # Convertir les objets time en datetime pour calculer la durée
                        if isinstance(start, time):
                            # Convertir time vers datetime pour calculer la différence
                            from datetime import datetime as dt
                            start_dt = dt.combine(dt.today(), start)
                            end_dt = dt.combine(dt.today(), end)
                            duration = (end_dt - start_dt).total_seconds() / 3600
                            teacher_hours[teacher] += duration
                        elif isinstance(start, str):
                            # Parse string vers datetime
                            from datetime import datetime as dt
                            start_dt = dt.strptime(start, "%H:%M:%S")
                            end_dt = dt.strptime(end, "%H:%M:%S")
                            duration = (end_dt - start_dt).total_seconds() / 3600
                            teacher_hours[teacher] += duration

                    # Créer la liste de TeacherWorkload
                    from ..models.schemas import TeacherWorkload
                    teacher_workloads = [
                        TeacherWorkload(
                            teacher_name=teacher,
                            total_hours_per_week=hours,
                            class_assignments={}
                        )
                        for teacher, hours in teacher_hours.items()
                    ]

                    # Sauvegarder le planning modifié
                    crud.save_schedule(db, modified_schedule, teacher_workloads)
                    save_message = " et sauvegardé en base de données"
                    logger.info(f"✅ Planning modifié {new_schedule_id} sauvegardé en DB")

                    # Incrémenter le compteur et mettre en cache
                    if redis_service.is_connected():
                        redis_service.increment_counter("modifications_applied")
                        # Cache Redis du planning modifié
                        modified_schedule_dict = json.loads(modified_schedule.json())
                        redis_service.cache_schedule(new_schedule_id, modified_schedule_dict)

                except Exception as e:
                    logger.error(f"❌ Erreur sauvegarde modification: {e}")
                    import traceback
                    logger.error(f"Stacktrace: {traceback.format_exc()}")
                    save_message = " (non sauvegardé en base)"

            return ModificationResponse(
                success=True,
                message=f"{message}{save_message}",
                action_taken=metadata,
                modified_schedule=modified_schedule,
                visual_html=html_output
            )

        # Si clarification nécessaire ou erreur
        else:
            return ModificationResponse(
                success=False,
                message=message,
                action_taken=metadata,
                modified_schedule=None
            )

    except Exception as e:
        logger.error(f"Erreur modification v2: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la modification: {str(e)}"
        )


from pydantic import BaseModel

class ValidateScheduleRequest(BaseModel):
    schedule_id: str
    validated_by: Optional[str] = "user"

@app.post("/api/schedule/validate")
async def validate_schedule(
    request: ValidateScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Valide un planning (passe de draft à validated)

    Args:
        schedule_id: ID du planning à valider
        validated_by: Identifiant de l'utilisateur validant
    """
    try:
        if not db:
            raise HTTPException(
                status_code=503,
                detail="Base de données non disponible"
            )

        # Récupérer le planning
        schedule = crud.get_schedule_by_id(db, request.schedule_id)
        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=f"Planning {request.schedule_id} non trouvé"
            )

        # Mettre à jour le statut
        schedule.status = "validated"
        schedule.validated_at = datetime.utcnow()
        schedule.validated_by = request.validated_by

        db.commit()
        db.refresh(schedule)

        # Invalider le cache Redis
        if redis_service.is_connected():
            redis_service.invalidate_schedule_cache(request.schedule_id)

        # Incrémenter le compteur
        if redis_service.is_connected():
            count = redis_service.increment_counter("schedules_validated")

        return {
            "success": True,
            "message": f"Planning {request.schedule_id} validé avec succès",
            "validated_at": schedule.validated_at.isoformat(),
            "validated_by": request.validated_by
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur validation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la validation: {str(e)}"
        )


@app.get("/api/schedules/latest")
async def get_latest_schedule(db: Session = Depends(get_db)):
    """
    Récupère le dernier planning créé ou modifié
    """
    try:
        if not db:
            return {
                "success": False,
                "message": "Base de données non disponible",
                "schedule": None
            }

        # Récupérer le dernier planning
        latest_schedule = crud.get_latest_schedule(db)

        if not latest_schedule:
            return {
                "success": False,
                "message": "Aucun planning disponible",
                "schedule": None
            }

        # Convertir en format schema
        schedule = crud.convert_db_schedule_to_schema(latest_schedule)

        # Générer la visualisation HTML
        visualizer = ScheduleVisualizer()
        html_output = visualizer.render_html(schedule)

        return {
            "success": True,
            "message": "Planning récupéré avec succès",
            "schedule": schedule,
            "visual_html": html_output
        }

    except Exception as e:
        logger.error(f"Erreur récupération dernier planning: {e}")
        return {
            "success": False,
            "message": f"Erreur: {str(e)}",
            "schedule": None
        }

@app.get("/api/schedules")
async def get_schedules(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Récupérer les plannings avec filtre par statut

    Args:
        status: Filtrer par statut (draft, validated, archived)
        skip: Pagination
        limit: Limite de résultats
    """
    try:
        # TODO: Ajouter le filtre par statut dans crud
        schedules = crud.get_all_schedules(db, skip=skip, limit=limit)

        result = []
        for schedule_model in schedules:
            # Vérifier le cache Redis
            if redis_service.is_connected():
                cached = redis_service.get_cached_schedule(schedule_model.schedule_id)
                if cached:
                    result.append(cached)
                    continue

            # Sinon, construire depuis la DB
            result.append({
                "schedule_id": schedule_model.schedule_id,
                "created_at": schedule_model.created_at.isoformat(),
                "status": getattr(schedule_model, 'status', 'draft'),
                "validated_at": getattr(schedule_model, 'validated_at', None),
                "num_slots": len(schedule_model.slots),
                "configuration": {
                    "num_rooms": schedule_model.configuration.num_rooms,
                    "num_teachers": schedule_model.configuration.num_teachers,
                    "num_classes": schedule_model.configuration.num_classes
                }
            })

        return {
            "success": True,
            "count": len(result),
            "schedules": result,
            "pagination": {
                "skip": skip,
                "limit": limit
            }
        }

    except Exception as e:
        logger.error(f"Erreur récupération plannings: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur: {str(e)}"
        )


@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """
    Supprimer un planning de la base de données

    Args:
        schedule_id: ID du planning à supprimer
    """
    try:
        # Supprimer de la base de données
        deleted = crud.delete_schedule(db, schedule_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Planning {schedule_id} non trouvé"
            )

        # Invalider le cache Redis
        if redis_service.is_connected():
            redis_service.invalidate_schedule_cache(schedule_id)

        return {
            "success": True,
            "message": f"Planning {schedule_id} supprimé avec succès"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur suppression planning: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression: {str(e)}"
        )


@app.get("/api/schedules/{schedule_id}")
async def get_schedule_by_id(schedule_id: str, db: Session = Depends(get_db)):
    """
    Récupérer un planning complet par son ID

    Args:
        schedule_id: ID du planning
    """
    try:
        # Vérifier d'abord le cache Redis
        if redis_service.is_connected():
            cached = redis_service.get_cached_schedule(schedule_id)
            if cached:
                return {
                    "success": True,
                    "schedule": cached,
                    "source": "cache"
                }

        # Sinon, récupérer depuis la DB
        schedule_model = crud.get_schedule_by_id(db, schedule_id)

        if not schedule_model:
            raise HTTPException(status_code=404, detail="Planning non trouvé")

        # Convertir en format schema
        schedule = crud.convert_db_schedule_to_schema(schedule_model)

        # Générer la visualisation
        visualizer = ScheduleVisualizer()
        html_output = visualizer.render_html(schedule)

        return {
            "success": True,
            "schedule": schedule.dict(),
            "visual_html": html_output,
            "source": "database"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération planning: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")


@app.get("/api/conversation/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 50):
    """
    Récupère l'historique d'une conversation avec l'agent

    Args:
        session_id: ID de la session
        limit: Nombre max de messages
    """
    if not redis_service.is_connected():
        return {
            "success": False,
            "message": "Redis non disponible",
            "history": []
        }

    agent = ToolBasedScheduleAgent()
    history = agent.get_conversation_history(session_id, limit)

    return {
        "success": True,
        "session_id": session_id,
        "count": len(history),
        "history": history
    }


@app.delete("/api/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """
    Efface l'historique d'une conversation

    Args:
        session_id: ID de la session
    """
    if not redis_service.is_connected():
        return {
            "success": False,
            "message": "Redis non disponible"
        }

    agent = ToolBasedScheduleAgent()
    success = agent.clear_conversation(session_id)

    return {
        "success": success,
        "message": "Conversation effacée" if success else "Erreur lors de la suppression"
    }


@app.get("/api/statistics")
async def get_statistics():
    """Obtenir les statistiques d'utilisation"""
    if not redis_service.is_connected():
        return {"error": "Redis non disponible pour les statistiques"}

    return {
        "schedules_generated": redis_service.get_counter("schedules_generated"),
        "schedules_validated": redis_service.get_counter("schedules_validated"),
        "modifications_applied": redis_service.get_counter("modifications_applied"),
        "cache_hits": redis_service.get_counter("cache_hits"),
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)