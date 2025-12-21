import streamlit as st
import requests
import pandas as pd
from datetime import time, datetime
import json
import plotly.graph_objects as go
from typing import Dict, List, Any


def custom_json_encoder(obj):
    """Encodeur JSON personnalisé pour gérer les objets time et datetime"""
    if isinstance(obj, (time, datetime)):
        return obj.strftime("%H:%M:%S") if isinstance(obj, time) else obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Configuration de la page - DOIT être la première commande Streamlit
st.set_page_config(
    page_title="EduPlan - Générateur de Planning",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"  # Sidebar collapsé par défaut
)

# URL de l'API
API_URL = "http://localhost:8000"

# CSS personnalisé pour un design moderne et épuré
def inject_custom_css():
    st.markdown("""
    <style>
    /* Sidebar compact */
    .css-1d391kg {
        width: 280px !important;
    }

    /* Couleurs et styles globaux */
    .main {
        padding: 1rem;
        background-color: #f8f9fa;
    }

    /* Cartes et conteneurs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: white;
        padding: 0.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        background-color: #f8f9fa;
        border-radius: 8px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #4A90E2;
        color: white;
    }

    /* Boutons modernes */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: 500;
        transition: transform 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #4A90E2;
        box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.1);
    }

    /* Headers */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 2rem;
    }

    h2 {
        color: #2C3E50;
        font-weight: 600;
        margin-top: 1.5rem;
    }

    h3 {
        color: #34495e;
        font-weight: 500;
    }

    /* Success/Error messages */
    .stSuccess {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 8px;
    }

    .stError {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 8px;
    }

    /* Planning grid */
    .planning-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        margin-top: 1rem;
    }

    /* Cards */
    .config-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }

    /* Expander custom */
    .streamlit-expanderHeader {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 2px solid #e0e0e0;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* Chat interface */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }

    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 20%;
    }

    .assistant-message {
        background: white;
        border: 1px solid #e0e0e0;
        margin-right: 20%;
    }
    </style>
    """, unsafe_allow_html=True)


def create_empty_planning_view():
    """Créer une vue de planning vide"""
    fig = go.Figure()

    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    hours = ["08:00", "09:30", "11:00", "12:30", "14:00", "15:30", "17:00", "18:30"]

    # Créer la grille vide
    for i, day in enumerate(days):
        for j, hour in enumerate(hours[:-1]):
            fig.add_shape(
                type="rect",
                x0=i, x1=i+1,
                y0=j, y1=j+1,
                line=dict(color="#E0E0E0", width=1),
                fillcolor="white"
            )

    fig.update_layout(
        title="Planning de la Semaine",
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(len(days))),
            ticktext=days,
            side='top',
            showgrid=False
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(hours))),
            ticktext=hours,
            autorange='reversed',
            showgrid=False
        ),
        height=600,
        showlegend=False,
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        margin=dict(l=80, r=20, t=80, b=20),
        font=dict(family="sans-serif", size=12, color="#2C3E50")
    )

    return fig


