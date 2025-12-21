"""
Agent conversationnel pour modifier un planning existant via langage naturel
"""
import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
from ..models.schemas import ScheduleSlot, DayOfWeek
from datetime import time


class AgentModifier:
    """
    Agent IA qui comprend les modifications demandées en langage naturel
    et génère les actions à effectuer sur le planning
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "llama-3.3-70b-versatile"

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def parse_modification_request(
        self,
        user_message: str,
        current_schedule: List[ScheduleSlot]
    ) -> Dict[str, Any]:
        """
        Parse une demande de modification en langage naturel

        Exemples de commandes supportées:
        - "Supprimer le cours de Prof_1 le lundi à 8h"
        - "Déplacer le cours de maths du mardi 10h au mercredi 14h"
        - "Ajouter un cours de Prof_2 pour Classe A le jeudi de 9h à 10h30"
        - "Changer la salle du cours de Prof_1 lundi 8h de Salle 1 à Salle 5"
        - "Supprimer tous les cours du vendredi"
        - "Prof_3 ne sera plus disponible le mardi"
        """

        # Construire le contexte du planning actuel
        schedule_summary = self._summarize_schedule(current_schedule)

        system_prompt = """Tu es un assistant IA spécialisé dans la modification de plannings scolaires.

Tu reçois des demandes en langage naturel et tu dois les convertir en actions structurées JSON.

ACTIONS DISPONIBLES:
1. "delete" - Supprimer un créneau
2. "move" - Déplacer un créneau
3. "add" - Ajouter un créneau
4. "modify" - Modifier un créneau (changer salle, prof, classe)
5. "delete_all" - Supprimer plusieurs créneaux selon critères

FORMAT DE RÉPONSE (JSON):
{
    "action": "delete|move|add|modify|delete_all",
    "parameters": {
        // Pour delete:
        "day": "lundi",
        "start_time": "08:00",
        "teacher": "Prof_1",
        "class": "Classe A"

        // Pour move:
        "from": {"day": "lundi", "start_time": "08:00", "teacher": "Prof_1"},
        "to": {"day": "mercredi", "start_time": "14:00"}

        // Pour add:
        "day": "jeudi",
        "start_time": "09:00",
        "end_time": "10:30",
        "teacher": "Prof_2",
        "class": "Classe A",
        "room": "Salle 3"

        // Pour modify:
        "selector": {"day": "lundi", "start_time": "08:00", "teacher": "Prof_1"},
        "changes": {"room": "Salle 5"}

        // Pour delete_all:
        "criteria": {"day": "vendredi"} ou {"teacher": "Prof_2"}
    },
    "confirmation_message": "Je vais supprimer le cours de Prof_1 le lundi à 8h",
    "reasoning": "L'utilisateur a demandé de supprimer ce cours spécifique"
}

Jours valides: lundi, mardi, mercredi, jeudi, vendredi
Format heure: "HH:MM" (24h)

Si la demande est ambiguë ou impossible, retourne:
{
    "action": "clarification_needed",
    "message": "Pouvez-vous préciser quel cours exactement ?",
    "suggestions": ["option 1", "option 2"]
}
"""

        user_prompt = f"""Planning actuel:
{schedule_summary}

Demande de l'utilisateur: "{user_message}"

