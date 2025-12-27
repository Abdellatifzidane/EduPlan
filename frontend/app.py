import streamlit as st
import requests
import pandas as pd
from datetime import time, datetime
import json
import plotly.graph_objects as go
from typing import Dict, List, Any
import os

def custom_json_encoder(obj):
    """Encodeur JSON personnalisé pour gérer les objets time et datetime"""
    if isinstance(obj, (time, datetime)):
        return obj.strftime("%H:%M:%S") if isinstance(obj, time) else obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

# Configuration de la page
st.set_page_config(
    page_title="EduPlan - Générateur de Planning Intelligent",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL de l'API
API_URL = os.getenv("API_URL", "http://backend:8000")

# CSS personnalisé pour une interface moderne en 3 colonnes
def inject_custom_css():
    st.markdown("""
    <style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Global styling */
    .main {
        padding: 0 !important;
        background: #ffffff;
    }

    .block-container {
        padding: 1rem !important;
        max-width: 100% !important;
        background: #f8f9fa;
    }

    /* Colonnes principales */
    .column-container {
        display: flex;
        height: 95vh;
        gap: 1rem;
    }

    .left-column {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        overflow-y: auto;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .middle-column {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        overflow-y: auto;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    .right-column {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        display: flex;
        flex-direction: column;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }

    /* Headers */
    h1, h2, h3 {
        color: #2C3E50;
        font-weight: 600;
    }

    h1 {
        font-size: 1.8rem;
        margin-bottom: 1rem;
        color: #2C3E50;
    }

    h2 {
        font-size: 1.3rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    h3 {
        font-size: 1.1rem;
        margin-top: 1rem;
        color: #34495e;
    }

    /* Boutons */
    .stButton > button {
        background: #667eea;
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s;
        width: 100%;
    }

    .stButton > button:hover {
        background: #5568d3;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stTimeInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 0.5rem;
        transition: all 0.2s;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        font-weight: 500;
        padding: 0.8rem;
    }

    /* Chat messages */
    .chat-container {
        flex: 1;
        overflow-y: auto;
        margin-bottom: 1rem;
        padding-right: 0.5rem;
    }

    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        animation: fadeIn 0.3s;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-message {
        background: #667eea;
        color: white;
        margin-left: 15%;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
    }

    .assistant-message {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        margin-right: 15%;
        color: #2C3E50;
    }

    /* Chat input */
    .chat-input-container {
        border-top: 2px solid #e0e0e0;
        padding-top: 1rem;
    }

    /* Metrics */
    .metric-card {
        background: #667eea;
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    .metric-value {
        font-size: 2rem;
        font-weight: 700;
    }

    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin-top: 0.3rem;
    }

    /* Scrollbar custom */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #5568d3;
    }

    /* Planning container */
    .planning-view {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin-top: 1rem;
    }

    /* Success/Error alerts */
    .stSuccess, .stError, .stInfo, .stWarning {
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
                    /* 1) Expander: titre + contenu */
    details summary,
    details summary * {
        color: #111 !important;
    }

    details div[data-testid="stMarkdownContainer"],
    details div[data-testid="stMarkdownContainer"] * {
        color: #111 !important;
    }

    /* 2) Labels des widgets (NumberInput/TimeInput/etc.) */
    div[data-testid="stWidgetLabel"] *,
    label, label * {
        color: #111 !important;
    }

    /* 3) Alerts (error/warning/info/success) */
    div[data-testid="stAlert"] *,
    div[role="alert"] * {
        color: #111 !important;
    }

    /* 4) Inputs (texte et placeholder) */
    input, textarea {
        color: #111 !important;
    }
    input::placeholder, textarea::placeholder {
        color: #666 !important;
        opacity: 1 !important;
    }

    /* Hide unnecessary elements */
    .stDeployButton {display: none;}
    .stDecoration {display: none;}
    </style>
    """, unsafe_allow_html=True)


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
            pass
    return False


def configuration_panel():
    """Panneau de configuration à gauche"""
    st.markdown("## ⚙️ Configuration")

    with st.expander("📊 **Ressources**", expanded=True):
        num_rooms = st.number_input("Nombre de salles", min_value=1, max_value=20, value=8, key="rooms")
        num_teachers = st.number_input("Nombre de professeurs", min_value=1, max_value=30, value=7, key="teachers")
        num_classes = st.number_input("Nombre de classes", min_value=1, max_value=20, value=3, key="classes")

    with st.expander("⏰ **Horaires**", expanded=False):
        day_start = st.time_input("Début de journée", value=time(8, 0), key="start")
        day_end = st.time_input("Fin de journée", value=time(19, 0), key="end")
        session_duration = st.slider("Durée d'une séance (min)", 45, 120, 90, 15)
        break_duration = st.slider("Durée des pauses (min)", 5, 30, 15, 5)

    with st.expander("🍽️ **Pause déjeuner**", expanded=False):
        lunch_start = st.time_input("Début pause déj", value=time(13, 0), key="lunch_s")
        lunch_end = st.time_input("Fin pause déj", value=time(14, 0), key="lunch_e")

    with st.expander("📋 **Contraintes**", expanded=False):
        days_in_person = st.number_input("Jours en présentiel", 1, 5, 4)
        days_remote = st.number_input("Jours en distanciel", 0, 2, 1)
        max_hours_per_day = st.slider("Max heures/jour/prof", 4, 10, 9)
        max_consecutive = st.slider("Max séances consécutives", 1, 5, 3)
        prevent_parallel = st.checkbox("Éviter profs en parallèle", True)

    # Configuration des professeurs
    st.markdown("### 👨‍🏫 Professeurs")
    num_profs = st.number_input("Nombre à configurer", 1, num_teachers, min(3, num_teachers), key="num_p")

    teacher_workloads = []
    for i in range(num_profs):
        with st.expander(f"Prof {i+1}", expanded=(i==0)):
            name = st.text_input("Nom", value=f"Prof_{i+1}", key=f"p_name_{i}")
            hours = st.number_input("Heures/semaine", 1.0, 40.0, 9.0, 0.5, key=f"p_hours_{i}")

            st.markdown("**Classes assignées:**")
            assignments = {}
            num_cls = st.number_input("Nb classes", 1, num_classes, min(2, num_classes), key=f"p_nc_{i}")

            for j in range(num_cls):
                col1, col2 = st.columns([2, 1])
                with col1:
                    class_name = st.text_input("", f"Classe {chr(65+j)}", key=f"p_c_{i}_{j}", label_visibility="collapsed")
                with col2:
                    class_hours = st.number_input("H", 0.5, hours, hours/num_cls, 0.5, key=f"p_ch_{i}_{j}", label_visibility="collapsed")
                assignments[class_name] = class_hours

            teacher_workloads.append({
                "teacher_name": name,
                "total_hours_per_week": hours,
                "class_assignments": assignments
            })

    # Disponibilités
    st.markdown("### 📅 Disponibilités")
    num_avail = st.number_input("Profs avec contraintes", 0, len(teacher_workloads), min(2, len(teacher_workloads)), key="num_av")

    days = ["lundi", "mardi", "mercredi", "jeudi", "vendredi"]
    time_slots = [
        ("08:00", "09:30"), ("09:45", "11:15"), ("11:30", "13:00"),
        ("14:00", "15:30"), ("15:45", "17:15"), ("17:30", "19:00")
    ]

    availabilities = []
    for i in range(num_avail):
        if i < len(teacher_workloads):
            teacher_name = teacher_workloads[i]['teacher_name']
        else:
            teacher_name = f"Prof_{i+1}"

        with st.expander(f"📅 {teacher_name}", expanded=(i==0)):
            teacher_availabilities = []

            for day in days:
                selected_slots = st.multiselect(
                    f"{day.capitalize()}",
                    options=[f"{s[0]}-{s[1]}" for s in time_slots],
                    default=[f"{s[0]}-{s[1]}" for s in time_slots[:4]],
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

    # Bouton de génération
    st.markdown("---")
    if st.button("🚀 Générer Planning", type="primary", use_container_width=True, key="gen_btn"):
        config_data = {
            'num_rooms': num_rooms,
            'num_teachers': num_teachers,
            'num_classes': num_classes,
            'day_start': day_start.strftime("%H:%M:%S"),
            'day_end': day_end.strftime("%H:%M:%S"),
            'lunch_start': lunch_start.strftime("%H:%M:%S"),
            'lunch_end': lunch_end.strftime("%H:%M:%S"),
            'session_duration': session_duration,
            'break_duration': break_duration,
            'days_in_person': days_in_person,
            'days_remote': days_remote,
            'max_hours_per_day': max_hours_per_day,
            'max_consecutive': max_consecutive,
            'prevent_parallel': prevent_parallel
        }

        return {
            "action": "generate",
            "configuration": config_data,
            "teacher_workloads": teacher_workloads,
            "structured_availabilities": availabilities
        }

    return None


def planning_view():
    """Vue principale du planning au centre"""
    st.markdown("# 📅 Planning de la Semaine")

    # Charger automatiquement le dernier planning
    load_latest_schedule()

    # Actions rapides
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("✅ Valider", use_container_width=True):
            save_validated_schedule()
    with col3:
        if st.button("🗑️ Effacer", use_container_width=True):
            delete_current_schedule()

    # Vérifier si un planning existe
    if 'current_schedule' in st.session_state and st.session_state['current_schedule']:
        schedule = st.session_state['current_schedule']

        # Métriques épurées (sans schedule_id)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Créneaux</div></div>'.format(len(schedule['slots'])), unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Professeurs</div></div>'.format(schedule['configuration']['num_teachers']), unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card"><div class="metric-value">{}</div><div class="metric-label">Classes</div></div>'.format(schedule['configuration']['num_classes']), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Afficher le planning HTML
        if 'visual_html' in st.session_state:
            st.components.v1.html(st.session_state['visual_html'], height=650, scrolling=True)

        # Bouton de téléchargement discret
        st.download_button(
            "📥 Télécharger le planning (JSON)",
            data=json.dumps(schedule, indent=2, default=custom_json_encoder),
            file_name=f"planning_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True
        )
    else:
        # Planning vide
        st.info("📌 **Aucun planning généré**\n\nUtilisez le panneau de configuration à gauche pour créer votre premier planning.")

        # Grille vide
        fig = create_empty_planning_view()
        st.plotly_chart(fig, use_container_width=True)


def create_empty_planning_view():
    """Créer une vue de planning vide"""
    fig = go.Figure()

    days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
    hours = ["08:00", "09:30", "11:00", "12:30", "14:00", "15:30", "17:00"]

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
        height=500,
        showlegend=False,
        plot_bgcolor='#F8F9FA',
        paper_bgcolor='white',
        margin=dict(l=60, r=20, t=60, b=20)
    )

    return fig


def chat_panel():
    """Panneau de chat avec l'agent à droite - TOUJOURS VISIBLE"""
    st.markdown("## 💬 Assistant IA")
    st.markdown("*Modifiez votre planning en langage naturel*")

    # Initialiser l'historique
    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    # Container pour le chat
    chat_container = st.container()

    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Message de bienvenue si vide
        if len(st.session_state['chat_history']) == 0:
            st.markdown('''
            <div class="chat-message assistant-message">
                👋 Bonjour ! Je suis votre assistant IA pour modifier le planning.
                <br><br>
                <b>Exemples de commandes :</b><br>
                • "Supprimer le cours de Prof_1 lundi à 8h"<br>
                • "Ajouter un cours pour Prof_2 mardi de 10h à 11h30"<br>
                • "Déplacer le cours du mercredi 9h au jeudi 14h"
            </div>
            ''', unsafe_allow_html=True)

        # Afficher l'historique des messages
        for msg in st.session_state['chat_history']:
            if msg['role'] == 'user':
                st.markdown(
                    f'<div class="chat-message user-message">👤 {msg["content"]}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="chat-message assistant-message">🤖 {msg["content"]}</div>',
                    unsafe_allow_html=True
                )

        st.markdown('</div>', unsafe_allow_html=True)

    # Zone d'input en bas
    st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)

    # Vérifier qu'un planning existe
    if 'current_schedule' not in st.session_state or not st.session_state['current_schedule']:
        st.warning("⚠️ Générez d'abord un planning pour pouvoir le modifier")
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Input pour nouveau message
    user_input = st.text_input(
        "Votre demande",
        placeholder="Ex: Supprimer le cours de Prof_1 lundi 8h",
        key="chat_input",
        label_visibility="collapsed"
    )

    if st.button("📤 Envoyer", type="primary", use_container_width=True, key="send_btn"):
        if user_input and user_input.strip():
            # Ajouter le message utilisateur
            st.session_state['chat_history'].append({
                'role': 'user',
                'content': user_input
            })

            # Appeler l'API
            with st.spinner("L'agent analyse votre demande..."):
                try:
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

    st.markdown('</div>', unsafe_allow_html=True)


