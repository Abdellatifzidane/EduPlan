from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import time, date
from enum import Enum


class DayOfWeek(str, Enum):
    MONDAY = "lundi"
    TUESDAY = "mardi"
    WEDNESDAY = "mercredi"
    THURSDAY = "jeudi"
    FRIDAY = "vendredi"
    SATURDAY = "samedi"
    SUNDAY = "dimanche"


class TimeSlot(BaseModel):
    start: time
    end: time


class TeacherAvailability(BaseModel):
    teacher_name: str
    day: DayOfWeek
    time_slots: List[TimeSlot]


class SystemConfiguration(BaseModel):
    """Configuration globale du système de planning"""
    num_rooms: int = Field(default=8, description="Nombre de salles disponibles")
    num_teachers: int = Field(default=7, description="Nombre de professeurs")
    num_classes: int = Field(default=3, description="Nombre de classes")

    # Horaires
    day_start: time = Field(default=time(8, 0), description="Début de journée")
    day_end: time = Field(default=time(19, 0), description="Fin de journée")

    # Durées
    session_duration: int = Field(default=90, description="Durée d'une séance en minutes")
    break_duration: int = Field(default=15, description="Pause entre cours en minutes")
    lunch_break_start: time = Field(default=time(13, 0), description="Début pause déjeuner")
    lunch_break_end: time = Field(default=time(14, 0), description="Fin pause déjeuner")

    # Jours
    days_in_person: int = Field(default=4, description="Jours en présentiel par semaine")
    days_remote: int = Field(default=1, description="Jours en distanciel par semaine")
    holidays: List[date] = Field(default_factory=list, description="Jours fériés")

    # Contraintes
    max_hours_per_day_per_teacher: int = Field(default=9, description="Max heures/jour/prof")
    prevent_same_teacher_parallel: bool = Field(default=True, description="Interdire même prof sur 2 classes simultanément")


class TeacherWorkload(BaseModel):
    """Charge de travail d'un professeur"""
    teacher_name: str
    total_hours_per_week: float
    class_assignments: Dict[str, float] = Field(
        description="Ex: {'Classe A': 4.5, 'Classe B': 4.5}"
    )


class NaturalLanguageConstraint(BaseModel):
    """Contrainte en langage naturel"""
    teacher_name: str
    constraint_text: str

    class Config:
        json_schema_extra = {
            "example": {
                "teacher_name": "Lyes",
                "constraint_text": "Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00"
            }
        }


class ParsedConstraint(BaseModel):
    """Contrainte parsée par l'agent NLP"""
    teacher_name: str
    availabilities: List[TeacherAvailability]
    unavailabilities: Optional[List[TeacherAvailability]] = None


class ScheduleRequest(BaseModel):
    """Requête pour générer un planning"""
    configuration: SystemConfiguration
    teacher_workloads: List[TeacherWorkload]
    constraints: List[NaturalLanguageConstraint]


class ScheduleSlot(BaseModel):
    """Un créneau dans le planning"""
    day: DayOfWeek
    start_time: time
    end_time: time
    teacher: str
    class_name: str
    room: str
    subject: Optional[str] = None


class Schedule(BaseModel):
    """Planning généré"""
    schedule_id: str
    created_at: str
    configuration: SystemConfiguration
    slots: List[ScheduleSlot]

    class Config:
        json_schema_extra = {
            "example": {
                "schedule_id": "schedule_2024_01_15",
                "created_at": "2024-01-15T10:30:00",
                "slots": [
                    {
                        "day": "lundi",
                        "start_time": "08:00",
                        "end_time": "09:30",
                        "teacher": "Lyes",
                        "class_name": "Classe A",
                        "room": "Salle 1",
                        "subject": "Mathématiques"
                    }
                ]
            }
        }


class ScheduleResponse(BaseModel):
    """Réponse de l'API avec le planning"""
    success: bool
    message: str
    schedule: Optional[Schedule] = None
    visual_html: Optional[str] = None