def sidebar_configuration():
    """Configuration dans la sidebar compacte avec tabs"""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")

        # Tabs dans la sidebar
        tab1, tab2, tab3 = st.tabs(["📊 Système", "👨‍🏫 Professeurs", "📅 Disponibilités"])

        config_data = {}

        # Tab 1: Configuration Système
        with tab1:
            st.markdown("#### Paramètres généraux")

            with st.expander("📍 Ressources", expanded=True):
                config_data['num_rooms'] = st.number_input("Salles", min_value=1, max_value=20, value=8, key="rooms")
                config_data['num_teachers'] = st.number_input("Professeurs", min_value=1, max_value=30, value=7, key="teachers")
                config_data['num_classes'] = st.number_input("Classes", min_value=1, max_value=20, value=3, key="classes")

            with st.expander("⏰ Horaires", expanded=False):
                config_data['day_start'] = st.time_input("Début", value=time(8, 0), key="start")
                config_data['day_end'] = st.time_input("Fin", value=time(19, 0), key="end")
                config_data['session_duration'] = st.slider("Durée séance (min)", 45, 120, 90, 15)
                config_data['break_duration'] = st.slider("Pause (min)", 5, 30, 15, 5)

            with st.expander("🍽️ Pause déjeuner", expanded=False):
                config_data['lunch_start'] = st.time_input("Début", value=time(13, 0), key="lunch_s")
                config_data['lunch_end'] = st.time_input("Fin", value=time(14, 0), key="lunch_e")

            with st.expander("📋 Contraintes", expanded=False):
                config_data['days_in_person'] = st.number_input("Jours présentiel", 1, 5, 4)
                config_data['days_remote'] = st.number_input("Jours distanciel", 0, 2, 1)
                config_data['max_hours_per_day'] = st.slider("Max h/jour/prof", 4, 10, 9)
                config_data['max_consecutive'] = st.slider("Max séances consécutives", 1, 5, 3)
                config_data['prevent_parallel'] = st.checkbox("Pas de prof en parallèle", True)

        # Tab 2: Charges de travail
        teacher_workloads = []
        with tab2:
            st.markdown("#### Charges de travail")

            max_teachers = config_data.get('num_teachers', 7)
            num_profs = st.number_input("Nombre à configurer", 1, max_teachers, min(3, max_teachers), key="num_p")

            for i in range(num_profs):
                with st.expander(f"Prof {i+1}", expanded=(i==0)):
                    name = st.text_input("Nom", value=f"Prof_{i+1}", key=f"p_name_{i}")
                    hours = st.number_input("Heures/semaine", 1.0, 40.0, 9.0, 0.5, key=f"p_hours_{i}")

                    st.markdown("**Classes:**")
                    assignments = {}
                    max_classes = config_data.get('num_classes', 3)
                    num_classes = st.number_input("Nb classes", 1, max_classes, min(2, max_classes), key=f"p_nc_{i}")

                    for j in range(num_classes):
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            class_name = st.text_input("Classe", f"Classe {chr(65+j)}", key=f"p_c_{i}_{j}", label_visibility="collapsed")
                        with col2:
                            class_hours = st.number_input("H", 0.5, hours, hours/num_classes, 0.5, key=f"p_ch_{i}_{j}", label_visibility="collapsed")
                        assignments[class_name] = class_hours

                    teacher_workloads.append({
                        "teacher_name": name,
                        "total_hours_per_week": hours,
                        "class_assignments": assignments
                    })

        # Tab 3: Disponibilités
        availabilities = []
        with tab3:
            st.markdown("#### Disponibilités")

            # Interface simplifiée pour les disponibilités
            num_avail = st.number_input("Profs avec contraintes", 0, len(teacher_workloads), min(2, len(teacher_workloads)), key="num_av")

            days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
            time_slots = [
                ("08:00", "09:30"), ("09:45", "11:15"), ("11:30", "13:00"),
                ("14:00", "15:30"), ("15:45", "17:15"), ("17:30", "19:00")
            ]

            for i in range(num_avail):
                if i < len(teacher_workloads):
                    teacher_name = teacher_workloads[i]['teacher_name']
                else:
                    teacher_name = f"Prof_{i+1}"

                with st.expander(f"📅 {teacher_name}", expanded=(i==0)):
                    st.markdown("**Cochez les disponibilités:**")

                    teacher_availabilities = []

                    # Interface compacte avec multiselect par jour
                    for day in days:
                        selected_slots = st.multiselect(
                            f"{day.capitalize()}",
                            options=[f"{s[0]}-{s[1]}" for s in time_slots],
                            default=[f"{s[0]}-{s[1]}" for s in time_slots[:4]],  # Matin par défaut
                            key=f"av_{i}_{day}"
                        )

                        if selected_slots:
                            slots_list = []
                            for slot_str in selected_slots:
                                start, end = slot_str.split("-")
                                slots_list.append({"start": start, "end": end})

                            teacher_availabilities.append({
                                "teacher_name": teacher_name,
                                "day": day,
                                "time_slots": slots_list
                            })

                    if teacher_availabilities:
                        availabilities.append({
                            "teacher_name": teacher_name,
                            "availabilities": teacher_availabilities
                        })

        # Bouton de génération en bas de la sidebar
        st.markdown("---")
        if st.button("🚀 Générer Planning", type="primary", use_container_width=True):
            # Convertir les objets time en strings avant de retourner
            config_data_serializable = config_data.copy()
            for key in ['day_start', 'day_end', 'lunch_start', 'lunch_end']:
                if key in config_data_serializable and isinstance(config_data_serializable[key], time):
                    config_data_serializable[key] = config_data_serializable[key].strftime("%H:%M:%S")

            return {
                "action": "generate",
                "configuration": config_data_serializable,
                "teacher_workloads": teacher_workloads,
                "structured_availabilities": availabilities
            }

        if st.button("💾 Sauvegarder", type="secondary", use_container_width=True):
            return {"action": "save"}

    return None


