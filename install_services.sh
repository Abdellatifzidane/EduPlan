#!/bin/bash

# Script d'installation de PostgreSQL et Redis pour EduPlan
echo "=== Installation de PostgreSQL et Redis pour EduPlan ==="

# Mise à jour des paquets
echo "1. Mise à jour des paquets..."
sudo apt update

# Installation de PostgreSQL
echo "2. Installation de PostgreSQL..."
sudo apt install -y postgresql postgresql-contrib

# Installation de Redis
echo "3. Installation de Redis..."
sudo apt install -y redis-server

# Démarrage des services
echo "4. Démarrage des services..."
sudo service postgresql start
sudo service redis-server start

# Configuration de PostgreSQL
echo "5. Configuration de PostgreSQL..."
sudo -u postgres psql << EOF
-- Créer l'utilisateur eduplan_user
CREATE USER eduplan_user WITH PASSWORD 'eduplan_password';

-- Créer la base de données
CREATE DATABASE eduplan_db OWNER eduplan_user;

-- Donner tous les privilèges à l'utilisateur
GRANT ALL PRIVILEGES ON DATABASE eduplan_db TO eduplan_user;

-- Afficher les bases de données créées
\l
EOF

# Vérification des services
echo "6. Vérification des services..."
echo "PostgreSQL status:"
sudo service postgresql status | head -3
echo ""
echo "Redis status:"
sudo service redis-server status | head -3

# Test de connexion
echo ""
echo "7. Test de connexion PostgreSQL..."
PGPASSWORD=eduplan_password psql -h localhost -U eduplan_user -d eduplan_db -c "SELECT version();"

echo ""
echo "8. Test de connexion Redis..."
redis-cli ping

echo ""
echo "=== Installation terminée ==="
echo "PostgreSQL: accessible sur localhost:5432"
echo "Redis: accessible sur localhost:6379"
echo "Base de données: eduplan_db"
echo "Utilisateur: eduplan_user"
echo "Mot de passe: eduplan_password"