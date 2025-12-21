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
API_URL = "http://localhost:8000"  # http://edupplan-backend-service:8000 pour Kubernetes


def custom_json_encoder(obj):
    """Encodeur JSON personnalisé pour gérer les objets time"""
    if isinstance(obj, time):
        return obj.strftime("%H:%M:%S")
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def load_latest_schedule():
    """Charger le dernier planning depuis la base de données"""
    if 'current_schedule' not in st.session_state:
        try:
            response = requests.get(f"{API_URL}/api/schedules/latest", timeout=10)

            if response.status_code == 200:
                result = response.json()

                if result.get('success') and result.get('schedule'):
                    st.session_state['current_schedule'] = result['schedule']
                    st.info(f"📊 Planning chargé: {result['schedule']['schedule_id']}")
                    return True
        except Exception:
            pass
    return False


def main():
    # Charger automatiquement le dernier planning au démarrage
    load_latest_schedule()

    st.title("📅 EduPlan - Générateur de Planning Intelligent")
    st.markdown("---")

    # Sidebar pour la navigation
    page = st.sidebar.radio(
        "Navigation",
        ["Générer un Planning", "Modifier le Planning", "Parser une Contrainte", "Historique"]
    )

    if page == "Générer un Planning":
        generate_schedule_page()
    elif page == "Modifier le Planning":
        modify_schedule_page()
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
        max_consecutive = st.number_input(
            "Max séances consécutives (prof, classe)",
            min_value=1,
            max_value=10,
            value=3,
            help="Maximum de séances consécutives qu'un prof peut donner à la même classe"
        )
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

    # Section 3: Contraintes de Disponibilité (Interface Visuelle)
    st.subheader("3. Disponibilités des Professeurs")

    # Générer les créneaux horaires basés sur la configuration
    def generate_time_slots_for_ui(day_start, day_end, session_duration, break_duration, lunch_start, lunch_end):
        from datetime import datetime, timedelta
        slots = []
        current = datetime.combine(datetime.today(), day_start)
        end = datetime.combine(datetime.today(), day_end)
        lunch_s = datetime.combine(datetime.today(), lunch_start)
        lunch_e = datetime.combine(datetime.today(), lunch_end)

        while current < end:
            slot_end = current + timedelta(minutes=session_duration)

            # Éviter la pause déjeuner
            if current < lunch_e and slot_end > lunch_s:
                current = lunch_e
                continue

            if slot_end <= end:
                slots.append((current.time().strftime("%H:%M"), slot_end.time().strftime("%H:%M")))

            current = slot_end + timedelta(minutes=break_duration)

        return slots

    time_slots_for_ui = generate_time_slots_for_ui(
        day_start, day_end, session_duration, break_duration, lunch_start, lunch_end
    )

    # Liste des jours
    days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]

    # Sélectionner les profs pour lesquels définir les disponibilités
    num_profs_availabilities = st.number_input(
        "Nombre de profs avec contraintes de disponibilité",
        min_value=0,
        max_value=num_teachers,
        value=min(3, num_teachers)
    )

    structured_availabilities = []

    for i in range(num_profs_availabilities):
        with st.expander(f"📅 Disponibilités - {teacher_workloads[i]['teacher_name'] if i < len(teacher_workloads) else f'Prof_{i+1}'}"):
            teacher_name = teacher_workloads[i]['teacher_name'] if i < len(teacher_workloads) else f"Prof_{i+1}"

            st.markdown(f"**Cochez les créneaux disponibles pour {teacher_name}**")

            # Créer une grille interactive
            teacher_availabilities = {}

            # Header avec les jours
            cols = st.columns([2] + [1] * len(days))
            cols[0].write("**Créneau**")
            for idx, day in enumerate(days):
                cols[idx + 1].write(f"**{day.capitalize()}**")

            # Créer une ligne par créneau horaire
            for slot_idx, (start, end) in enumerate(time_slots_for_ui):
                cols = st.columns([2] + [1] * len(days))
                cols[0].write(f"{start} - {end}")

                for day_idx, day in enumerate(days):
                    checkbox_key = f"avail_{i}_{day}_{slot_idx}"
                    is_checked = cols[day_idx + 1].checkbox(
                        f"Disponible {day} {start}-{end}",
                        key=checkbox_key,
                        label_visibility="collapsed"
                    )

                    if is_checked:
                        if day not in teacher_availabilities:
                            teacher_availabilities[day] = []
                        teacher_availabilities[day].append((start, end))

            # Convertir en format API
            availabilities_list = []
            for day, slots in teacher_availabilities.items():
                if slots:
                    # Fusionner les créneaux consécutifs
                    time_slots = [{"start": slot[0], "end": slot[1]} for slot in slots]
                    availabilities_list.append({
                        "teacher_name": teacher_name,
                        "day": day,
                        "time_slots": time_slots
                    })

            if availabilities_list:
                structured_availabilities.append({
                    "teacher_name": teacher_name,
                    "availabilities": availabilities_list
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
                        "prevent_same_teacher_parallel": prevent_parallel,
                        "max_consecutive_sessions": max_consecutive
                    },
                    "teacher_workloads": teacher_workloads,
                    "structured_availabilities": structured_availabilities
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

                    # Stocker le planning dans la session
                    st.session_state['current_schedule'] = result['schedule']

                    # Afficher le planning
                    if result.get("visual_html"):
                        st.components.v1.html(result["visual_html"], height=800, scrolling=True)

                    # Téléchargement
                    st.download_button(
                        label="📥 Télécharger le planning (JSON)",
                        data=json.dumps(result["schedule"], indent=2, default=custom_json_encoder),
                        file_name=f"{result['schedule']['schedule_id']}.json",
                        mime="application/json"
                    )

                    st.info("💡 Vous pouvez maintenant modifier ce planning via l'onglet 'Modifier le Planning'")
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


def modify_schedule_page():
    st.header("🤖 Modifier le Planning - Agent IA")

    st.markdown("""
    Utilisez l'agent IA pour modifier votre planning en **langage naturel** !

    **Exemples de commandes :**
    - "Supprimer le cours de Prof_1 le lundi à 8h"
    - "Déplacer le cours du mardi 10h au mercredi 14h"
    - "Ajouter un cours de Prof_2 pour Classe A le jeudi de 9h à 10h30"
    - "Changer la salle du cours de Prof_1 lundi 8h en Salle 5"
    - "Supprimer tous les cours du vendredi"
    """)

    # Vérifier qu'un planning existe
    if 'current_schedule' not in st.session_state or not st.session_state['current_schedule']:
        st.warning("⚠️ Aucun planning n'a encore été généré. Veuillez d'abord générer un planning.")
        return

    current_schedule = st.session_state['current_schedule']

    st.success(f"📅 Planning actif: **{current_schedule['schedule_id']}** ({len(current_schedule['slots'])} créneaux)")

    # Zone de chat
    st.markdown("---")
    st.subheader("💬 Chat avec l'Agent Modificateur")

    # Historique de conversation
    if 'conversation_history' not in st.session_state:
        st.session_state['conversation_history'] = []

    # Afficher l'historique
    for msg in st.session_state['conversation_history']:
        if msg['role'] == 'user':
            st.chat_message("user").write(msg['content'])
        else:
            st.chat_message("assistant").write(msg['content'])

    # Input utilisateur
    user_input = st.chat_input("Tapez votre demande de modification...")

    if user_input:
        # Ajouter le message utilisateur
        st.session_state['conversation_history'].append({
            'role': 'user',
            'content': user_input
        })

        st.chat_message("user").write(user_input)

        # Appeler l'API
        with st.spinner("L'agent analyse votre demande..."):
            try:
                # Convertir le schedule en JSON puis le recharger pour éviter les problèmes de sérialisation
                schedule_json = json.dumps(current_schedule, default=custom_json_encoder)
                schedule_data = json.loads(schedule_json)

                response = requests.post(
                    f"{API_URL}/api/schedule/modify",
                    json={
                        "current_schedule": schedule_data,
                        "user_message": user_input
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()

                    if result['success']:
                        # Mise à jour du planning
                        st.session_state['current_schedule'] = result['modified_schedule']

                        # Message de confirmation
                        confirmation_msg = f"{result['message']}\n\n**Action effectuée:** {result['action_taken']['action']}"
                        st.session_state['conversation_history'].append({
                            'role': 'assistant',
                            'content': confirmation_msg
                        })

                        st.chat_message("assistant").write(confirmation_msg)

                        # Afficher le nouveau planning
                        if result.get("visual_html"):
                            st.markdown("### 📊 Planning Mis à Jour")
                            st.components.v1.html(result["visual_html"], height=600, scrolling=True)

                        # Télécharger
                        st.download_button(
                            label="📥 Télécharger le planning modifié",
                            data=json.dumps(result["modified_schedule"], indent=2, default=custom_json_encoder),
                            file_name=f"{result['modified_schedule']['schedule_id']}.json",
                            mime="application/json"
                        )

                    else:
                        # Clarification nécessaire
                        clarification_msg = result['message']
                        st.session_state['conversation_history'].append({
                            'role': 'assistant',
                            'content': clarification_msg
                        })
                        st.chat_message("assistant").write(clarification_msg)

                else:
                    error_detail = response.json().get('detail', 'Erreur inconnue')
                    st.error(f"❌ Erreur: {error_detail}")

            except requests.exceptions.ConnectionError:
                st.error("❌ Impossible de se connecter à l'API")
            except Exception as e:
                st.error(f"❌ Erreur: {str(e)}")


def history_page():
    st.header("📚 Historique des Plannings Sauvegardés")

    # Récupérer la liste des plannings
    try:
        response = requests.get(f"{API_URL}/api/schedules", timeout=10)

        if response.status_code == 200:
            data = response.json()
            schedules = data.get("schedules", [])

            if not schedules:
                st.info("Aucun planning enregistré pour le moment. Générez-en un pour le voir apparaître ici !")
                return

            st.success(f"📊 {data['count']} planning(s) trouvé(s)")

            # Afficher sous forme de tableau
            for schedule in schedules:
                with st.expander(f"📅 {schedule['schedule_id']} - Créé le {schedule['created_at'][:19]}"):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write(f"**Créneaux:** {schedule['num_slots']}")
                        st.write(f"**Salles:** {schedule['configuration']['num_rooms']}")

                    with col2:
                        st.write(f"**Professeurs:** {schedule['configuration']['num_teachers']}")
                        st.write(f"**Classes:** {schedule['configuration']['num_classes']}")

                    with col3:
                        if st.button("👁️ Voir", key=f"view_{schedule['schedule_id']}"):
                            # Charger le planning complet
                            detail_response = requests.get(
                                f"{API_URL}/api/schedules/{schedule['schedule_id']}",
                                timeout=10
                            )

                            if detail_response.status_code == 200:
                                detail_data = detail_response.json()

                                # Stocker dans la session
                                st.session_state['current_schedule'] = detail_data['schedule']

                                # Afficher
                                st.success(f"✅ Planning {schedule['schedule_id']} chargé!")

                                if detail_data.get("visual_html"):
                                    st.components.v1.html(detail_data["visual_html"], height=800, scrolling=True)

                                # Télécharger
                                st.download_button(
                                    label="📥 Télécharger (JSON)",
                                    data=json.dumps(detail_data["schedule"], indent=2, default=custom_json_encoder),
                                    file_name=f"{schedule['schedule_id']}.json",
                                    mime="application/json",
                                    key=f"dl_{schedule['schedule_id']}"
                                )

                        if st.button("🗑️ Supprimer", key=f"del_{schedule['schedule_id']}"):
                            # Confirmer la suppression
                            if st.button("⚠️ Confirmer suppression", key=f"conf_{schedule['schedule_id']}"):
                                delete_response = requests.delete(
                                    f"{API_URL}/api/schedules/{schedule['schedule_id']}",
                                    timeout=10
                                )

                                if delete_response.status_code == 200:
                                    st.success("✅ Planning supprimé!")
                                    st.rerun()
                                else:
                                    st.error("❌ Erreur lors de la suppression")

        else:
            st.error(f"❌ Erreur: {response.status_code}")

    except requests.exceptions.ConnectionError:
        st.error("❌ Impossible de se connecter à l'API")
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")


if __name__ == "__main__":
    main()
