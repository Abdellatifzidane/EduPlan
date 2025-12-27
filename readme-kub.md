Dans le projet EduPlan, on a déployé toute l’application sur Kubernetes, dans un namespace dédié qui s’appelle edupplan.
L’architecture repose sur plusieurs Deployments :
•	un Deployment frontend, basé sur Streamlit,
•	un Deployment backend, basé sur FastAPI,
•	un Deployment Redis pour le cache et les sessions,
•	et un StatefulSet PostgreSQL pour la base de données.
Avant le déploiement sur Kubernetes, on a d’abord conteneurisé l’application :
•	on a créé un Dockerfile pour le backend,
•	et un Dockerfile pour le frontend.
Ensuite, on a build les images Docker, on les a push sur le registry (GCR), puis on les a utilisées dans les Deployments Kubernetes.
Pour l’exposition des services :
•	le frontend est exposé via un Service de type LoadBalancer, ce qui permet d’accéder à l’application depuis l’extérieur avec une adresse IP publique,
•	le backend utilise un Service de type ClusterIP, car il n’a pas besoin d’être exposé publiquement : il est appelé uniquement par le frontend à l’intérieur du cluster.
On n’a pas utilisé Ingress volontairement :
•	parce que l’objectif était de rester simple,
•	il n’y a qu’une seule application à exposer,
•	et on n’a pas besoin de routing avancé, de nom de domaine ou de HTTPS à ce stade.
Le LoadBalancer est donc suffisant pour ce projet.
Pour la configuration, on a bien séparé les responsabilités :
•	les variables non sensibles sont dans des ConfigMaps (ports, URL interne du backend, configuration Streamlit),
•	les variables sensibles sont dans des Secrets (DATABASE_URL, REDIS_URL, GROQ_API_KEY).
Côté persistance :
•	PostgreSQL est déployé avec un volume persistant (PVC), ce qui garantit que les données restent même si le pod redémarre,
•	Redis est utilisé pour stocker le cache et les conversations de l’agent, et on a vérifié que des clés sont bien créées.
Enfin, on a validé que tout fonctionne :
•	le frontend communique bien avec le backend,
•	le backend est bien connecté à PostgreSQL et Redis,
•	les données sont bien stockées dans Postgres,
•	et l’agent fonctionne correctement avec l’API Groq.
À chaque changement de code, comme Kubernetes ne rebuild pas les images automatiquement, on doit :
•	rebuild l’image Docker,
•	la repush,
•	puis redéployer le Deployment concerné.
»
