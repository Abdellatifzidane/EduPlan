"""
Tool pour supprimer un ou plusieurs créneaux du planning
"""
from typing import Dict, Any, List, Optional
from .base_tool import BaseTool, ToolResult, ToolStatus


class DeleteSlotTool(BaseTool):
    """Supprime un ou plusieurs créneaux du planning selon les critères spécifiés"""

    def get_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "day": {
                    "type": "string",
                    "description": "Jour du créneau à supprimer (ex: lundi, mardi...)",
                    "enum": ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
                },
                "start_time": {
                    "type": "string",
                    "description": "Heure de début du créneau (format HH:MM)"
                },
                "teacher": {
                    "type": "string",
                    "description": "Nom du professeur"
                },
                "class_name": {
                    "type": "string",
                    "description": "Nom de la classe"
                },
                "room": {
                    "type": "string",
                    "description": "Nom de la salle"
                },
                "delete_all_matching": {
                    "type": "boolean",
                    "description": "Si true, supprime tous les créneaux correspondant aux critères",
                    "default": False
                }
            },
            "anyOf": [
                {"required": ["day"]},
                {"required": ["teacher"]},
                {"required": ["class_name"]},
                {"required": ["room"]}
            ]
        }

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """Valide qu'au moins un critère de suppression est fourni"""
        required_fields = ["day", "start_time", "teacher", "class_name", "room"]
        return any(field in params for field in required_fields)

    def execute(
        self,
        params: Dict[str, Any],
        current_schedule: List[Dict],
        configuration: Optional[Dict] = None
    ) -> ToolResult:
        """
        Exécute la suppression de créneaux

        Args:
            params: Critères de suppression
            current_schedule: Planning actuel
            configuration: Configuration système (non utilisé)

        Returns:
            ToolResult avec le planning modifié
        """
        if not self.validate_params(params):
            return ToolResult(
                status=ToolStatus.VALIDATION_ERROR,
                message="Au moins un critère de suppression est requis",
                data=params
            )

        # Normaliser les paramètres
        if "day" in params:
            params["day"] = self.normalize_day(params["day"])
        if "start_time" in params:
            params["start_time"] = self.parse_time(params["start_time"])

        delete_all = params.get("delete_all_matching", False)
        new_schedule = []
        deleted_slots = []
        deleted_count = 0

        for slot in current_schedule:
            should_delete = self._matches_criteria(slot, params)

            if should_delete:
                deleted_slots.append(slot)
                deleted_count += 1
                # Si on ne supprime que le premier match, on arrête
                if not delete_all and deleted_count == 1:
                    # Ajouter le reste des créneaux non vérifiés
                    new_schedule.extend([s for s in current_schedule if s != slot])
                    break
            else:
                new_schedule.append(slot)

        if deleted_count == 0:
            return ToolResult(
                status=ToolStatus.NOT_FOUND,
                message="Aucun créneau correspondant aux critères n'a été trouvé",
                data=params
            )

        # Créer un message descriptif
        message_parts = []
        if deleted_count == 1:
            slot = deleted_slots[0]
            message = f"Créneau supprimé : {slot['teacher']} → {slot['class_name']} le {slot['day']} à {slot['start_time']}"
        else:
            message = f"{deleted_count} créneaux supprimés"
            if params.get("day"):
                message += f" le {params['day']}"
            if params.get("teacher"):
                message += f" pour {params['teacher']}"
            if params.get("class_name"):
                message += f" de la classe {params['class_name']}"

        return ToolResult(
            status=ToolStatus.SUCCESS,
            message=message,
            data={
                "deleted_count": deleted_count,
                "deleted_slots": deleted_slots,
                "criteria": params
            },
            modified_schedule=new_schedule
        )

    def _matches_criteria(self, slot: Dict, criteria: Dict) -> bool:
        """
        Vérifie si un créneau correspond aux critères de suppression

        Args:
            slot: Créneau à vérifier
            criteria: Critères de suppression

        Returns:
            True si le créneau doit être supprimé
        """
        # Si delete_all_matching est False, tous les critères doivent matcher
        # Si delete_all_matching est True, au moins un critère doit matcher
        delete_all = criteria.get("delete_all_matching", False)

        matches = []

        if "day" in criteria:
            day_match = self.normalize_day(slot.get("day", "")) == criteria["day"]
            matches.append(("day", day_match))

        if "start_time" in criteria:
            slot_time = slot.get("start_time", "")
            if isinstance(slot_time, dict):
                slot_time = f"{slot_time.get('hour', 0):02d}:{slot_time.get('minute', 0):02d}"
            elif hasattr(slot_time, 'strftime'):
                slot_time = slot_time.strftime("%H:%M")
            else:
                slot_time = str(slot_time)[:5]

            time_match = slot_time == criteria["start_time"]
            matches.append(("start_time", time_match))

        if "teacher" in criteria:
            teacher_match = slot.get("teacher") == criteria["teacher"]
            matches.append(("teacher", teacher_match))

        if "class_name" in criteria:
            class_match = slot.get("class_name") == criteria["class_name"]
            matches.append(("class_name", class_match))

        if "room" in criteria:
            room_match = slot.get("room") == criteria["room"]
            matches.append(("room", room_match))

        if not matches:
            return False

        # Si on veut supprimer tout ce qui matche au moins un critère
        if delete_all:
            return any(match for _, match in matches)
        # Sinon, tous les critères fournis doivent matcher
        else:
            return all(match for _, match in matches)