def save_validated_schedule():
    """Sauvegarder un planning validé"""
    if 'current_schedule' in st.session_state:
        try:
            schedule_id = st.session_state['current_schedule'].get('schedule_id')

            if not schedule_id:
                st.error("❌ ID du planning manquant")
                return

            response = requests.post(
                f"{API_URL}/api/schedule/validate",
                json={"schedule_id": schedule_id, "validated_by": "user"},
                timeout=30
            )

            if response.status_code == 200:
                st.success("✅ Planning validé et sauvegardé !")
                st.session_state['schedule_validated'] = True
            else:
                st.error(f"❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")


def delete_current_schedule():
    """Supprimer le planning actuel"""
    if 'current_schedule' in st.session_state:
        try:
            schedule_id = st.session_state['current_schedule'].get('schedule_id')
            if schedule_id:
                response = requests.delete(f"{API_URL}/api/schedules/{schedule_id}", timeout=10)
                if response.status_code == 200:
                    st.success("✅ Planning supprimé")
                else:
                    st.warning("⚠️ Impossible de supprimer")
        except Exception as e:
            st.warning(f"⚠️ Erreur: {str(e)}")

        # Nettoyer la session
        if 'current_schedule' in st.session_state:
            del st.session_state['current_schedule']
        if 'visual_html' in st.session_state:
            del st.session_state['visual_html']
        st.rerun()