Analyse cette demande et génère l'action JSON correspondante."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            return {
                "action": "error",
                "message": f"Erreur lors de l'analyse: {str(e)}"
            }

    def _summarize_schedule(self, schedule: List[ScheduleSlot]) -> str:
        """Créer un résumé textuel du planning pour le LLM"""
        if not schedule:
            return "Planning vide"

        lines = ["PLANNING ACTUEL:"]

        # Grouper par jour
        by_day = {}
        for slot in schedule:
            day = slot.day.value
            if day not in by_day:
                by_day[day] = []
            by_day[day].append(slot)

        days_order = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]

        for day in days_order:
            if day in by_day:
                lines.append(f"\n{day.upper()}:")
                for slot in sorted(by_day[day], key=lambda s: s.start_time):
                    lines.append(
                        f"  {slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')} | "
                        f"{slot.teacher} → {slot.class_name} | {slot.room}"
                    )

        return "\n".join(lines)

    def apply_modification(
        self,
        action_data: Dict[str, Any],
        current_schedule: List[ScheduleSlot]
    ) -> tuple[List[ScheduleSlot], str]:
        """
        Applique la modification au planning

        Returns:
            (nouveau_planning, message_confirmation)
        """
        action = action_data.get("action")
        params = action_data.get("parameters", {})

        if action == "delete":
            return self._apply_delete(current_schedule, params)

        elif action == "move":
            return self._apply_move(current_schedule, params)

        elif action == "add":
            return self._apply_add(current_schedule, params)

        elif action == "modify":
            return self._apply_modify(current_schedule, params)

        elif action == "delete_all":
            return self._apply_delete_all(current_schedule, params)

        else:
            return current_schedule, f"Action '{action}' non reconnue"

    def _apply_delete(self, schedule: List[ScheduleSlot], params: Dict) -> tuple:
        """Supprimer un créneau spécifique"""
        new_schedule = []
        deleted_count = 0

        for slot in schedule:
            should_delete = True

            # Vérifier tous les critères
            if "day" in params and slot.day.value != params["day"]:
                should_delete = False
            if "start_time" in params and slot.start_time.strftime("%H:%M") != params["start_time"]:
                should_delete = False
            if "teacher" in params and slot.teacher != params["teacher"]:
                should_delete = False
            if "class" in params and slot.class_name != params["class"]:
                should_delete = False

            if not should_delete:
                new_schedule.append(slot)
            else:
                deleted_count += 1

        message = f"✅ {deleted_count} créneau(x) supprimé(s)"
        return new_schedule, message

    def _apply_move(self, schedule: List[ScheduleSlot], params: Dict) -> tuple:
        """Déplacer un créneau"""
        new_schedule = []
        moved = False

        from_criteria = params.get("from", {})
        to_data = params.get("to", {})

        for slot in schedule:
            # Identifier le créneau à déplacer
            should_move = True
            if "day" in from_criteria and slot.day.value != from_criteria["day"]:
                should_move = False
            if "start_time" in from_criteria and slot.start_time.strftime("%H:%M") != from_criteria["start_time"]:
                should_move = False
            if "teacher" in from_criteria and slot.teacher != from_criteria["teacher"]:
                should_move = False

            if should_move and not moved:
                # Modifier le créneau
                moved_slot = ScheduleSlot(
                    day=DayOfWeek(to_data.get("day", slot.day.value)),
                    start_time=self._parse_time(to_data.get("start_time", slot.start_time.strftime("%H:%M"))),
                    end_time=self._parse_time(to_data.get("end_time", slot.end_time.strftime("%H:%M"))),
                    teacher=to_data.get("teacher", slot.teacher),
                    class_name=to_data.get("class", slot.class_name),
                    room=to_data.get("room", slot.room)
                )
                new_schedule.append(moved_slot)
                moved = True
            else:
                new_schedule.append(slot)

        message = "✅ Créneau déplacé" if moved else "❌ Créneau non trouvé"
        return new_schedule, message

    def _apply_add(self, schedule: List[ScheduleSlot], params: Dict) -> tuple:
        """Ajouter un nouveau créneau"""
        try:
            new_slot = ScheduleSlot(
                day=DayOfWeek(params["day"]),
                start_time=self._parse_time(params["start_time"]),
                end_time=self._parse_time(params["end_time"]),
                teacher=params["teacher"],
                class_name=params["class"],
                room=params.get("room", "Salle non assignée")
            )

            new_schedule = schedule + [new_slot]
            return new_schedule, f"✅ Créneau ajouté: {params['teacher']} → {params['class']} le {params['day']}"

        except Exception as e:
            return schedule, f"❌ Erreur lors de l'ajout: {str(e)}"

    def _apply_modify(self, schedule: List[ScheduleSlot], params: Dict) -> tuple:
        """Modifier un créneau existant"""
        new_schedule = []
        modified = False

        selector = params.get("selector", {})
        changes = params.get("changes", {})

        for slot in schedule:
            # Identifier le créneau à modifier
            should_modify = True
            if "day" in selector and slot.day.value != selector["day"]:
                should_modify = False
            if "start_time" in selector and slot.start_time.strftime("%H:%M") != selector["start_time"]:
                should_modify = False
            if "teacher" in selector and slot.teacher != selector["teacher"]:
                should_modify = False

            if should_modify and not modified:
                # Appliquer les changements
                modified_slot = ScheduleSlot(
                    day=DayOfWeek(changes.get("day", slot.day.value)),
                    start_time=self._parse_time(changes.get("start_time", slot.start_time.strftime("%H:%M"))),
                    end_time=self._parse_time(changes.get("end_time", slot.end_time.strftime("%H:%M"))),
                    teacher=changes.get("teacher", slot.teacher),
                    class_name=changes.get("class", slot.class_name),
                    room=changes.get("room", slot.room)
                )
                new_schedule.append(modified_slot)
                modified = True
            else:
                new_schedule.append(slot)

        message = "✅ Créneau modifié" if modified else "❌ Créneau non trouvé"
        return new_schedule, message

    def _apply_delete_all(self, schedule: List[ScheduleSlot], params: Dict) -> tuple:
        """Supprimer tous les créneaux correspondant aux critères"""
        criteria = params.get("criteria", {})
        new_schedule = []
        deleted_count = 0

        for slot in schedule:
            should_delete = False

            if "day" in criteria and slot.day.value == criteria["day"]:
                should_delete = True
            if "teacher" in criteria and slot.teacher == criteria["teacher"]:
                should_delete = True
            if "class" in criteria and slot.class_name == criteria["class"]:
                should_delete = True

            if not should_delete:
                new_schedule.append(slot)
            else:
                deleted_count += 1

        return new_schedule, f"✅ {deleted_count} créneau(x) supprimé(s)"

    def _parse_time(self, time_str: str) -> time:
        """Parse une chaîne de temps HH:MM"""
        hour, minute = map(int, time_str.split(":"))
        return time(hour, minute)
