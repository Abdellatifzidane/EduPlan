# 📅 EduPlan - Générateur de Planning Intelligent

Un système intelligent de génération et modification de plannings scolaires basé sur des contraintes, avec agent NLP pour interpréter le langage naturel.

## 🎯 Fonctionnalités

- **Génération automatique de planning** : Utilise OR-Tools pour résoudre les contraintes complexes
- **Agent NLP intelligent** : Parse les contraintes en langage naturel via OpenAI
- **API REST FastAPI** : Backend performant et bien documenté
- **Interface Streamlit** : Frontend intuitif pour la configuration et visualisation
- **Visualisation HTML/Plotly** : Affichage professionnel des plannings
- **Base PostgreSQL** : Stockage persistant des configurations et plannings

## 🏗️ Architecture

```
EduPlan/
├── backend/
│   ├── src/
│   │   ├── api/              # FastAPI endpoints
│   │   │   └── main.py       # Routes API
│   │   ├── scheduler/        # Moteur de génération
│   │   │   └── constraint_solver.py  # OR-Tools CSP solver
│   │   ├── nlp_agent/        # Agent NLP
│   │   │   └── constraint_parser.py  # OpenAI parser
│   │   ├── database/         # Modèles DB
│   │   │   ├── models.py     # SQLAlchemy models
│   │   │   └── database.py   # Configuration DB
│   │   ├── models/           # Schémas Pydantic
│   │   │   └── schemas.py
│   │   └── utils/            # Utilitaires
│   │       └── visualizer.py # Génération HTML/Plotly
│   ├── tests/
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   └── app.py               # Application Streamlit
├── data/
│   ├── example_request.json
│   └── migrations/
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Installation

### Prérequis

- Python 3.8+
- PostgreSQL
- Clé API OpenAI

### Étapes

1. **Cloner le projet**
```bash
cd /home/latifsunix/EduPlan
```

2. **Créer l'environnement virtuel**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r backend/requirements.txt
```

4. **Configurer les variables d'environnement**
```bash
cp .env.example .env
nano .env  # Éditer avec vos valeurs
```

Variables requises:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/eduplan_db
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

5. **Créer la base de données PostgreSQL**
```bash
# Se connecter à PostgreSQL
psql -U postgres

# Créer la base
CREATE DATABASE eduplan_db;
\q
```

6. **Initialiser la base de données**
```bash
cd backend
python -c "from src.database.database import init_db; init_db()"
```

## 🎮 Utilisation

### 1. Lancer l'API Backend

```bash
cd backend
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur `http://localhost:8000`

Documentation interactive: `http://localhost:8000/docs`

### 2. Lancer l'interface Streamlit

Dans un autre terminal:

```bash
cd frontend
streamlit run app.py
```

L'interface sera accessible sur `http://localhost:8501`

## 📖 Exemples d'utilisation

### Via l'API (cURL)

```bash
curl -X POST "http://localhost:8000/api/schedule/generate" \
  -H "Content-Type: application/json" \
  -d @data/example_request.json
```

### Via Python

```python
import requests

# Parser une contrainte
response = requests.post(
    "http://localhost:8000/api/constraint/parse",
    json={
        "teacher_name": "Lyes",
        "constraint_text": "Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00"
    }
)
print(response.json())

# Générer un planning
with open('data/example_request.json') as f:
    data = json.load(f)

response = requests.post(
    "http://localhost:8000/api/schedule/generate",
    json=data
)
schedule = response.json()
```

## 📋 Configuration des Critères

### Critères Fixes (Système)

```python
{
  "num_rooms": 8,                    # Nombre de salles
  "num_teachers": 7,                 # Nombre de professeurs
  "num_classes": 3,                  # Nombre de classes
  "day_start": "08:00:00",           # Début journée
  "day_end": "19:00:00",             # Fin journée
  "session_duration": 90,            # Durée séance (min)
  "break_duration": 15,              # Pause entre cours (min)
  "lunch_break_start": "13:00:00",   # Début pause déj
  "lunch_break_end": "14:00:00",     # Fin pause déj
  "days_in_person": 4,               # Jours présentiel/semaine
  "days_remote": 1,                  # Jours distanciel/semaine
  "max_hours_per_day_per_teacher": 9,# Max heures/jour/prof
  "prevent_same_teacher_parallel": true  # Interdiction prof en parallèle
}
```

### Charge de Travail des Profs

```python
{
  "teacher_name": "Lyes",
  "total_hours_per_week": 9,
  "class_assignments": {
    "Classe A": 4.5,
    "Classe B": 4.5
  }
}
```

### Contraintes en Langage Naturel

Exemples supportés:

- ✅ "Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00"
- ✅ "Je ne serai pas disponible mardi et mercredi"
- ✅ "Pas de cours après 16h le vendredi"
- ✅ "Je préfère enseigner le matin"
- ✅ "Indisponible vendredi après-midi"

## 🧪 Tests

```bash
cd backend
pytest tests/ -v
```

## 🔧 Technologies Utilisées

- **Backend**: FastAPI, Python 3.8+
- **Résolution de contraintes**: Google OR-Tools (CP-SAT Solver)
- **NLP**: OpenAI GPT-4
- **Database**: PostgreSQL + SQLAlchemy
- **Frontend**: Streamlit
- **Visualisation**: Plotly, HTML/CSS
- **Tests**: pytest

## 📊 Endpoints API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/` | Racine de l'API |
| GET | `/health` | Health check |
| POST | `/api/constraint/parse` | Parser une contrainte NL |
| POST | `/api/schedule/generate` | Générer un planning |
| POST | `/api/schedule/modify` | Modifier un planning (TODO) |

## 🎯 Workflow Complet

1. **Utilisateur** entre les critères et contraintes via Streamlit
2. **Frontend** envoie une requête POST à l'API
3. **Agent NLP** parse les contraintes en langage naturel (OpenAI)
4. **Solver OR-Tools** génère le planning optimal
5. **Visualizer** crée le rendu HTML/Plotly
6. **Database** sauvegarde le planning
7. **Frontend** affiche le résultat visuel

## 🐛 Troubleshooting

### Erreur de connexion à l'API
- Vérifiez que le backend tourne sur le port 8000
- Vérifiez les CORS si vous utilisez un autre domaine

### Erreur OpenAI
- Vérifiez votre clé API dans `.env`
- Vérifiez votre quota OpenAI

### Erreur PostgreSQL
- Vérifiez que PostgreSQL est lancé: `sudo service postgresql status`
- Vérifiez les credentials dans `DATABASE_URL`

### Planning impossible à générer
- Réduisez les contraintes
- Augmentez le nombre de salles/créneaux disponibles
- Vérifiez que les heures assignées sont cohérentes

## 🚧 Améliorations Futures

- [ ] Modification incrémentale de planning existant
- [ ] Export PDF/Excel
- [ ] Notifications par email
- [ ] Gestion multi-utilisateurs
- [ ] Tableau de bord analytics
- [ ] API de synchronisation avec calendriers (Google Calendar, Outlook)
- [ ] Mode offline avec modèles NLP locaux (spaCy)

## 📝 Licence

MIT License

## 👥 Auteur

Projet EduPlan - Générateur de planning intelligent avec NLP