def handle_generation(action_data):
    """Gérer la génération d'un nouveau planning"""
    with st.spinner("🔄 Génération du planning en cours..."):
        try:
            config = action_data['configuration']

            request_data = {
                "configuration": {
                    **config,
                    "lunch_break_start": config.get('lunch_start'),
                    "lunch_break_end": config.get('lunch_end'),
                    "max_hours_per_day_per_teacher": config.get('max_hours_per_day'),
                    "prevent_same_teacher_parallel": config.get('prevent_parallel'),
                    "max_consecutive_sessions": config.get('max_consecutive')
                },
                "teacher_workloads": action_data['teacher_workloads'],
                "structured_availabilities": action_data['structured_availabilities']
            }

            response = requests.post(
                f"{API_URL}/api/schedule/generate",
                json=request_data,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                st.session_state['current_schedule'] = result['schedule']
                st.session_state['visual_html'] = result.get('visual_html', '')
                st.session_state['schedule_validated'] = False

                st.success(f"✅ {result['message']}")
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ Erreur: {response.json().get('detail', 'Erreur inconnue')}")

        except requests.exceptions.ConnectionError:
            st.error("❌ Impossible de se connecter à l'API. Assurez-vous que le backend est lancé sur le port 8000.")
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")


def main():
    # Injecter le CSS personnalisé
    inject_custom_css()

    # Layout en 3 colonnes
    col1, col2, col3 = st.columns([1.2, 2.5, 1.3], gap="medium")

    # Colonne gauche : Configuration
    with col1:
        action = configuration_panel()

    # Colonne milieu : Planning
    with col2:
        planning_view()

    # Colonne droite : Chat Agent
    with col3:
        chat_panel()

    # Traiter l'action de génération
    if action and action['action'] == 'generate':
        handle_generation(action)


if __name__ == "__main__":
    main()
