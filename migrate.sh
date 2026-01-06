#!/bin/bash

# Script de migration vers EduPlan v2.0
# Usage: ./migrate.sh [--docker|--local]

set -e

echo "========================================="
echo "   Migration vers EduPlan v2.0          "
echo "========================================="
echo ""

# Fonction pour afficher les messages colorés
print_success() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_error() {
    echo -e "\033[0;31m❌ $1\033[0m"
}

print_warning() {
    echo -e "\033[0;33m⚠️  $1\033[0m"
}

print_info() {
    echo -e "\033[0;36mℹ️  $1\033[0m"
}

# Vérifier le mode d'installation
MODE=${1:-"--docker"}

# Créer les backups
backup() {
    print_info "Création des backups..."

    if [ -f .env ]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        print_success "Backup .env créé"
    fi

    if [ -d backend ]; then
        cp -r backend backend.backup.$(date +%Y%m%d_%H%M%S)
        print_success "Backup backend créé"
    fi

    if [ -d frontend ]; then
        cp -r frontend frontend.backup.$(date +%Y%m%d_%H%M%S)
        print_success "Backup frontend créé"
    fi
}

# Installation avec Docker
install_docker() {
    print_info "Installation avec Docker Compose..."

    # Vérifier que Docker est installé
    if ! command -v docker &> /dev/null; then
        print_error "Docker n'est pas installé"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose n'est pas installé"
        exit 1
    fi

    # Construire les images
    print_info "Construction des images Docker..."
    docker-compose build

    # Lancer les services
    print_info "Lancement des services..."
    docker-compose up -d postgres redis

    # Attendre que PostgreSQL soit prêt
    print_info "Attente de PostgreSQL..."
    sleep 10

    # Initialiser la base de données
    print_info "Initialisation de la base de données..."
    docker-compose exec postgres psql -U eduplan_user -d eduplan_db -f /docker-entrypoint-initdb.d/init.sql

    # Lancer backend et frontend
    docker-compose up -d backend frontend

    print_success "Installation Docker terminée!"
    print_info "Services disponibles:"
    print_info "  - Frontend: http://localhost:8501"
    print_info "  - Backend API: http://localhost:8000"
    print_info "  - Adminer (PostgreSQL): http://localhost:8080"
    print_info "  - Redis Commander: http://localhost:8081"
}

# Installation locale
install_local() {
    print_info "Installation locale..."

    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 n'est pas installé"
        exit 1
    fi

    # Créer l'environnement virtuel si nécessaire
    if [ ! -d venv ]; then
        print_info "Création de l'environnement virtuel..."
        python3 -m venv venv
    fi

    # Activer l'environnement
    source venv/bin/activate

    # Installer les dépendances
    print_info "Installation des dépendances backend..."
    pip install -r backend/requirements_new.txt

    print_info "Installation des dépendances frontend..."
    pip install -r frontend/requirements.txt

    # Vérifier PostgreSQL
    if command -v psql &> /dev/null; then
        print_info "Configuration de PostgreSQL..."

        # Créer la base si elle n'existe pas
        sudo -u postgres psql -c "CREATE DATABASE eduplan_db;" 2>/dev/null || true
        sudo -u postgres psql -c "CREATE USER eduplan_user WITH PASSWORD 'eduplan_password';" 2>/dev/null || true
        sudo -u postgres psql -c "GRANT ALL ON DATABASE eduplan_db TO eduplan_user;" 2>/dev/null || true

        # Initialiser les tables
        psql -U eduplan_user -d eduplan_db -f backend/data/init.sql

        print_success "PostgreSQL configuré"
    else
        print_warning "PostgreSQL non détecté - Installation manuelle requise"
    fi

    # Vérifier Redis
    if command -v redis-cli &> /dev/null; then
        print_info "Vérification de Redis..."
        if redis-cli ping > /dev/null 2>&1; then
            print_success "Redis est actif"
        else
            print_info "Démarrage de Redis..."
            sudo service redis-server start
        fi
    else
        print_warning "Redis non détecté - Installation manuelle requise"
        print_info "  sudo apt install redis-server"
    fi

    print_success "Installation locale terminée!"
}

# Créer les scripts de lancement
create_launchers() {
    print_info "Création des scripts de lancement..."

    # Script pour lancer le backend
    cat > start_backend.sh << 'EOF'
#!/bin/bash
cd backend
source ../venv/bin/activate 2>/dev/null || true
uvicorn src.api.main_new:app --reload --host 0.0.0.0 --port 8000
EOF
    chmod +x start_backend.sh

    # Script pour lancer le frontend
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
cd frontend
source ../venv/bin/activate 2>/dev/null || true
streamlit run app_new.py
EOF
    chmod +x start_frontend.sh

    # Script pour tout lancer
    cat > start_all.sh << 'EOF'
#!/bin/bash
echo "Lancement d'EduPlan v2.0..."

# Lancer le backend en arrière-plan
./start_backend.sh &
BACKEND_PID=$!

# Attendre un peu
sleep 3

# Lancer le frontend
./start_frontend.sh &
FRONTEND_PID=$!

echo "Services lancés:"
echo "  Backend PID: $BACKEND_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "Pour arrêter: kill $BACKEND_PID $FRONTEND_PID"

# Attendre
wait
EOF
    chmod +x start_all.sh

    print_success "Scripts de lancement créés"
}

# Test de santé
health_check() {
    print_info "Vérification des services..."

    # Test API
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API Backend accessible"
    else
        print_warning "API Backend non accessible"
    fi

    # Test Redis
    if redis-cli ping > /dev/null 2>&1; then
        print_success "Redis accessible"
    else
        print_warning "Redis non accessible"
    fi

    # Test PostgreSQL
    if PGPASSWORD=eduplan_password psql -U eduplan_user -h localhost -d eduplan_db -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "PostgreSQL accessible"
    else
        print_warning "PostgreSQL non accessible"
    fi
}

# Menu principal
main() {
    echo "Mode sélectionné: $MODE"
    echo ""

    # Créer les backups
    backup

    case $MODE in
        --docker)
            install_docker
            ;;
        --local)
            install_local
            create_launchers
            ;;
        *)
            print_error "Mode invalide. Utilisez --docker ou --local"
            exit 1
            ;;
    esac

    # Test de santé
    echo ""
    health_check

    echo ""
    print_success "Migration terminée avec succès!"
    echo ""
    print_info "Prochaines étapes:"
    print_info "1. Vérifiez votre fichier .env"
    print_info "2. Testez l'interface: http://localhost:8501"
    print_info "3. Consultez UPGRADE_GUIDE.md pour plus de détails"
    echo ""

    if [ "$MODE" == "--local" ]; then
        print_info "Pour lancer les services:"
        print_info "  ./start_all.sh"
        print_info "Ou séparément:"
        print_info "  ./start_backend.sh"
        print_info "  ./start_frontend.sh"
    else
        print_info "Pour voir les logs:"
        print_info "  docker-compose logs -f"
    fi
}

# Exécuter
main