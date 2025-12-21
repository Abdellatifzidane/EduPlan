#!/bin/bash

echo "=== Lancement d'EduPlan ==="

# Couleurs pour l'output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérification de PostgreSQL
echo -e "${YELLOW}Vérification de PostgreSQL...${NC}"
if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL est en cours d'exécution${NC}"
else
    echo -e "${RED}✗ PostgreSQL n'est pas démarré${NC}"
    echo "Tentative de démarrage de PostgreSQL..."
    sudo service postgresql start
    sleep 2
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL démarré avec succès${NC}"
    else
        echo -e "${RED}Erreur: Impossible de démarrer PostgreSQL${NC}"
        echo "Veuillez exécuter: ./install_services.sh"
        exit 1
    fi
fi

# Vérification de Redis
echo -e "${YELLOW}Vérification de Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis est en cours d'exécution${NC}"
else
    echo -e "${RED}✗ Redis n'est pas démarré${NC}"
    echo "Tentative de démarrage de Redis..."
    sudo service redis-server start
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Redis démarré avec succès${NC}"
    else
        echo -e "${RED}Erreur: Impossible de démarrer Redis${NC}"
        echo "Veuillez exécuter: ./install_services.sh"
        exit 1
    fi
fi

# Activation de l'environnement virtuel
echo -e "${YELLOW}Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# Lancement du backend en arrière-plan
echo -e "${YELLOW}Lancement du backend FastAPI...${NC}"
cd backend
uvicorn src.api.main_new:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Attendre que le backend soit prêt
echo "Attente du démarrage du backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend FastAPI démarré sur http://localhost:8000${NC}"
        echo -e "${GREEN}  Documentation API: http://localhost:8000/docs${NC}"
        break
    fi
    sleep 1
done

# Lancement du frontend
echo -e "${YELLOW}Lancement du frontend Streamlit...${NC}"
cd frontend
streamlit run app_new.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!
cd ..

echo ""
echo -e "${GREEN}=== EduPlan est lancé! ===${NC}"
echo ""
echo "📚 Frontend: http://localhost:8501"
echo "🔧 Backend API: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🗄️ Adminer (optionnel): http://localhost:8080"
echo ""
echo "Pour arrêter les services, appuyez sur Ctrl+C"

# Fonction pour arrêter proprement
cleanup() {
    echo ""
    echo -e "${YELLOW}Arrêt des services...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Services arrêtés${NC}"
    exit 0
}

# Capturer Ctrl+C
trap cleanup INT

# Garder le script actif
wait