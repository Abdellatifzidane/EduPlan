# 🚀 Quick Start Guide - EduPlan

Guide de démarrage rapide pour lancer EduPlan en 5 minutes.

## Étape 1: Installation (2 min)

```bash
# Se placer dans le projet
cd /home/latifsunix/EduPlan

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r backend/requirements.txt
```

## Étape 2: Configuration (1 min)

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos valeurs
nano .env
```

**Minimum requis dans .env:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/eduplan_db
OPENAI_API_KEY=sk-your-key-here
```

## Étape 3: Base de données (1 min)

```bash
# Option A: PostgreSQL local
sudo service postgresql start
psql -U postgres -c "CREATE DATABASE eduplan_db;"

# Option B: SQLite (pour test rapide - modifier DATABASE_URL)
# DATABASE_URL=sqlite:///./eduplan.db
```

## Étape 4: Lancer l'application (1 min)

**Terminal 1 - Backend:**
```bash
cd /home/latifsunix/EduPlan/backend
uvicorn src.api.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd /home/latifsunix/EduPlan/frontend
streamlit run app.py
```

## Étape 5: Utilisation

1. Ouvrir Streamlit: http://localhost:8501
2. Remplir les critères système
3. Ajouter les charges de travail des profs
4. Ajouter les contraintes en langage naturel
5. Cliquer sur "Générer le Planning"

## Exemple Rapide (via API)

```bash
curl -X POST "http://localhost:8000/api/schedule/generate" \
  -H "Content-Type: application/json" \
  -d @data/example_request.json
```

## Test de l'Agent NLP

```python
import requests

response = requests.post(
    "http://localhost:8000/api/constraint/parse",
    json={
        "teacher_name": "Lyes",
        "constraint_text": "Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00"
    }
)

print(response.json())
```

## Dépannage Rapide

**Port déjà utilisé?**
```bash
# Changer le port
uvicorn src.api.main:app --port 8001
streamlit run app.py --server.port 8502
```

**Erreur OpenAI?**
- Vérifiez votre clé API
- Vérifiez votre quota

**Erreur PostgreSQL?**
- Utilisez SQLite pour tester rapidement
- Ou installez PostgreSQL: `sudo apt install postgresql`

## Accès Rapide

- **API Docs**: http://localhost:8000/docs
- **Streamlit**: http://localhost:8501
- **Health Check**: http://localhost:8000/health

Profitez d'EduPlan! 🎉
