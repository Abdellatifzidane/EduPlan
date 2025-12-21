"""
Classe de base pour tous les tools de l'agent NLP
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ToolStatus(str, Enum):
    """Statut de l'exécution d'un tool"""
    SUCCESS = "success"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"


@dataclass
class ToolResult:
    """Résultat de l'exécution d'un tool"""
    status: ToolStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    modified_schedule: Optional[List] = None
    needs_regeneration: bool = False


class BaseTool(ABC):
    """Classe de base abstraite pour les tools"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "Tool sans description"

    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Retourne le schéma JSON des paramètres attendus par le tool
        Format OpenAI function calling
        """
        pass

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Valide les paramètres avant exécution

        Args:
            params: Paramètres à valider

        Returns:
            True si les paramètres sont valides
        """
        pass

    @abstractmethod
    def execute(
        self,
        params: Dict[str, Any],
        current_schedule: List[Dict],
        configuration: Optional[Dict] = None
    ) -> ToolResult:
        """
        Exécute l'action du tool

        Args:
            params: Paramètres de l'action
            current_schedule: Planning actuel (liste de créneaux)
            configuration: Configuration système (optionnel)

        Returns:
            ToolResult avec le résultat de l'exécution
        """
        pass

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Retourne la définition complète du tool pour l'agent
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_schema()
        }

    @staticmethod
    def parse_time(time_str: str) -> str:
        """
        Parse et normalise une chaîne de temps

        Args:
            time_str: Chaîne de temps (ex: "8h", "08:00", "8:00")

        Returns:
            Format normalisé "HH:MM"
        """
        import re

        # Nettoyer la chaîne
        time_str = time_str.strip().lower()

        # Pattern pour "8h", "8h30", etc.
        match_h = re.match(r'^(\d{1,2})h(\d{0,2})$', time_str)
        if match_h:
            hour = int(match_h.group(1))
            minute = int(match_h.group(2)) if match_h.group(2) else 0
            return f"{hour:02d}:{minute:02d}"

        # Pattern pour "8:00", "08:00", etc.
        match_colon = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
        if match_colon:
            hour = int(match_colon.group(1))
            minute = int(match_colon.group(2))
            return f"{hour:02d}:{minute:02d}"

        # Si rien ne correspond, retourner tel quel
        return time_str

    @staticmethod
    def normalize_day(day_str: str) -> str:
        """
        Normalise le nom d'un jour

        Args:
            day_str: Nom du jour (ex: "Lundi", "lun", "monday")

        Returns:
            Nom normalisé en minuscules
        """
        day_mapping = {
            "lundi": "lundi",
            "lun": "lundi",
            "monday": "lundi",
            "mardi": "mardi",
            "mar": "mardi",
            "tuesday": "mardi",
            "mercredi": "mercredi",
            "mer": "mercredi",
            "wednesday": "mercredi",
            "jeudi": "jeudi",
            "jeu": "jeudi",
            "thursday": "jeudi",
            "vendredi": "vendredi",
            "ven": "vendredi",
            "friday": "vendredi",
            "samedi": "samedi",
            "sam": "samedi",
            "saturday": "samedi",
            "dimanche": "dimanche",
            "dim": "dimanche",
            "sunday": "dimanche"
        }

        day_lower = day_str.strip().lower()
        return day_mapping.get(day_lower, day_lower)

    def find_slot(
        self,
        schedule: List[Dict],
        day: Optional[str] = None,
        start_time: Optional[str] = None,
        teacher: Optional[str] = None,
        class_name: Optional[str] = None,
        room: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Trouve un créneau dans le planning selon les critères

        Args:
            schedule: Planning à parcourir
            day: Jour recherché
            start_time: Heure de début recherchée
            teacher: Professeur recherché
            class_name: Classe recherchée
            room: Salle recherchée

        Returns:
            Le créneau trouvé ou None
        """
        for slot in schedule:
            matches = True

            if day and self.normalize_day(slot.get("day", "")) != self.normalize_day(day):
                matches = False

            if start_time:
                slot_time = slot.get("start_time", "")
                if isinstance(slot_time, str):
                    slot_time = slot_time[:5]  # Prendre seulement HH:MM
                if slot_time != self.parse_time(start_time):
                    matches = False

            if teacher and slot.get("teacher") != teacher:
                matches = False

            if class_name and slot.get("class_name") != class_name:
                matches = False

            if room and slot.get("room") != room:
                matches = False

            if matches:
                return slot

        return None

    def check_conflicts(
        self,
        schedule: List[Dict],
        new_slot: Dict,
        exclude_slot: Optional[Dict] = None
    ) -> List[str]:
        """
        Vérifie les conflits potentiels pour un nouveau créneau

        Args:
            schedule: Planning actuel
            new_slot: Nouveau créneau à vérifier
            exclude_slot: Créneau à exclure de la vérification (pour modification)

        Returns:
            Liste des conflits trouvés
        """
        conflicts = []

        for slot in schedule:
            # Ignorer le créneau à exclure
            if exclude_slot and slot == exclude_slot:
                continue

            # Même jour et heure
            if (self.normalize_day(slot.get("day", "")) == self.normalize_day(new_slot.get("day", "")) and
                slot.get("start_time") == new_slot.get("start_time")):

                # Conflit prof (même prof, 2 classes différentes)
                if slot.get("teacher") == new_slot.get("teacher"):
                    conflicts.append(
                        f"Le professeur {new_slot.get('teacher')} est déjà assigné à {slot.get('class_name')} à cette heure"
                    )

                # Conflit salle
                if slot.get("room") == new_slot.get("room"):
                    conflicts.append(
                        f"La salle {new_slot.get('room')} est déjà occupée par {slot.get('class_name')} à cette heure"
                    )

                # Conflit classe
                if slot.get("class_name") == new_slot.get("class_name"):
                    conflicts.append(
                        f"La classe {new_slot.get('class_name')} a déjà un cours avec {slot.get('teacher')} à cette heure"
                    )

        return conflicts