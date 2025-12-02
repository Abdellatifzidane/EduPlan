from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import uuid

from ..database.database import get_db, init_db
from ..models.schemas import (
    ScheduleRequest,
    ScheduleResponse,
    Schedule,
    NaturalLanguageConstraint
)
from ..scheduler.constraint_solver import ScheduleGenerator
from ..nlp_agent.constraint_parser import ConstraintParser
from ..utils.visualizer import ScheduleVisualizer

app = FastAPI(
    title="EduPlan API",
    description="API pour générer et gérer des plannings scolaires intelligents",
    version="1.0.0"
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
def startup_event():
    """Initialiser la base de données au démarrage"""
    import os
    if os.getenv("DATABASE_URL"):
        try:
            init_db()
            print("✓ Base de données initialisée")
        except Exception as e:
            print(f"⚠ Erreur base de données: {e}")
    else:
        print("ℹ Mode sans base de données")


@app.get("/")
def root():
    """Endpoint racine"""
    return {
        "message": "Bienvenue sur EduPlan API",
        "version": "1.0.0",
        "endpoints": {
            "generate_schedule": "/api/schedule/generate",
            "parse_constraint": "/api/constraint/parse",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Vérifier l'état de l'API"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/constraint/parse", response_model=dict)
async def parse_constraint(constraint: NaturalLanguageConstraint):
    """
    Parse une contrainte en langage naturel

    Exemple:
    ```json
    {
        "teacher_name": "Lyes",
        "constraint_text": "Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00"
    }
    ```
    """
    try:
        parser = ConstraintParser()
        parsed = parser.parse(constraint)
        return {
            "success": True,
            "parsed_constraint": parsed.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du parsing: {str(e)}")


@app.post("/api/schedule/generate", response_model=ScheduleResponse)
async def generate_schedule(
    request: ScheduleRequest
):
    """
    Génère un planning complet basé sur la configuration et les contraintes

    Workflow:
    1. Utilise les disponibilités structurées (ou parse le langage naturel si fourni)
    2. Génère le planning avec OR-Tools
    3. Sauvegarde dans la base de données
    4. Retourne le planning + visualisation HTML
    """
    try:
        # Étape 1: Obtenir les contraintes parsées
        parsed_constraints = []

        # Nouveau format: disponibilités structurées (prioritaire)
        if request.structured_availabilities:
            # Convertir directement en ParsedConstraint
            from ..models.schemas import ParsedConstraint
            parsed_constraints = [
                ParsedConstraint(
                    teacher_name=avail.teacher_name,
                    availabilities=avail.availabilities
                )
                for avail in request.structured_availabilities
            ]
        # Ancien format: langage naturel (deprecated mais gardé pour compatibilité)
        elif request.constraints:
            parser = ConstraintParser()
            parsed_constraints = parser.parse_batch(request.constraints)

        # Étape 2: Générer le planning avec OR-Tools
        generator = ScheduleGenerator(request.configuration)
        slots = generator.generate(
            teacher_workloads=request.teacher_workloads,
            constraints=parsed_constraints
        )

        # Étape 3: Créer l'objet Schedule
        schedule_id = f"schedule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        schedule = Schedule(
            schedule_id=schedule_id,
            created_at=datetime.utcnow().isoformat(),
            configuration=request.configuration,
            slots=slots
        )

        # Étape 4: Générer la visualisation HTML
        visualizer = ScheduleVisualizer()
        html_output = visualizer.render_html(schedule)

        # Étape 5: Sauvegarder dans la base de données (optionnel)
        # TODO: Implémenter la sauvegarde en DB

        return ScheduleResponse(
            success=True,
            message=f"Planning généré avec succès: {len(slots)} créneaux créés",
            schedule=schedule,
            visual_html=html_output
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du planning: {str(e)}"
        )


@app.post("/api/schedule/modify")
async def modify_schedule(
    schedule_id: str,
    new_constraint: NaturalLanguageConstraint
):
    """
    Modifie un planning existant en ajoutant une nouvelle contrainte

    TODO: Implémenter la logique de modification incrémentale
    """
    return {
        "success": False,
        "message": "Feature en développement"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
