#!/bin/bash

echo "=== Vérification des services EduPlan ==="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STATUS_OK=true

# Vérifier PostgreSQL
echo -n "PostgreSQL: "
if command -v psql &> /dev/null; then
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        echo -e "${GREEN}✓ Installé et en cours d'exécution${NC}"
        # Test de connexion à la base de données
        PGPASSWORD=eduplan_password psql -h localhost -U eduplan_user -d eduplan_db -c "SELECT 1" &> /dev/null
        if [ $? -eq 0 ]; then
            echo -e "  ${GREEN}✓ Base de données eduplan_db accessible${NC}"
        else
            echo -e "  ${YELLOW}⚠ Base de données non configurée${NC}"
            echo -e "  ${YELLOW}  Exécutez: ./install_services.sh${NC}"
            STATUS_OK=false
        fi
    else
        echo -e "${YELLOW}✓ Installé mais non démarré${NC}"
        echo -e "  ${YELLOW}  Exécutez: sudo service postgresql start${NC}"
        STATUS_OK=false
    fi
else
    echo -e "${RED}✗ Non installé${NC}"
    echo -e "  ${RED}  Exécutez: ./install_services.sh${NC}"
    STATUS_OK=false
fi

# Vérifier Redis
echo -n "Redis: "
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓ Installé et en cours d'exécution${NC}"
    else
        echo -e "${YELLOW}✓ Installé mais non démarré${NC}"
        echo -e "  ${YELLOW}  Exécutez: sudo service redis-server start${NC}"
        STATUS_OK=false
    fi
else
    echo -e "${RED}✗ Non installé${NC}"
    echo -e "  ${RED}  Exécutez: ./install_services.sh${NC}"
    STATUS_OK=false
fi

# Vérifier Python et venv
echo -n "Python venv: "
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Environnement virtuel présent${NC}"
    source venv/bin/activate 2>/dev/null

    # Vérifier les packages essentiels
    echo "  Packages essentiels:"

    # FastAPI
    echo -n "    - FastAPI: "
    if pip show fastapi &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        STATUS_OK=false
    fi

    # Streamlit
    echo -n "    - Streamlit: "
    if pip show streamlit &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        STATUS_OK=false
    fi

    # psycopg2
    echo -n "    - PostgreSQL driver: "
    if pip show psycopg2-binary &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        STATUS_OK=false
    fi

    # redis
    echo -n "    - Redis client: "
    if pip show redis &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        STATUS_OK=false
    fi
else
    echo -e "${RED}✗ Environnement virtuel non trouvé${NC}"
    STATUS_OK=false
fi

# Vérifier les clés API
echo "Clés API:"
if [ -f ".env" ]; then
    if grep -q "GROQ_API_KEY=gsk_" .env 2>/dev/null; then
        echo -e "  - GROQ_API_KEY: ${GREEN}✓ Configurée${NC}"
    else
        echo -e "  - GROQ_API_KEY: ${YELLOW}⚠ Non configurée (optionnel)${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ Fichier .env non trouvé${NC}"
fi

echo ""
echo "==================================="
if [ "$STATUS_OK" = true ]; then
    echo -e "${GREEN}✅ Tout est prêt!${NC}"
    echo ""
    echo "Vous pouvez maintenant lancer le projet avec:"
    echo "  ./launch.sh"
else
    echo -e "${YELLOW}⚠️ Configuration incomplète${NC}"
    echo ""
    echo "Actions recommandées:"
    echo "1. Exécutez: ./install_services.sh"
    echo "2. Puis relancez ce script de vérification"
fi