# 📅 EduPlan - Générateur de Planning Intelligent

Un système intelligent de génération et modification de plannings scolaires basé sur des contraintes, avec agent IA conversationnel tool-based pour interpréter et modifier les plannings en langage naturel.

## 🎯 Fonctionnalités

### Core Features
- **Génération automatique de planning** : Utilise OR-Tools pour résoudre les contraintes complexes
- **Agent IA Tool-Based** : Agent conversationnel intelligent avec outils pour ajouter/supprimer des créneaux
- **Modification en langage naturel** : Modifiez vos plannings en parlant naturellement
- **API REST FastAPI v2** : Backend performant avec cache Redis
- **Interface Streamlit** : Frontend intuitif pour la configuration et visualisation
- **Visualisation HTML/Plotly** : Affichage professionnel des plannings
- **Architecture Docker** : Déploiement simplifié avec docker-compose

### Infrastructure
- **PostgreSQL** : Stockage persistant des configurations et plannings
- **Redis** : Cache haute performance et sessions conversationnelles
- **Multi-API Support** : Support GROQ, OpenAI, et XAI
- **Adminer** : Interface web pour gérer PostgreSQL
- **Redis Commander** : Visualisation des données Redis en temps réel

## 🏗️ Architecture

### Structure du Projet
- **backend/** : API FastAPI v2.0 avec Redis cache
  - `api/` : Routes API
  - `scheduler/` : Moteur OR-Tools
  - `nlp_agent/` : Agent IA conversationnel tool-based
    - `tools/` : AddSlotTool, DeleteSlotTool
  - `database/` : Modèles SQLAlchemy et CRUD
  - `services/` : Service Redis
  - `models/` : Schémas Pydantic
  - `utils/` : Visualisation HTML/Plotly

- **frontend/** : Interface Streamlit
- **docker-compose.yml** : Orchestration complète
- **data/** : Exemples et migrations

### Services Docker
- **backend** : API FastAPI (port 8000)
- **frontend** : Interface Streamlit (port 8501)
- **postgres** : Base de données PostgreSQL (port 5432)
- **redis** : Cache et sessions (port 6379)
- **adminer** : Interface web PostgreSQL (port 8080)
- **redis-commander** : Interface web Redis (port 8081)

## 🚀 Installation

### Option 1 : Docker (Recommandé)

#### Prérequis
- Docker Desktop ou Docker Engine
- Docker Compose

#### Étapes

1. **Cloner le projet et configurer**
   - Copier `.env.example` vers `.env`
   - Ajouter au moins une clé API : `GROQ_API_KEY`, `OPENAI_API_KEY`, ou `XAI_API_KEY`

2. **Lancer tous les services**
   - `docker-compose up -d`

3. **Accéder aux interfaces**
   - Frontend Streamlit : http://localhost:8501
   - API Documentation : http://localhost:8000/docs
   - Adminer (PostgreSQL) : http://localhost:8080
   - Redis Commander : http://localhost:8081

4. **Arrêter les services**
   - `docker-compose down`

### Option 2 : Installation Manuelle

#### Prérequis
- Python 3.8+
- PostgreSQL 15+
- Redis 7+
- Au moins une clé API (GROQ, OpenAI, ou XAI)

#### Étapes

1. **Environnement Python**
   - Créer environnement virtuel : `python3 -m venv venv`
   - Activer : `source venv/bin/activate` (Linux/Mac) ou `venv\Scripts\activate` (Windows)
   - Installer dépendances : `pip install -r backend/requirements.txt`

2. **Services**
   - Démarrer PostgreSQL et créer la base `eduplan_db`
   - Démarrer Redis

3. **Configuration**
   - Copier `.env.example` vers `.env`
   - Configurer `DATABASE_URL`, `REDIS_URL`, et au moins une clé API

4. **Initialisation**
   - Initialiser la base de données (voir QUICKSTART.md)

## 🎮 Utilisation

### Mode Docker (Recommandé)

Une fois les services lancés avec `docker-compose up -d`, accédez directement aux interfaces :

- **Frontend Streamlit** : http://localhost:8501
- **API Documentation** : http://localhost:8000/docs
- **Adminer (PostgreSQL)** : http://localhost:8080
- **Redis Commander** : http://localhost:8081

### Mode Manuel

1. **Lancer Redis et PostgreSQL**
   - `sudo service postgresql start`
   - `sudo service redis-server start`

2. **Lancer l'API Backend**
   - `cd backend && uvicorn src.api.main:app --reload`
   - API disponible sur http://localhost:8000
   - Documentation sur http://localhost:8000/docs

3. **Lancer l'interface Streamlit**
   - `cd frontend && streamlit run app.py`
   - Interface disponible sur http://localhost:8501

## 📖 Utilisation

### Générer un planning
- Ouvrir l'interface Streamlit sur http://localhost:8501
- Remplir les critères système (salles, profs, classes, horaires)
- Ajouter les charges de travail des professeurs
- Ajouter les contraintes en langage naturel si besoin
- Cliquer sur "Générer le Planning"

### Modifier un planning avec l'agent IA
- Parler naturellement à l'agent : "Ajoute un cours de Python avec Lyes le lundi de 10h à 12h"
- L'agent comprend et applique automatiquement les modifications
- Demander des suppressions : "Supprime tous les cours du vendredi"

### Valider un planning
- Une fois satisfait du planning, le valider pour le sauvegarder définitivement
- Les plannings validés sont marqués avec timestamp et utilisateur

## 📋 Configuration des Critères

### Critères Système
- Nombre de salles, professeurs, classes
- Horaires de journée (début/fin)
- Durée des séances et pauses
- Pause déjeuner
- Jours présentiel/distanciel
- Heures max par jour par professeur

### Charge de Travail
- Nom du professeur
- Heures totales par semaine
- Répartition par classe

### Contraintes en Langage Naturel

Exemples supportés:
- ✅ "Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00"
- ✅ "Je ne serai pas disponible mardi et mercredi"
- ✅ "Pas de cours après 16h le vendredi"
- ✅ "Je préfère enseigner le matin"
- ✅ "Indisponible vendredi après-midi"

## 🔧 Technologies Utilisées

### Backend
- **Framework**: FastAPI v2.0
- **Language**: Python 3.8+
- **Solver**: Google OR-Tools (CP-SAT Solver)
- **AI/LLM**: Support multi-provider (GROQ, OpenAI GPT-4, XAI Grok)
- **Database**: PostgreSQL 15 + SQLAlchemy 2.0
- **Cache**: Redis 7 avec hiredis
- **Tests**: pytest, pytest-asyncio

### Frontend
- **Framework**: Streamlit
- **Visualisation**: Plotly, HTML/CSS

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Database UI**: Adminer
- **Cache UI**: Redis Commander
- **Monitoring**: prometheus-client, python-json-logger

### DevOps
- **Code Quality**: black, isort, mypy, pylint
- **Type Checking**: Pydantic v2

## 📊 Endpoints API v2.0

### Core Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Informations système et features activées |
| GET | `/health` | Health check (API, Redis, PostgreSQL) |
| GET | `/api/system/redis-info` | Informations Redis |
| GET | `/api/statistics` | Statistiques d'utilisation |

### Schedule Management

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/schedule/generate` | Générer un planning (avec cache Redis) |
| POST | `/api/schedule/modify` | Modifier avec agent IA tool-based |
| POST | `/api/schedule/modify/v2` | Version 2 de modification (explicite) |
| POST | `/api/schedule/validate` | Valider un planning (draft → validated) |
| GET | `/api/schedules` | Lister tous les plannings (pagination) |
| GET | `/api/schedules/latest` | Récupérer le dernier planning |
| GET | `/api/schedules/{id}` | Récupérer un planning par ID |
| DELETE | `/api/schedules/{id}` | Supprimer un planning |

### Conversation Management

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/conversation/{session_id}` | Récupérer l'historique de conversation |
| DELETE | `/api/conversation/{session_id}` | Effacer une conversation |

## 🎯 Workflow Complet

### Génération de Planning
1. **Utilisateur** entre les critères et contraintes via Streamlit
2. **Frontend** envoie une requête POST à `/api/schedule/generate`
3. **API** vérifie le cache Redis (hash de configuration)
4. Si non caché :
   - **Solver OR-Tools** génère le planning optimal
   - **Visualizer** crée le rendu HTML/Plotly
   - **PostgreSQL** sauvegarde le planning (état: draft)
   - **Redis** met en cache le résultat
5. **Frontend** affiche le résultat visuel

### Modification Interactive avec Agent IA
1. **Utilisateur** demande modification en langage naturel
2. **Frontend** envoie la demande à `/api/schedule/modify`
3. **Agent Tool-Based** analyse la demande :
   - Identifie l'outil approprié (AddSlotTool, DeleteSlotTool)
   - Extrait les paramètres (jour, horaire, prof, classe, salle)
   - Valide les paramètres
4. **Agent** applique la modification sur le planning
5. **API** :
   - Génère nouveau planning modifié
   - Sauvegarde en PostgreSQL
   - Met en cache Redis
   - Retourne visualisation HTML
6. **Frontend** affiche le planning modifié

### Validation et Archivage
1. **Utilisateur** valide le planning
2. **API** met à jour le statut (draft → validated)
3. **PostgreSQL** sauvegarde l'état validé avec timestamp
4. **Redis** invalide le cache pour forcer rafraîchissement

## 🐛 Troubleshooting

### Mode Docker

#### Services ne démarrent pas
- Vérifier les logs avec `docker-compose logs -f`
- Redémarrer un service : `docker-compose restart backend`
- Reconstruire : `docker-compose up -d --build`

#### PostgreSQL ou Redis non accessible
- Vérifier l'état : `docker-compose ps`
- Vérifier la santé des conteneurs

#### Problème de volumes
- Supprimer et recréer : `docker-compose down -v` puis `docker-compose up -d`

### Mode Manuel

#### Erreur de connexion à l'API
- Vérifiez que le backend tourne sur port 8000
- Consultez les logs backend
- Vérifiez les CORS

#### Erreur Redis
- Vérifier que Redis est lancé : `redis-cli ping`
- Installer si nécessaire : `sudo apt install redis-server`

#### Erreur LLM API
- **GROQ** : Clé gratuite sur https://console.groq.com
- **OpenAI** : Vérifiez quota sur https://platform.openai.com
- **XAI** : Vérifiez clé sur https://x.ai
- Vérifiez les clés dans `.env`

#### Erreur PostgreSQL
- Vérifier que PostgreSQL est lancé
- Tester la connexion
- Vérifier les credentials dans DATABASE_URL

#### Planning impossible à générer
- Réduisez les contraintes
- Augmentez le nombre de salles/créneaux disponibles
- Vérifiez la cohérence des heures assignées
- Consultez les logs

#### Agent ne comprend pas la demande
- Soyez plus explicite
- Incluez tous les paramètres : jour, heure, prof, classe, salle
- Consultez l'historique de conversation

## 🚧 Roadmap et Améliorations Futures

### Version 2.1 (En cours)
- [x] Agent IA tool-based
- [x] Cache Redis des plannings
- [x] Système de validation (draft/validated)
- [x] Support multi-API (GROQ, OpenAI, XAI)
- [x] Architecture Docker complète
- [x] Historique de conversations
- [ ] Tests end-to-end complets
- [ ] Métriques Prometheus

### Version 2.2 (Prévue)
- [ ] Plus d'outils pour l'agent (MoveSlotTool, SwapSlotTool)
- [ ] Export PDF/Excel des plannings
- [ ] Import depuis fichiers Excel/CSV
- [ ] Notifications email/Slack
- [ ] Webhooks pour événements

### Version 3.0 (Future)
- [ ] Gestion multi-utilisateurs et authentification
- [ ] Tableau de bord analytics et KPIs
- [ ] API de synchronisation calendriers (Google Calendar, Outlook)
- [ ] Mode offline avec modèles LLM locaux (Ollama)
- [ ] Interface mobile responsive
- [ ] Support multi-tenant
- [ ] Audit logs complets
- [ ] Rollback de modifications

## 📝 Licence

MIT License

## 👥 Auteur

Projet EduPlan - Générateur de planning intelligent avec NLP
