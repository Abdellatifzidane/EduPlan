import os
import json
from typing import List
from openai import OpenAI
from datetime import time
from ..models.schemas import (
    NaturalLanguageConstraint,
    ParsedConstraint,
    TeacherAvailability,
    TimeSlot,
    DayOfWeek
)


class ConstraintParser:
    """Agent NLP utilisant Grok (xAI) pour parser les contraintes en langage naturel"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("XAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("XAI_MODEL", "grok-beta")
        # Configuration pour utiliser l'API Grok de xAI
        self.base_url = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def parse(self, constraint: NaturalLanguageConstraint) -> ParsedConstraint:
        """
        Parse une contrainte en langage naturel et la convertit en structure utilisable
        """
        prompt = self._build_prompt(constraint)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": """Tu es un assistant spécialisé dans l'analyse de contraintes de disponibilité pour des plannings scolaires.
                    Tu dois extraire les informations de disponibilité et les retourner au format JSON structuré.

                    Jours valides: lundi, mardi, mercredi, jeudi, vendredi, samedi, dimanche

                    Format de sortie attendu:
                    {
                        "teacher_name": "nom du prof",
                        "availabilities": [
                            {
                                "day": "lundi",
                                "time_slots": [
                                    {"start": "08:00", "end": "13:00"}
                                ]
                            }
                        ]
                    }

                    Si la contrainte indique une INDISPONIBILITÉ (exemple: "je ne serai pas disponible"),
                    inverse la logique pour retourner les créneaux de DISPONIBILITÉ restants dans la journée (08:00-19:00).
                    """
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return self._convert_to_parsed_constraint(result)

    def _build_prompt(self, constraint: NaturalLanguageConstraint) -> str:
        """Construit le prompt pour OpenAI"""
        return f"""
Professeur: {constraint.teacher_name}
Contrainte: {constraint.constraint_text}

Parse cette contrainte et extrais:
1. Les jours de la semaine mentionnés
2. Les créneaux horaires de disponibilité
3. Si c'est une disponibilité ou une indisponibilité

Retourne le résultat au format JSON structuré.

Exemples:
- "Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00"
  → disponible ces jours de 08:00 à 13:00

- "Je ne serai pas disponible mardi et mercredi"
  → indisponible toute la journée mardi et mercredi (donc disponible autres jours)

- "Pas de cours après 16h le vendredi"
  → indisponible vendredi après 16:00 (disponible vendredi avant 16:00)
"""

    def _convert_to_parsed_constraint(self, result: dict) -> ParsedConstraint:
        """Convertit le résultat JSON en ParsedConstraint"""
        availabilities = []

        for avail in result.get("availabilities", []):
            day_str = avail["day"]

            # Mapper le jour français vers l'enum
            day_mapping = {
                "lundi": DayOfWeek.MONDAY,
                "mardi": DayOfWeek.TUESDAY,
                "mercredi": DayOfWeek.WEDNESDAY,
                "jeudi": DayOfWeek.THURSDAY,
                "vendredi": DayOfWeek.FRIDAY,
                "samedi": DayOfWeek.SATURDAY,
                "dimanche": DayOfWeek.SUNDAY,
            }

            day = day_mapping.get(day_str.lower())
            if not day:
                continue

            time_slots = []
            for ts in avail["time_slots"]:
                start = self._parse_time(ts["start"])
                end = self._parse_time(ts["end"])
                time_slots.append(TimeSlot(start=start, end=end))

            availabilities.append(
                TeacherAvailability(
                    teacher_name=result["teacher_name"],
                    day=day,
                    time_slots=time_slots
                )
            )

        return ParsedConstraint(
            teacher_name=result["teacher_name"],
            availabilities=availabilities
        )

    def _parse_time(self, time_str: str) -> time:
        """Parse une heure au format HH:MM"""
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)

    def parse_batch(self, constraints: List[NaturalLanguageConstraint]) -> List[ParsedConstraint]:
        """Parse plusieurs contraintes en batch"""
        return [self.parse(constraint) for constraint in constraints]
