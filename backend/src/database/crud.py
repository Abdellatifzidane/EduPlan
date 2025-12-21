"""
CRUD operations pour la base de données
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from .models import (
    ScheduleModel,
    ScheduleSlotModel,
    Configuration,
    Teacher
)
from ..models.schemas import Schedule, ScheduleSlot, SystemConfiguration, TeacherWorkload


def save_schedule(db: Session, schedule: Schedule, teacher_workloads: List[TeacherWorkload]) -> ScheduleModel:
    """
    Sauvegarder un planning complet dans la base de données
    """

    # 1. Sauvegarder ou récupérer la configuration
    config = db.query(Configuration).filter(
        Configuration.num_rooms == schedule.configuration.num_rooms,
        Configuration.num_teachers == schedule.configuration.num_teachers,
        Configuration.num_classes == schedule.configuration.num_classes
    ).first()

    if not config:
        config = Configuration(
            name=f"Config_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            num_rooms=schedule.configuration.num_rooms,
            num_teachers=schedule.configuration.num_teachers,
            num_classes=schedule.configuration.num_classes,
            day_start=schedule.configuration.day_start,
            day_end=schedule.configuration.day_end,
            session_duration=schedule.configuration.session_duration,
            break_duration=schedule.configuration.break_duration,
            lunch_break_start=schedule.configuration.lunch_break_start,
            lunch_break_end=schedule.configuration.lunch_break_end,
            days_in_person=schedule.configuration.days_in_person,
            days_remote=schedule.configuration.days_remote,
            max_hours_per_day_per_teacher=schedule.configuration.max_hours_per_day_per_teacher,
            prevent_same_teacher_parallel=schedule.configuration.prevent_same_teacher_parallel
        )
        db.add(config)
        db.flush()

    # 2. Sauvegarder les profs si nécessaire
    for tw in teacher_workloads:
        teacher = db.query(Teacher).filter(Teacher.name == tw.teacher_name).first()
        if not teacher:
            teacher = Teacher(
                name=tw.teacher_name,
                total_hours_per_week=tw.total_hours_per_week,
                class_assignments=tw.class_assignments,
                configuration_id=config.id
            )
            db.add(teacher)

    # 3. Créer le planning
    schedule_model = ScheduleModel(
        schedule_id=schedule.schedule_id,
        configuration_id=config.id,
        created_at=datetime.fromisoformat(schedule.created_at) if isinstance(schedule.created_at, str) else schedule.created_at
    )
    db.add(schedule_model)
    db.flush()

    # 4. Sauvegarder tous les créneaux
    for slot in schedule.slots:
        slot_model = ScheduleSlotModel(
            schedule_id=schedule_model.id,
            day_of_week=slot.day.value,
            start_time=slot.start_time,
            end_time=slot.end_time,
            teacher_name=slot.teacher,
            class_name=slot.class_name,
            room_name=slot.room,
            subject=slot.subject
        )
        db.add(slot_model)

    db.commit()
    db.refresh(schedule_model)

    return schedule_model


def get_all_schedules(db: Session, skip: int = 0, limit: int = 100) -> List[ScheduleModel]:
    """
    Récupérer tous les plannings sauvegardés
    """
    return db.query(ScheduleModel).order_by(ScheduleModel.created_at.desc()).offset(skip).limit(limit).all()


def get_schedule_by_id(db: Session, schedule_id: str) -> Optional[ScheduleModel]:
    """
    Récupérer un planning par son ID
    """
    return db.query(ScheduleModel).filter(ScheduleModel.schedule_id == schedule_id).first()


def get_latest_schedule(db: Session) -> Optional[ScheduleModel]:
    """
    Récupérer le dernier planning créé (le plus récent)
    """
    return db.query(ScheduleModel).order_by(ScheduleModel.created_at.desc()).first()


def delete_schedule(db: Session, schedule_id: str) -> bool:
    """
    Supprimer un planning
    """
    schedule = db.query(ScheduleModel).filter(ScheduleModel.schedule_id == schedule_id).first()
    if schedule:
        # Supprimer les slots associés
        db.query(ScheduleSlotModel).filter(ScheduleSlotModel.schedule_id == schedule.id).delete()
        # Supprimer le planning
        db.delete(schedule)
        db.commit()
        return True
    return False


def convert_db_schedule_to_schema(schedule_model: ScheduleModel) -> Schedule:
    """
    Convertir un ScheduleModel (DB) en Schedule (Pydantic)
    """
    from ..models.schemas import DayOfWeek

    slots = []
    for slot_model in schedule_model.slots:
        slot = ScheduleSlot(
            day=DayOfWeek(slot_model.day_of_week),
            start_time=slot_model.start_time,
            end_time=slot_model.end_time,
            teacher=slot_model.teacher_name,
            class_name=slot_model.class_name,
            room=slot_model.room_name,
            subject=slot_model.subject
        )
        slots.append(slot)

    config = schedule_model.configuration
    system_config = SystemConfiguration(
        num_rooms=config.num_rooms,
        num_teachers=config.num_teachers,
        num_classes=config.num_classes,
        day_start=config.day_start,
        day_end=config.day_end,
        session_duration=config.session_duration,
        break_duration=config.break_duration,
        lunch_break_start=config.lunch_break_start,
        lunch_break_end=config.lunch_break_end,
        days_in_person=config.days_in_person,
        days_remote=config.days_remote,
        max_hours_per_day_per_teacher=config.max_hours_per_day_per_teacher,
        prevent_same_teacher_parallel=config.prevent_same_teacher_parallel
    )

    return Schedule(
        schedule_id=schedule_model.schedule_id,
        created_at=schedule_model.created_at.isoformat(),
        configuration=system_config,
        slots=slots
    )
