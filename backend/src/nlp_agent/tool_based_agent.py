"""
Agent NLP basé sur des tools pour modifier les plannings
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
from datetime import datetime

from .tools import (
    BaseTool,
    ToolResult,
    DeleteSlotTool,
    AddSlotTool,
    # MoveSlotTool,
    # ModifySlotTool,
    # UpdateConfigTool,
    # RegenerateScheduleTool,
    # QueryScheduleTool
)
from ..services.redis_service import redis_service

logger = logging.getLogger(__name__)


class ToolBasedScheduleAgent:
    """
    Agent conversationnel qui utilise des tools pour modifier le planning
    """

    def __init__(self, api_key: str = None):
        """
        Initialise l'agent avec les tools disponibles

        Args:
            api_key: Clé API pour le LLM (Groq ou OpenAI)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

        # Initialiser le client LLM
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # Initialiser les tools disponibles
        self.tools = self._initialize_tools()
        self.tools_by_name = {tool.name: tool for tool in self.tools}

        logger.info(f"Agent initialisé avec {len(self.tools)} tools")

    def _initialize_tools(self) -> List[BaseTool]:
        """
        Initialise et retourne la liste des tools disponibles

        Returns:
            Liste des instances de tools
        """
        return [
            DeleteSlotTool(),
            AddSlotTool(),
            # MoveSlotTool(),  # TODO: À implémenter
            # ModifySlotTool(),  # TODO: À implémenter
            # UpdateConfigTool(),
            # RegenerateScheduleTool(),
            # QueryScheduleTool()
        ]

    def _get_tools_definitions(self) -> List[Dict[str, Any]]:
        """
        Retourne les définitions des tools pour le LLM

        Returns:
            Liste des définitions au format OpenAI function calling
        """
        return [
            {
                "type": "function",
                "function": tool.get_tool_definition()
            }
            for tool in self.tools
        ]

    def _build_system_prompt(self) -> str:
        """
        Construit le prompt système pour l'agent

        Returns:
            Prompt système détaillé
        """
        return """Tu es un assistant intelligent spécialisé dans la gestion de plannings scolaires.
Tu as accès à des outils (tools) pour modifier le planning existant.

RÈGLES IMPORTANTES:
1. Analyse la demande de l'utilisateur pour comprendre l'intention
2. Choisis le ou les tools appropriés pour répondre à la demande
3. Tu peux utiliser plusieurs tools si nécessaire
4. Si la demande est ambiguë, demande des clarifications
5. Explique toujours ce que tu fais de manière claire

TOOLS DISPONIBLES:
- DeleteSlotTool: Supprimer un ou plusieurs créneaux
- AddSlotTool: Ajouter un nouveau créneau

TOOLS À VENIR:
- MoveSlotTool: Déplacer un créneau vers un autre moment (prochainement)
- ModifySlotTool: Modifier les détails d'un créneau (prochainement)

FORMAT DES RÉPONSES:
- Utilise TOUJOURS les tools quand c'est approprié
- Si tu ne peux pas répondre, explique pourquoi
- Confirme toujours l'action effectuée

JOURS VALIDES: lundi, mardi, mercredi, jeudi, vendredi
FORMAT HEURE: HH:MM (ex: 08:00, 14:30)

Contexte actuel:
- Date: {date}
- Nombre de créneaux dans le planning: {num_slots}
"""

    def process_request(
        self,
        user_message: str,
        current_schedule: List[Dict],
        configuration: Optional[Dict] = None,
        session_id: Optional[str] = None
    ) -> Tuple[bool, str, Optional[List[Dict]], Dict[str, Any]]:
        """
        Traite une demande utilisateur et modifie le planning

        Args:
            user_message: Message de l'utilisateur
            current_schedule: Planning actuel
            configuration: Configuration système
            session_id: ID de session pour l'historique

        Returns:
            Tuple (succès, message, planning_modifié, metadata)
        """
        try:
            # Sauvegarder dans l'historique Redis si disponible
            if session_id and redis_service.is_connected():
                redis_service.save_conversation_message(
                    session_id, "user", user_message
                )

            # Créer le contexte pour le LLM
            context = self._create_context(current_schedule, configuration)

            # Préparer le prompt système
            system_prompt = self._build_system_prompt().format(
                date=datetime.now().strftime("%Y-%m-%d"),
                num_slots=len(current_schedule)
            )

            # Appeler le LLM avec les tools
            response = self._call_llm_with_tools(
                system_prompt,
                user_message,
                context
            )

            # Traiter la réponse
            result = self._process_llm_response(
                response,
                current_schedule,
                configuration
            )

            # Sauvegarder la réponse dans l'historique
            if session_id and redis_service.is_connected():
                redis_service.save_conversation_message(
                    session_id, "assistant", result[1], {"success": result[0]}
                )

            return result

        except Exception as e:
            logger.error(f"Erreur lors du traitement: {e}")
            error_message = f"Désolé, une erreur s'est produite : {str(e)}"

            if session_id and redis_service.is_connected():
                redis_service.save_conversation_message(
                    session_id, "assistant", error_message, {"error": str(e)}
                )

            return False, error_message, None, {"error": str(e)}

    def _create_context(
        self,
        current_schedule: List[Dict],
        configuration: Optional[Dict]
    ) -> str:
        """
        Crée un résumé du contexte actuel pour le LLM

        Args:
            current_schedule: Planning actuel
            configuration: Configuration système

        Returns:
            Contexte formaté en string
        """
        context_parts = []

        # Résumé du planning
        if current_schedule:
            # Grouper par jour
            by_day = {}
            for slot in current_schedule:
                day = slot.get("day", "inconnu")
                if day not in by_day:
                    by_day[day] = []
                by_day[day].append(slot)

            context_parts.append("PLANNING ACTUEL:")
            days_order = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]

            for day in days_order:
                if day in by_day:
                    context_parts.append(f"\n{day.upper()}:")
                    for slot in sorted(by_day[day], key=lambda s: s.get("start_time", "")):
                        start = slot.get("start_time", "")
                        if hasattr(start, 'strftime'):
                            start = start.strftime("%H:%M")
                        else:
                            start = str(start)[:5]

                        end = slot.get("end_time", "")
                        if hasattr(end, 'strftime'):
                            end = end.strftime("%H:%M")
                        else:
                            end = str(end)[:5]

                        context_parts.append(
                            f"  {start}-{end} | {slot.get('teacher')} → "
                            f"{slot.get('class_name')} | {slot.get('room')}"
                        )
        else:
            context_parts.append("PLANNING ACTUEL: Vide")

        # Configuration système
        if configuration:
            context_parts.append("\n\nCONFIGURATION:")
            context_parts.append(f"- Nombre de salles: {configuration.get('num_rooms', 'N/A')}")
            context_parts.append(f"- Nombre de professeurs: {configuration.get('num_teachers', 'N/A')}")
            context_parts.append(f"- Nombre de classes: {configuration.get('num_classes', 'N/A')}")
            context_parts.append(f"- Horaires: {configuration.get('day_start', 'N/A')} - {configuration.get('day_end', 'N/A')}")

        return "\n".join(context_parts)

    def _call_llm_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        context: str
    ) -> Dict[str, Any]:
        """
        Appelle le LLM avec les tools disponibles

        Args:
            system_prompt: Prompt système
            user_message: Message utilisateur
            context: Contexte du planning

        Returns:
            Réponse du LLM
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context}\n\nDemande: {user_message}"}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self._get_tools_definitions(),
                tool_choice="auto",
                temperature=0.1,
                max_tokens=2000
            )

            return response

        except Exception as e:
            logger.error(f"Erreur appel LLM: {e}")
            raise

    def _process_llm_response(
        self,
        response: Any,
        current_schedule: List[Dict],
        configuration: Optional[Dict]
    ) -> Tuple[bool, str, Optional[List[Dict]], Dict[str, Any]]:
        """
        Traite la réponse du LLM et exécute les tools

        Args:
            response: Réponse du LLM
            current_schedule: Planning actuel
            configuration: Configuration système

        Returns:
            Tuple (succès, message, planning_modifié, metadata)
        """
        message = response.choices[0].message

        # Si le LLM veut utiliser un tool
        if message.tool_calls:
            modified_schedule = current_schedule.copy()
            results = []
            all_success = True

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                logger.info(f"Exécution du tool: {tool_name} avec args: {tool_args}")

                # Exécuter le tool
                if tool_name in self.tools_by_name:
                    tool = self.tools_by_name[tool_name]
                    result = tool.execute(tool_args, modified_schedule, configuration)

                    results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": result
                    })

                    if result.status == "success" and result.modified_schedule:
                        modified_schedule = result.modified_schedule

                    if result.status != "success":
                        all_success = False
                else:
                    logger.warning(f"Tool inconnu: {tool_name}")
                    all_success = False

            # Construire le message de réponse
            if all_success:
                messages = [r["result"].message for r in results]
                final_message = " ".join(messages)

                return True, final_message, modified_schedule, {
                    "tools_used": [r["tool"] for r in results],
                    "results": results
                }
            else:
                error_messages = []
                for r in results:
                    if r["result"].status != "success":
                        error_messages.append(f"{r['tool']}: {r['result'].message}")

                return False, " | ".join(error_messages), None, {
                    "tools_used": [r["tool"] for r in results],
                    "results": results
                }

        # Si pas de tool call, c'est une réponse directe
        else:
            return False, message.content, None, {
                "response_type": "direct",
                "message": message.content
            }

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'historique d'une conversation

        Args:
            session_id: ID de la session
            limit: Nombre max de messages

        Returns:
            Liste des messages de l'historique
        """
        if redis_service.is_connected():
            return redis_service.get_conversation_history(session_id, limit)
        return []

    def clear_conversation(self, session_id: str) -> bool:
        """
        Efface l'historique d'une conversation

        Args:
            session_id: ID de la session

        Returns:
            True si effacé avec succès
        """
        if redis_service.is_connected():
            return redis_service.clear_conversation(session_id)
        return False