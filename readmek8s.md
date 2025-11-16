
#  EduPlan – Déploiement Kubernetes sur Google Kubernetes Engine (GKE)

Ce document explique toutes les étapes réalisées pour conteneuriser, déployer et exposer l’application **EduPlan** (backend FastAPI + frontend Streamlit) sur **Kubernetes** et **Google Cloud Platform (GKE)**.

---

#  1. Conteneurisation des Applications

##  Backend (FastAPI)

* Dockerfile basé sur `python:3.11-slim`
* Installation des dépendances via `requirements.txt`
* Copie du code dans `/app/src`
* Lancement avec Uvicorn :

uvicorn api.main:app --host 0.0.0.0 --port 8000

### Build & test local

docker build -t edupplan-backend .
docker run -p 8000:8000 edupplan-backend

---

##  Frontend (Streamlit)

* Dockerfile dédié
* Installation des dépendances
* Exposition du port `8501`
* Lancement avec :

streamlit run app.py --server.port=8501 --server.address=0.0.0.0

### Build & test local

docker build -t edupplan-frontend .
docker run -p 8501:8501 edupplan-frontend

---

#  2. Publication des images sur Google Container Registry (GCR)

Connexion Docker ↔ GCP :
gcloud auth configure-docker

Tag :
docker tag edupplan-backend gcr.io/<PROJECT-ID>/edupplan-backend:v1
docker tag edupplan-frontend gcr.io/<PROJECT-ID>/edupplan-frontend:v1

Push :
docker push gcr.io/<PROJECT-ID>/edupplan-backend:v1
docker push gcr.io/<PROJECT-ID>/edupplan-frontend:v1

---

#  3. Déploiement Kubernetes (GKE)

Création d’un namespace :
kubectl create namespace edupplan

---

#  4. Déploiements Kubernetes

## Backend Deployment + Service

* 1 pod FastAPI
* Service ClusterIP (interne)

kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml

---

## Frontend Deployment + Service

* 1 pod Streamlit
* Service LoadBalancer (public)

kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml

---

#  5. Exposition du Frontend au Public

Le service frontend apparaît comme :

TYPE = LoadBalancer
EXTERNAL-IP = <PUBLIC-IP>
PORT(S) = 80 → 8501

Accès public :
http://<PUBLIC-IP>:8501/

---

# 6. Communication interne Backend ⇄ Frontend

Le backend reste interne :

[http://edupplan-backend-service:8000](http://edupplan-backend-service:8000)

Le frontend communique via ce DNS interne.

---

#  7. Vérification du Backend (ClusterIP)

## Méthode 1 — Port-forward

kubectl port-forward -n edupplan svc/edupplan-backend-service 8000:8000

Swagger :
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## Méthode 2 — Tester depuis un pod interne

kubectl run -it tmp --rm --image=busybox --namespace=edupplan -- sh
wget -qO- edupplan-backend-service:8000/health

---

## Méthode 3 — Logs

kubectl logs -n edupplan -l app=edupplan-backend

---

#  8. Résultat final (Étape 1 terminée)

✔ Backend conteneurisé
✔ Frontend conteneurisé
✔ Images poussées sur GCR
✔ Namespace créé
✔ Déploiements OK
✔ Services OK
✔ Frontend accessible publiquement
✔ Communication interne front → back
✔ Backend accessible via port-forward

Architecture finale :

[Public User] → LoadBalancer → Frontend (Streamlit)
Frontend → ClusterIP → Backend (FastAPI)

---

# Prochaines étapes possibles

* Autoscaling (HPA)
* ConfigMaps
* Secrets (.env)
* Requests/Limits CPU-RAM
* PersistentVolume pour DB
* HTTPS (cert-manager)
* CI/CD GitHub Actions

---

# Architecture

                       🌍 Utilisateur (navigateur)
                                │
                                │ HTTP (port 8501)
                                ▼
                 +----------------------------------+
                 |  Service LoadBalancer            |
                 |  edupplan-frontend-service       |
                 |  EXTERNAL-IP : 34.38.19.120      |
                 |  Port 80 -> 8501                 |
                 +-----------------┬----------------+
                                   │
                          Trafic interne (ClusterIP)
                                   │
                                   ▼
                 +----------------------------------+
                 |  Pod frontend (Streamlit)        |
                 |  Deployment:                     |
                 |  edupplan-frontend-deployment    |
                 +----------------------------------+
                                   │
                            Requêtes HTTP
                   http://edupplan-backend-service:8000
                                   │
                                   ▼
                 +----------------------------------+
                 |  Service ClusterIP               |
                 |  edupplan-backend-service        |
                 |  Port 8000 -> 8000               |
                 +-----------------┬----------------+
                                   │
                           Trafic interne Pod
                                   │
                                   ▼
                 +----------------------------------+
                 |  Pod backend (FastAPI / Uvicorn) |
                 |  Deployment:                     |
                 |  edupplan-backend-deployment     |
                 +----------------------------------+

Namespace Kubernetes : edupplan
Cluster : GKE (Google Kubernetes Engine)
Registry des images : GCR (gcr.io/<PROJECT-ID>/...)


# Auteur

Déployé par **Melissa Issolah**
Projet EduPlan – ESGI – 2025


