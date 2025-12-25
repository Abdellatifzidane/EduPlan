"""
Tool pour ajouter un créneau dans l'emploi du temps
"""
from typing import Dict, Any, List, Optional
from datetime import time
from .base_tool import BaseTool, ToolResult, ToolStatus


class AddSlotTool(BaseTool):
    """Ajoute un nouveau créneau horaire dans le planning"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "day": {
                    "type": "string",
                    "description": "Jour du nouveau créneau (ex: lundi, mardi...)",
                    "enum": ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
                },
                "start_time": {
                    "type": "string",
                    "description": "Heure de début (format HH:MM, ex: 09:45)"
                },
                "end_time": {
                    "type": "string",
                    "description": "Heure de fin (format HH:MM, ex: 13:00)"
                },
                "teacher": {
                    "type": "string",
                    "description": "Nom du professeur"
                },
                "class_name": {
                    "type": "string",
                    "description": "Nom de la classe (ex: Classe A)"
                },
                "room": {
                    "type": "string",
                    "description": "Nom de la salle (ex: Salle 1)"
                },
                "subject": {
                    "type": "string",
                    "description": "Matière enseignée (optionnel)",
                    "default": ""
                }
            },
            "required": ["day", "start_time", "end_time", "teacher", "class_name", "room"]
        }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valide que tous les paramètres requis sont fournis"""
        required_fields = ["day", "start_time", "end_time", "teacher", "class_name", "room"]
        return all(field in params for field in required_fields)

    def execute(
        self,
        params: Dict[str, Any],
        current_schedule: List[Dict],
        configuration: Optional[Dict] = None
    ) -> ToolResult:
        """
        Exécute l'ajout d'un créneau

        Args:
            params: Paramètres du nouveau créneau
            current_schedule: Planning actuel
            configuration: Configuration système (non utilisé)

        Returns:
            ToolResult avec le planning modifié
        """
        if not self.validate_params(params):
            return ToolResult(
                status=ToolStatus.VALIDATION_ERROR,
                message="Paramètres manquants. Requis : day, start_time, end_time, teacher, class_name, room",
                data=params
            )

        # Normaliser les paramètres
        try:
            day = self.normalize_day(params["day"])
            start_time = self.parse_time(params["start_time"])
            end_time = self.parse_time(params["end_time"])
        except ValueError as e:
            return ToolResult(
                status=ToolStatus.VALIDATION_ERROR,
                message=f"Erreur de format : {str(e)}",
                data=params
            )

        # Vérifier que end_time > start_time
        if end_time <= start_time:
            return ToolResult(
                status=ToolStatus.VALIDATION_ERROR,
                message="L'heure de fin doit être après l'heure de début",
                data=params
            )

        # Créer le nouveau créneau
        new_slot = {
            "day": day,
            "start_time": start_time,
            "end_time": end_time,
            "teacher": params["teacher"],
            "class_name": params["class_name"],
            "room": params["room"],
            "subject": params.get("subject", "")
        }

        # Vérifier les conflits (optionnel)
        conflicts = self._check_conflicts(new_slot, current_schedule)
        if conflicts:
            conflict_messages = []
            for conflict in conflicts:
                conflict_messages.append(
                    f"{conflict['teacher']} ({conflict['start_time']}-{conflict['end_time']})"
                )
            warning = f" ⚠️ Conflits potentiels détectés : {', '.join(conflict_messages)}"
        else:
            warning = ""

        # Ajouter le créneau au planning
        new_schedule = current_schedule.copy()
        new_schedule.append(new_slot)

        message = (
            f"Créneau ajouté : {params['teacher']} → {params['class_name']} "
            f"le {day} de {start_time} à {end_time} en {params['room']}{warning}"
        )

        return ToolResult(
            status=ToolStatus.SUCCESS,
            message=message,
            data={
                "added_slot": new_slot,
                "conflicts": conflicts
            },
            modified_schedule=new_schedule
        )

    def _check_conflicts(self, new_slot: Dict, schedule: List[Dict]) -> List[Dict]:
        """
        Vérifie les conflits potentiels avec le planning existant

        Args:
            new_slot: Nouveau créneau à ajouter
            schedule: Planning actuel

        Returns:
            Liste des créneaux en conflit
        """
        conflicts = []

        for slot in schedule:
            # Même jour
            if self.normalize_day(slot.get("day", "")) != new_slot["day"]:
                continue

            # Extraire les heures
            slot_start = slot.get("start_time", "")
            slot_end = slot.get("end_time", "")

            # Convertir en string si nécessaire
            if hasattr(slot_start, 'strftime'):
                slot_start = slot_start.strftime("%H:%M")
            else:
                slot_start = str(slot_start)[:5]

            if hasattr(slot_end, 'strftime'):
                slot_end = slot_end.strftime("%H:%M")
            else:
                slot_end = str(slot_end)[:5]

            new_start = new_slot["start_time"]
            new_end = new_slot["end_time"]

            # Vérifier le chevauchement horaire
            if not (new_end <= slot_start or new_start >= slot_end):
                # Il y a chevauchement
                # Conflit si même prof, même classe ou même salle
                if (slot.get("teacher") == new_slot["teacher"] or
                    slot.get("class_name") == new_slot["class_name"] or
                    slot.get("room") == new_slot["room"]):
                    conflicts.append(slot)

        return conflicts