def load_latest_schedule():
    """Charger le dernier planning depuis la base de données"""
    if 'current_schedule' not in st.session_state:
        try:
            response = requests.get(f"{API_URL}/api/schedules/latest", timeout=10)

            if response.status_code == 200:
                result = response.json()

                if result.get('success') and result.get('schedule'):
                    st.session_state['current_schedule'] = result['schedule']
                    st.session_state['visual_html'] = result.get('visual_html', '')
                    return True
        except Exception as e:
            print(f"Erreur chargement planning: {e}")
    return False

def main_planning_area():
    """Zone principale avec le planning"""

    # Charger automatiquement le dernier planning au démarrage
    load_latest_schedule()

    # Header avec actions rapides
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("# 📅 EduPlan - Planning Intelligent")
    with col2:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()
    with col3:
        if st.button("💬 Assistant IA", use_container_width=True):
            st.session_state['show_chat'] = not st.session_state.get('show_chat', False)

    # Container pour le planning
    with st.container():
        st.markdown('<div class="planning-container">', unsafe_allow_html=True)

        # Vérifier si un planning existe
        if 'current_schedule' in st.session_state and st.session_state['current_schedule']:
            schedule = st.session_state['current_schedule']

            # Infos du planning
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ID Planning", schedule['schedule_id'][:20] + "...")
            with col2:
                st.metric("Créneaux", len(schedule['slots']))
            with col3:
                st.metric("Professeurs", schedule['configuration']['num_teachers'])
            with col4:
                st.metric("Classes", schedule['configuration']['num_classes'])

            # Afficher le planning HTML
            if 'visual_html' in st.session_state:
                st.components.v1.html(st.session_state['visual_html'], height=700, scrolling=True)

            # Actions sur le planning
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Valider & Sauvegarder", type="primary", use_container_width=True):
                    save_validated_schedule()
            with col2:
                st.download_button(
                    "📥 Télécharger JSON",
                    data=json.dumps(schedule, indent=2, default=custom_json_encoder),
                    file_name=f"{schedule['schedule_id']}.json",
                    mime="application/json"
                )
            with col3:
                if st.button("🗑️ Effacer", type="secondary", use_container_width=True):
                    del st.session_state['current_schedule']
                    st.rerun()
        else:
            # Planning vide
            st.info("📌 Aucun planning généré. Utilisez le panneau de configuration à gauche pour créer votre premier planning.")

            # Afficher une grille vide
            fig = create_empty_planning_view()
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)


def chat_interface():
    """Interface de chat avec l'agent IA"""
    if st.session_state.get('show_chat', False):
        with st.container():
            st.markdown("---")
            st.markdown("### 💬 Assistant IA - Modification du Planning")

            # Vérifier qu'un planning existe
            if 'current_schedule' not in st.session_state:
                st.warning("⚠️ Générez d'abord un planning pour pouvoir le modifier")
                return

            # Zone de chat
            chat_container = st.container()

            # Historique des messages
            if 'chat_history' not in st.session_state:
                st.session_state['chat_history'] = []

            # Afficher l'historique
            with chat_container:
                for msg in st.session_state['chat_history']:
                    if msg['role'] == 'user':
                        st.markdown(f'<div class="chat-message user-message">{msg["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-message assistant-message">{msg["content"]}</div>', unsafe_allow_html=True)

            # Input pour nouveau message
            col1, col2 = st.columns([5, 1])
            with col1:
                user_input = st.text_input(
                    "Votre demande",
                    placeholder="Ex: Supprimer le cours de Prof_1 lundi 8h",
                    key="chat_input",
                    label_visibility="collapsed"
                )
            with col2:
                send_button = st.button("Envoyer", type="primary", use_container_width=True)

            if send_button and user_input:
                # Ajouter le message utilisateur
                st.session_state['chat_history'].append({
                    'role': 'user',
                    'content': user_input
                })

                # Appeler l'API pour modifier
                with st.spinner("L'agent analyse votre demande..."):
                    try:
                        # Convertir le schedule pour éviter les problèmes de sérialisation
                        schedule_json = json.dumps(st.session_state['current_schedule'], default=custom_json_encoder)
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
                                # Mettre à jour le planning
                                st.session_state['current_schedule'] = result['modified_schedule']
                                st.session_state['visual_html'] = result.get('visual_html', '')

                                # Message de confirmation
                                st.session_state['chat_history'].append({
                                    'role': 'assistant',
                                    'content': f"✅ {result['message']}"
                                })
                            else:
                                st.session_state['chat_history'].append({
                                    'role': 'assistant',
                                    'content': f"❓ {result['message']}"
                                })
                        else:
                            st.session_state['chat_history'].append({
                                'role': 'assistant',
                                'content': f"❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}"
                            })
                    except Exception as e:
                        st.session_state['chat_history'].append({
                            'role': 'assistant',
                            'content': f"❌ Erreur de connexion: {str(e)}"
                        })

                st.rerun()


