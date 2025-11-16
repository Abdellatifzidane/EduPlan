import streamlit as st
import requests
import pandas as pd
from datetime import time
import json

# Configuration de la page
st.set_page_config(
    page_title="EduPlan - Générateur de Planning",
    page_icon="📅",
    layout="wide"
)

# URL de l'API
API_URL = "http://edupplan-backend-service:8000" #http://localhost:8000


def main():
    st.title("📅 EduPlan - Générateur de Planning Intelligent")
    st.markdown("---")

    # Sidebar pour la navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Générer un Planning", "Parser une Contrainte", "Historique"]
    )

    if page == "Générer un Planning":
        generate_schedule_page()
    elif page == "Parser une Contrainte":
        parse_constraint_page()
    else:
        history_page()


def generate_schedule_page():
    st.header("🎯 Générer un Nouveau Planning")

    # Section 1: Configuration Système
    st.subheader("1. Configuration du Système")

    col1, col2, col3 = st.columns(3)

    with col1:
        num_rooms = st.number_input("Nombre de salles", min_value=1, value=8)
        num_teachers = st.number_input("Nombre de professeurs", min_value=1, value=7)
        num_classes = st.number_input("Nombre de classes", min_value=1, value=3)

    with col2:
        day_start = st.time_input("Début de journée", value=time(8, 0))
        day_end = st.time_input("Fin de journée", value=time(19, 0))
        session_duration = st.number_input("Durée séance (min)", min_value=30, value=90)

    with col3:
        break_duration = st.number_input("Pause entre cours (min)", min_value=5, value=15)
        lunch_start = st.time_input("Début pause déj", value=time(13, 0))
        lunch_end = st.time_input("Fin pause déj", value=time(14, 0))

    col4, col5 = st.columns(2)
    with col4:
        days_in_person = st.number_input("Jours en présentiel", min_value=1, max_value=7, value=4)
        days_remote = st.number_input("Jours en distanciel", min_value=0, max_value=7, value=1)

    with col5:
        max_hours_per_day = st.number_input("Max heures/jour/prof", min_value=1, value=9)
        prevent_parallel = st.checkbox(
            "Interdire même prof sur 2 classes simultanément",
            value=True
        )

    # Section 2: Charges de travail des profs
    st.subheader("2. Charges de Travail des Professeurs")

    num_profs_to_configure = st.number_input(
        "Nombre de profs à configurer",
        min_value=1,
        max_value=num_teachers,
        value=min(3, num_teachers)
    )

    teacher_workloads = []
    for i in range(num_profs_to_configure):
        with st.expander(f"Professeur {i+1}"):
            teacher_name = st.text_input(f"Nom", key=f"teacher_name_{i}", value=f"Prof_{i+1}")
            total_hours = st.number_input(
                f"Total heures/semaine",
                min_value=1.0,
                max_value=40.0,
                value=9.0,
                key=f"total_hours_{i}"
            )

            st.write("Répartition par classe:")
            class_assignments = {}

            num_classes_assigned = st.number_input(
                "Nombre de classes assignées",
                min_value=1,
                max_value=num_classes,
                value=min(2, num_classes),
                key=f"num_classes_{i}"
            )

            for j in range(num_classes_assigned):
                col_a, col_b = st.columns(2)
                with col_a:
                    class_name = st.text_input(
                        f"Classe {j+1}",
                        value=f"Classe {chr(65+j)}",
                        key=f"class_name_{i}_{j}"
                    )
                with col_b:
                    hours = st.number_input(
                        f"Heures",
                        min_value=0.5,
                        max_value=total_hours,
                        value=total_hours / num_classes_assigned,
                        step=0.5,
                        key=f"class_hours_{i}_{j}"
                    )
                class_assignments[class_name] = hours

            teacher_workloads.append({
                "teacher_name": teacher_name,
                "total_hours_per_week": total_hours,
                "class_assignments": class_assignments
            })

    # Section 3: Contraintes en langage naturel
    st.subheader("3. Contraintes de Disponibilité (Langage Naturel)")

    num_constraints = st.number_input(
        "Nombre de contraintes",
        min_value=0,
        max_value=20,
        value=1
    )

    constraints = []
    for i in range(num_constraints):
        with st.expander(f"Contrainte {i+1}"):
            teacher_name = st.text_input(
                "Nom du professeur",
                key=f"constraint_teacher_{i}",
                value=teacher_workloads[0]["teacher_name"] if teacher_workloads else "Prof_1"
            )
            constraint_text = st.text_area(
                "Contrainte en langage naturel",
                key=f"constraint_text_{i}",
                placeholder="Ex: Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00",
                height=100
            )

            if constraint_text.strip():
                constraints.append({
                    "teacher_name": teacher_name,
                    "constraint_text": constraint_text
                })

    # Bouton de génération
    st.markdown("---")
    if st.button("🚀 Générer le Planning", type="primary", use_container_width=True):
        with st.spinner("Génération du planning en cours..."):
            try:
                # Préparer la requête
                request_data = {
                    "configuration": {
                        "num_rooms": num_rooms,
                        "num_teachers": num_teachers,
                        "num_classes": num_classes,
                        "day_start": day_start.strftime("%H:%M:%S"),
                        "day_end": day_end.strftime("%H:%M:%S"),
                        "session_duration": session_duration,
                        "break_duration": break_duration,
                        "lunch_break_start": lunch_start.strftime("%H:%M:%S"),
                        "lunch_break_end": lunch_end.strftime("%H:%M:%S"),
                        "days_in_person": days_in_person,
                        "days_remote": days_remote,
                        "max_hours_per_day_per_teacher": max_hours_per_day,
                        "prevent_same_teacher_parallel": prevent_parallel
                    },
                    "teacher_workloads": teacher_workloads,
                    "constraints": constraints
                }

                # Appeler l'API
                response = requests.post(
                    f"{API_URL}/api/schedule/generate",
                    json=request_data,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()

                    st.success(f"✅ {result['message']}")

                    # Afficher le planning
                    if result.get("visual_html"):
                        st.components.v1.html(result["visual_html"], height=800, scrolling=True)

                    # Téléchargement
                    st.download_button(
                        label="📥 Télécharger le planning (JSON)",
                        data=json.dumps(result["schedule"], indent=2),
                        file_name=f"{result['schedule']['schedule_id']}.json",
                        mime="application/json"
                    )
                else:
                    st.error(f"❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Impossible de se connecter à l'API. Assurez-vous que le serveur est lancé.")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")


def parse_constraint_page():
    st.header("🧠 Parser une Contrainte en Langage Naturel")

    st.info("Testez l'agent NLP pour voir comment il interprète vos contraintes")

    teacher_name = st.text_input("Nom du professeur", value="Lyes")
    constraint_text = st.text_area(
        "Contrainte en langage naturel",
        placeholder="Ex: Je serai disponible lundi, mardi, vendredi matin de 08:00 - 13:00",
        height=150
    )

    if st.button("🔍 Analyser", type="primary"):
        if constraint_text.strip():
            with st.spinner("Analyse en cours..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/constraint/parse",
                        json={
                            "teacher_name": teacher_name,
                            "constraint_text": constraint_text
                        },
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("✅ Contrainte parsée avec succès!")

                        st.json(result["parsed_constraint"])
                    else:
                        st.error(f"❌ Erreur: {response.json().get('detail')}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Impossible de se connecter à l'API")
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
        else:
            st.warning("⚠️ Veuillez entrer une contrainte")


def history_page():
    st.header("📚 Historique des Plannings")
    st.info("Fonctionnalité en développement - Affichera l'historique depuis la base de données")


if __name__ == "__main__":
    main()
