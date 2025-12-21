"""
Service Redis pour la gestion du cache et des sessions
"""
import redis
import json
import os
from typing import Optional, Dict, Any, List
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class RedisService:
    """Service pour gérer le cache Redis et les sessions"""

    def __init__(self):
        """Initialiser la connexion Redis"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.cache_ttl = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 heure par défaut

        try:
            # Parser l'URL Redis
            if redis_url.startswith("redis://"):
                redis_url = redis_url.replace("redis://", "")

            host, port = redis_url.split(":")
            self.client = redis.Redis(
                host=host,
                port=int(port),
                db=self.redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Test de connexion
            self.client.ping()
            logger.info(f"✅ Connexion Redis établie sur {host}:{port}")

        except Exception as e:
            logger.error(f"❌ Erreur connexion Redis: {e}")
            # Mode fallback sans Redis
            self.client = None

    def is_connected(self) -> bool:
        """Vérifier si Redis est connecté"""
        if not self.client:
            return False
        try:
            self.client.ping()
            return True
        except:
            return False

    # ========== Cache des plannings ==========

    def cache_schedule(self, schedule_id: str, schedule_data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Mettre en cache un planning"""
        if not self.client:
            return False

        try:
            key = f"schedule:{schedule_id}"
            data = json.dumps(schedule_data)
            ttl = ttl or self.cache_ttl

            self.client.setex(key, ttl, data)
            logger.debug(f"Planning {schedule_id} mis en cache pour {ttl}s")
            return True

        except Exception as e:
            logger.error(f"Erreur cache planning: {e}")
            return False

    def get_cached_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer un planning depuis le cache"""
        if not self.client:
            return None

        try:
            key = f"schedule:{schedule_id}"
            data = self.client.get(key)

            if data:
                logger.debug(f"Planning {schedule_id} trouvé dans le cache")
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Erreur lecture cache planning: {e}")
            return None

    def invalidate_schedule_cache(self, schedule_id: str) -> bool:
        """Invalider le cache d'un planning"""
        if not self.client:
            return False

        try:
            key = f"schedule:{schedule_id}"
            result = self.client.delete(key)
            logger.debug(f"Cache invalidé pour {schedule_id}")
            return result > 0

        except Exception as e:
            logger.error(f"Erreur invalidation cache: {e}")
            return False

    # ========== Sessions utilisateur ==========

    def create_session(self, session_id: str, user_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Créer une session utilisateur"""
        if not self.client:
            return False

        try:
            key = f"session:{session_id}"
            data = json.dumps(user_data)
            self.client.setex(key, ttl, data)
            logger.debug(f"Session {session_id} créée")
            return True

        except Exception as e:
            logger.error(f"Erreur création session: {e}")
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Récupérer une session utilisateur"""
        if not self.client:
            return None

        try:
            key = f"session:{session_id}"
            data = self.client.get(key)

            if data:
                # Renouveler le TTL
                self.client.expire(key, self.cache_ttl)
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Erreur lecture session: {e}")
            return None

    def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """Mettre à jour une session"""
        if not self.client:
            return False

        try:
            key = f"session:{session_id}"
            if self.client.exists(key):
                data = json.dumps(user_data)
                self.client.set(key, data)
                self.client.expire(key, self.cache_ttl)
                logger.debug(f"Session {session_id} mise à jour")
                return True
            return False

        except Exception as e:
            logger.error(f"Erreur mise à jour session: {e}")
            return False

    def delete_session(self, session_id: str) -> bool:
        """Supprimer une session"""
        if not self.client:
            return False

        try:
            key = f"session:{session_id}"
            result = self.client.delete(key)
            logger.debug(f"Session {session_id} supprimée")
            return result > 0

        except Exception as e:
            logger.error(f"Erreur suppression session: {e}")
            return False

    # ========== Historique des conversations avec l'agent ==========

    def save_conversation_message(
        self,
        session_id: str,
        role: str,
        message: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Sauvegarder un message de conversation"""
        if not self.client:
            return False

        try:
            key = f"conversation:{session_id}"

            msg_data = {
                "role": role,
                "message": message,
                "timestamp": self.client.time()[0],
                "metadata": metadata or {}
            }

            # Ajouter à la liste (RPUSH = append)
            self.client.rpush(key, json.dumps(msg_data))

            # Limiter à 100 derniers messages
            self.client.ltrim(key, -100, -1)

            # TTL de 24h pour les conversations
            self.client.expire(key, 86400)

            logger.debug(f"Message ajouté à conversation {session_id}")
            return True

        except Exception as e:
            logger.error(f"Erreur sauvegarde message: {e}")
            return False

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Récupérer l'historique d'une conversation"""
        if not self.client:
            return []

        try:
            key = f"conversation:{session_id}"

            # Récupérer les N derniers messages
            messages = self.client.lrange(key, -limit, -1)

            history = []
            for msg_str in messages:
                try:
                    history.append(json.loads(msg_str))
                except:
                    continue

            logger.debug(f"Récupéré {len(history)} messages pour {session_id}")
            return history

        except Exception as e:
            logger.error(f"Erreur lecture conversation: {e}")
            return []

    def clear_conversation(self, session_id: str) -> bool:
        """Effacer une conversation"""
        if not self.client:
            return False

        try:
            key = f"conversation:{session_id}"
            result = self.client.delete(key)
            logger.debug(f"Conversation {session_id} effacée")
            return result > 0

        except Exception as e:
            logger.error(f"Erreur suppression conversation: {e}")
            return False

    # ========== Cache des résultats de génération ==========

    def cache_generation_result(
        self,
        config_hash: str,
        result_data: Dict[str, Any],
        ttl: int = 1800  # 30 minutes
    ) -> bool:
        """Mettre en cache un résultat de génération"""
        if not self.client:
            return False

        try:
            key = f"generation:{config_hash}"
            data = json.dumps(result_data)
            self.client.setex(key, ttl, data)
            logger.debug(f"Résultat de génération mis en cache: {config_hash[:8]}...")
            return True

        except Exception as e:
            logger.error(f"Erreur cache génération: {e}")
            return False

    def get_cached_generation(self, config_hash: str) -> Optional[Dict[str, Any]]:
        """Récupérer un résultat de génération depuis le cache"""
        if not self.client:
            return None

        try:
            key = f"generation:{config_hash}"
            data = self.client.get(key)

            if data:
                logger.debug(f"Résultat trouvé dans le cache: {config_hash[:8]}...")
                return json.loads(data)
            return None

        except Exception as e:
            logger.error(f"Erreur lecture cache génération: {e}")
            return None

    # ========== Statistiques et monitoring ==========

    def increment_counter(self, counter_name: str, amount: int = 1) -> int:
        """Incrémenter un compteur"""
        if not self.client:
            return 0

        try:
            key = f"counter:{counter_name}"
            new_value = self.client.incrby(key, amount)

            # Reset mensuel
            self.client.expire(key, 2592000)  # 30 jours
            return new_value

        except Exception as e:
            logger.error(f"Erreur incrémentation compteur: {e}")
            return 0

    def get_counter(self, counter_name: str) -> int:
        """Lire la valeur d'un compteur"""
        if not self.client:
            return 0

        try:
            key = f"counter:{counter_name}"
            value = self.client.get(key)
            return int(value) if value else 0

        except Exception as e:
            logger.error(f"Erreur lecture compteur: {e}")
            return 0

    def get_info(self) -> Dict[str, Any]:
        """Obtenir des informations sur Redis"""
        if not self.client:
            return {"connected": False}

        try:
            info = self.client.info()
            return {
                "connected": True,
                "version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "db_keys": self.client.dbsize()
            }

        except Exception as e:
            logger.error(f"Erreur info Redis: {e}")
            return {"connected": False, "error": str(e)}


# Instance singleton
redis_service = RedisService()