def save_validated_schedule():
    """Sauvegarder un planning validé"""
    if 'current_schedule' in st.session_state:
        try:
            # Extraire l'ID du planning
            schedule_id = st.session_state['current_schedule'].get('schedule_id')

            if not schedule_id:
                st.error("❌ ID du planning manquant")
                return

            response = requests.post(
                f"{API_URL}/api/schedule/validate",
                json={
                    "schedule_id": schedule_id,
                    "validated_by": "user"
                },
                timeout=30
            )

            if response.status_code == 200:
                st.success("✅ Planning validé et sauvegardé avec succès!")
                # Marquer comme validé dans la session
                st.session_state['schedule_validated'] = True
            else:
                st.error(f"❌ Erreur lors de la sauvegarde: {response.json().get('detail', 'Erreur inconnue')}")
        except Exception as e:
            st.error(f"❌ Erreur de connexion: {str(e)}")


def handle_generation(action_data):
    """Gérer la génération d'un nouveau planning"""
    with st.spinner("🔄 Génération du planning en cours..."):
        try:
            # Préparer la requête
            config = action_data['configuration']

            # Convertir les times en strings si nécessaire
            def convert_time(value):
                if isinstance(value, time):
                    return value.strftime("%H:%M:%S")
                elif isinstance(value, str):
                    return value
                return value

            request_data = {
                "configuration": {
                    **config,
                    "day_start": convert_time(config.get('day_start')),
                    "day_end": convert_time(config.get('day_end')),
                    "lunch_break_start": convert_time(config.get('lunch_start')),
                    "lunch_break_end": convert_time(config.get('lunch_end')),
                    "max_hours_per_day_per_teacher": config.get('max_hours_per_day'),
                    "prevent_same_teacher_parallel": config.get('prevent_parallel'),
                    "max_consecutive_sessions": config.get('max_consecutive')
                },
                "teacher_workloads": action_data['teacher_workloads'],
                "structured_availabilities": action_data['structured_availabilities']
            }

            # Appeler l'API
            response = requests.post(
                f"{API_URL}/api/schedule/generate",
                json=request_data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                # Stocker dans la session
                st.session_state['current_schedule'] = result['schedule']
                st.session_state['visual_html'] = result.get('visual_html', '')
                st.session_state['schedule_validated'] = False

                st.success(f"✅ {result['message']}")
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")

        except requests.exceptions.ConnectionError:
            st.error("❌ Impossible de se connecter à l'API. Assurez-vous que le serveur backend est lancé sur le port 8000.")
        except Exception as e:
            st.error(f"❌ Erreur inattendue: {str(e)}")


def main():
    # Injecter le CSS personnalisé
    inject_custom_css()

    # Zone principale
    main_planning_area()

    # Interface de chat (conditionnelle)
    chat_interface()

    # Sidebar avec configuration
    action = sidebar_configuration()

    # Traiter l'action si nécessaire
    if action:
        if action['action'] == 'generate':
            handle_generation(action)
        elif action['action'] == 'save':
            save_validated_schedule()


if __name__ == "__main__":
    main()