# 📚 Guide de Migration vers EduPlan v2.0

Ce guide explique comment migrer vers la nouvelle version avec l'architecture améliorée.

## 🎯 Nouvelles Fonctionnalités

### ✨ Frontend
- **Interface claire et moderne** avec thème lumineux
- **Sidebar compact** avec 3 onglets organisés
- **Planning en page principale** (toujours visible)
- **Chat intégré** avec l'agent IA

### 🚀 Backend
- **PostgreSQL** pour stockage persistant avec validation
- **Redis** pour cache et historique des conversations
- **Agent NLP tool-based** : architecture modulaire avec tools spécialisés
- **API v2** avec nouveaux endpoints

### 🤖 Agent IA Amélioré
- Ne génère plus directement le planning
- Utilise des **tools spécialisés** pour chaque action
- Historique des conversations dans Redis
- Meilleure compréhension du contexte

## 📋 Étapes de Migration

### 1. Sauvegarde
```bash
# Sauvegarder votre configuration actuelle
cp .env .env.backup
cp -r backend backend.backup
cp -r frontend frontend.backup
```

### 2. Installation des Nouvelles Dépendances

```bash
# Backend
cd backend
pip install -r requirements_new.txt

# Ou avec Docker
docker-compose build
```

### 3. Configuration des Services

#### PostgreSQL & Redis avec Docker
```bash
# Lancer tous les services
docker-compose up -d

# Ou seulement PostgreSQL et Redis
docker-compose up -d postgres redis
```

#### Sans Docker (installation locale)
```bash
# PostgreSQL
sudo apt install postgresql
sudo -u postgres createdb eduplan_db
sudo -u postgres psql -c "CREATE USER eduplan_user WITH PASSWORD 'eduplan_password';"
sudo -u postgres psql -c "GRANT ALL ON DATABASE eduplan_db TO eduplan_user;"

# Redis
sudo apt install redis-server
sudo service redis-server start
```

### 4. Migration de la Base de Données

```bash
# Initialiser les tables PostgreSQL
cd backend
python -c "
from src.database.database import init_db
init_db()
print('✅ Base de données initialisée')
"
```

### 5. Utiliser la Nouvelle Interface

```bash
# Lancer le nouveau backend
cd backend
uvicorn src.api.main_new:app --reload --port 8000

# Lancer le nouveau frontend
cd frontend
streamlit run app_new.py
```

## 🔄 Changements API

### Endpoints Supprimés
- ❌ `/api/constraint/parse` - Plus nécessaire avec les disponibilités structurées

### Nouveaux Endpoints
- ✅ `/api/schedule/validate` - Valider un planning
- ✅ `/api/schedule/modify/v2` - Modification avec agent tool-based
- ✅ `/api/conversation/{session_id}` - Historique des conversations
- ✅ `/api/statistics` - Statistiques d'utilisation
- ✅ `/api/system/redis-info` - Informations Redis

### Format des Requêtes

#### Ancien format (deprecated)
```json
{
  "constraints": [
    {
      "teacher_name": "Prof_1",
      "constraint_text": "Disponible lundi matin"
    }
  ]
}
```

#### Nouveau format (recommandé)
```json
{
  "structured_availabilities": [
    {
      "teacher_name": "Prof_1",
      "availabilities": [
        {
          "day": "lundi",
          "time_slots": [
            {"start": "08:00", "end": "12:00"}
          ]
        }
      ]
    }
  ]
}
```

## 🐳 Docker Compose

### Services Disponibles

```yaml
# Services principaux
postgres    # Base de données PostgreSQL
redis       # Cache et sessions
backend     # API FastAPI
frontend    # Interface Streamlit

# Services optionnels
adminer           # Interface web PostgreSQL (port 8080)
redis-commander   # Interface web Redis (port 8081)
```

### Commandes Utiles

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f backend

# Redémarrer un service
docker-compose restart backend

# Arrêter tout
docker-compose down

# Arrêter et supprimer les volumes
docker-compose down -v
```

## 🔧 Configuration Environnement

### Variables Requises (.env)

```env
# Base de données
DATABASE_URL=postgresql://eduplan_user:eduplan_password@localhost:5432/eduplan_db

# Redis
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_CACHE_TTL=3600

# LLM (Groq ou OpenAI)
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

## 🧪 Tests

### Tester la Nouvelle API

```python
import requests

# Test de génération avec cache
response = requests.post(
    "http://localhost:8000/api/schedule/generate",
    json={
        "configuration": {...},
        "teacher_workloads": [...],
        "structured_availabilities": [...]
    }
)

# Test de modification avec agent v2
response = requests.post(
    "http://localhost:8000/api/schedule/modify/v2",
    json={
        "current_schedule": {...},
        "user_message": "Supprimer le cours de Prof_1 lundi 8h"
    }
)

# Valider un planning
response = requests.post(
    f"http://localhost:8000/api/schedule/validate",
    params={"schedule_id": "schedule_xxx", "validated_by": "admin"}
)
```

### Vérifier les Services

```bash
# Redis
redis-cli ping
# Réponse: PONG

# PostgreSQL
psql -U eduplan_user -d eduplan_db -c "SELECT version();"

# API Health
curl http://localhost:8000/health
```

## ❓ FAQ

### Q: Puis-je utiliser l'ancienne interface ?
**R:** Oui, l'ancien `app.py` reste fonctionnel. Utilisez `app_new.py` pour la nouvelle interface.

### Q: Les anciens plannings sont-ils compatibles ?
**R:** Oui, le format JSON des plannings reste compatible.

### Q: Redis est-il obligatoire ?
**R:** Non, l'application fonctionne sans Redis mais sans cache ni historique.

### Q: Comment revenir à l'ancienne version ?
**R:** Utilisez vos backups :
```bash
mv backend.backup backend
mv frontend.backup frontend
mv .env.backup .env
```

## 🐛 Troubleshooting

### Erreur de connexion PostgreSQL
```bash
# Vérifier que PostgreSQL est lancé
sudo service postgresql status

# Vérifier les credentials
psql -U eduplan_user -h localhost -d eduplan_db
```

### Erreur Redis
```bash
# Vérifier que Redis est lancé
redis-cli ping

# Si Docker, vérifier le container
docker ps | grep redis
```

### Erreur Agent NLP
```bash
# Vérifier la clé API Groq
curl -H "Authorization: Bearer $GROQ_API_KEY" \
  https://api.groq.com/openai/v1/models
```

## 📞 Support

Pour toute question ou problème :
1. Consultez les logs : `docker-compose logs -f`
2. Vérifiez la configuration : `.env`
3. Testez les services individuellement

---

**Note :** Cette migration apporte des améliorations significatives en termes de performance, UX et fonctionnalités. Prenez le temps de tester en environnement de développement avant de migrer en production.