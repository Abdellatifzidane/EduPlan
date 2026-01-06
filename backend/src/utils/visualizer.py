import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List
from datetime import datetime, time
from ..models.schemas import Schedule, ScheduleSlot, DayOfWeek


class ScheduleVisualizer:
    """Classe pour visualiser les plannings en différents formats"""

    def __init__(self):
        self.day_order = {
            DayOfWeek.MONDAY: 0,
            DayOfWeek.TUESDAY: 1,
            DayOfWeek.WEDNESDAY: 2,
            DayOfWeek.THURSDAY: 3,
            DayOfWeek.FRIDAY: 4,
            DayOfWeek.SATURDAY: 5,
            DayOfWeek.SUNDAY: 6,
        }

        self.colors = {
            "primary": "#4A90E2",
            "success": "#7ED321",
            "warning": "#F5A623",
            "danger": "#D0021B",
            "info": "#50E3C2",
            "purple": "#9013FE",
            "pink": "#E91E63"
        }

    def to_dataframe(self, schedule: Schedule) -> pd.DataFrame:
        """Convertit le planning en DataFrame pandas"""
        data = []
        for slot in schedule.slots:
            data.append({
                "Jour": slot.day.value.capitalize(),
                "Heure début": slot.start_time.strftime("%H:%M"),
                "Heure fin": slot.end_time.strftime("%H:%M"),
                "Professeur": slot.teacher,
                "Classe": slot.class_name,
                "Salle": slot.room,
                "Matière": slot.subject or "N/A"
            })

        df = pd.DataFrame(data)

        # Trier par jour puis par heure
        day_order_map = {day.value.capitalize(): idx for day, idx in self.day_order.items()}
        df["_day_order"] = df["Jour"].map(day_order_map)
        df = df.sort_values(["_day_order", "Heure début"]).drop(columns=["_day_order"])

        return df

    def render_html(self, schedule: Schedule) -> str:
        """Génère une visualisation HTML du planning en format grille calendrier avec onglets par classe"""

        # Organiser les slots par jour et horaire
        days_fr = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        days_enum = [DayOfWeek.MONDAY, DayOfWeek.TUESDAY, DayOfWeek.WEDNESDAY, DayOfWeek.THURSDAY, DayOfWeek.FRIDAY]

        # Extraire toutes les classes
        all_classes = sorted(list(set(slot.class_name for slot in schedule.slots)))

        # Extraire tous les créneaux horaires uniques
        time_slots = set()
        for slot in schedule.slots:
            time_slots.add((slot.start_time, slot.end_time))
        time_slots = sorted(list(time_slots))

        # Créer une grille par classe: dict[class_name][day][time_slot] = list of courses
        grids = {}
        for class_name in all_classes:
            grids[class_name] = {}
            for day_enum in days_enum:
                grids[class_name][day_enum] = {}
                for time_slot in time_slots:
                    grids[class_name][day_enum][time_slot] = []

        # Remplir les grilles avec les cours
        for slot in schedule.slots:
            time_key = (slot.start_time, slot.end_time)
            grids[slot.class_name][slot.day][time_key].append(slot)

        # Générer le HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Planning - {schedule.schedule_id}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .header {{
                    text-align: center;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .stats {{
                    display: flex;
                    justify-content: space-around;
                    margin: 20px 0;
                    flex-wrap: wrap;
                }}
                .stat-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                    min-width: 150px;
                    margin: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .stat-value {{
                    font-size: 2em;
                    font-weight: bold;
                    color: #667eea;
                }}
                .stat-label {{
                    color: #666;
                    margin-top: 5px;
                    font-size: 0.9em;
                }}
                .schedule-container {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow-x: auto;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th {{
                    background-color: #667eea;
                    color: white;
                    padding: 15px 10px;
                    text-align: center;
                    font-weight: 600;
                    text-transform: uppercase;
                    font-size: 0.9em;
                    letter-spacing: 0.5px;
                    border: 1px solid #5568d3;
                }}
                th.time-header {{
                    background-color: #764ba2;
                    min-width: 100px;
                }}
                td {{
                    padding: 0;
                    border: 1px solid #ddd;
                    vertical-align: top;
                    min-height: 80px;
                    position: relative;
                }}
                td.time-cell {{
                    background-color: #f8f9fa;
                    padding: 15px 10px;
                    text-align: center;
                    font-weight: 600;
                    color: #764ba2;
                    font-family: 'Courier New', monospace;
                    font-size: 0.9em;
                    white-space: nowrap;
                }}
                .course-box {{
                    padding: 10px;
                    margin: 5px;
                    border-radius: 8px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-size: 0.85em;
                    line-height: 1.6;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    min-height: 70px;
                }}
                .course-time {{
                    font-weight: bold;
                    font-size: 0.95em;
                    margin-bottom: 8px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid rgba(255,255,255,0.3);
                }}
                .course-info {{
                    margin: 3px 0;
                }}
                .course-label {{
                    opacity: 0.9;
                    font-size: 0.8em;
                }}
                .empty-cell {{
                    background-color: #fafafa;
                    min-height: 80px;
                }}
                .tabs {{
                    display: flex;
                    justify-content: center;
                    gap: 10px;
                    margin: 20px 0;
                    flex-wrap: wrap;
                }}
                .tab-button {{
                    padding: 12px 24px;
                    background: white;
                    border: 2px solid #667eea;
                    color: #667eea;
                    border-radius: 8px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.3s;
                    font-size: 1em;
                }}
                .tab-button:hover {{
                    background: #f0f4ff;
                }}
                .tab-button.active {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
                }}
                .tab-content {{
                    display: none;
                }}
                .tab-content.active {{
                    display: block;
                }}
            </style>
            <script>
                function showTab(className) {{
                    // Cacher tous les onglets
                    document.querySelectorAll('.tab-content').forEach(tab => {{
                        tab.classList.remove('active');
                    }});
                    document.querySelectorAll('.tab-button').forEach(btn => {{
                        btn.classList.remove('active');
                    }});

                    // Afficher l'onglet sélectionné
                    document.getElementById('tab-' + className).classList.add('active');
                    document.querySelector('[data-class="' + className + '"]').classList.add('active');
                }}
            </script>
        </head>
        <body>
            <div class="header">
                <h1>📅 Planning Scolaire par Classe</h1>
                <p>ID: {schedule.schedule_id}</p>
                <p>Généré le: {datetime.fromisoformat(schedule.created_at).strftime("%d/%m/%Y à %H:%M")}</p>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{len(schedule.slots)}</div>
                    <div class="stat-label">Créneaux</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(set(s.teacher for s in schedule.slots))}</div>
                    <div class="stat-label">Professeurs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(all_classes)}</div>
                    <div class="stat-label">Classes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(set(s.room for s in schedule.slots))}</div>
                    <div class="stat-label">Salles utilisées</div>
                </div>
            </div>

            <div class="tabs">
        """

        # Créer les boutons d'onglets
        for idx, class_name in enumerate(all_classes):
            active_class = "active" if idx == 0 else ""
            # Nettoyer le nom de classe pour l'ID
            clean_name = class_name.replace(" ", "-").replace("'", "")
            html += f'<button class="tab-button {active_class}" data-class="{clean_name}" onclick="showTab(\'{clean_name}\')">🎓 {class_name}</button>\n'

        html += "</div>\n"

        # Créer le contenu de chaque onglet
        for idx, class_name in enumerate(all_classes):
            active_class = "active" if idx == 0 else ""
            clean_name = class_name.replace(" ", "-").replace("'", "")
            grid = grids[class_name]

            html += f"""
            <div id="tab-{clean_name}" class="tab-content {active_class}">
                <div class="schedule-container">
                    <h2 style="text-align: center; color: #667eea; margin-bottom: 20px;">Planning de {class_name}</h2>
                    <table>
                        <thead>
                            <tr>
                                <th class="time-header">Horaires</th>
            """

            # En-tête avec les jours
            for day_name in days_fr:
                html += f"<th>{day_name}</th>\n"

            html += """
                            </tr>
                        </thead>
                        <tbody>
            """

            # Lignes pour chaque créneau horaire
            for time_slot in time_slots:
                start_time, end_time = time_slot
                html += f"""
                            <tr>
                                <td class="time-cell">{start_time.strftime("%H:%M")}<br>-<br>{end_time.strftime("%H:%M")}</td>
                """

                # Colonnes pour chaque jour
                for day_enum in days_enum:
                    courses = grid[day_enum][time_slot]
                    if courses:
                        html += "<td>"
                        for course in courses:
                            html += f"""
                                <div class="course-box">
                                    <div class="course-time">⏰ {course.start_time.strftime("%H:%M")} - {course.end_time.strftime("%H:%M")}</div>
                                    <div class="course-info">👨‍🏫 <span class="course-label">Prof:</span> {course.teacher}</div>
                                    <div class="course-info">🚪 <span class="course-label">Salle:</span> {course.room}</div>
                                </div>
                            """
                        html += "</td>"
                    else:
                        html += '<td class="empty-cell"></td>'

                html += "</tr>\n"

            html += """
                        </tbody>
                    </table>
                </div>
            </div>
            """

        html += """
        </body>
        </html>
        """

        return html

    def render_plotly(self, schedule: Schedule):
        """Génère une visualisation interactive avec Plotly"""
        df = self.to_dataframe(schedule)

        # Créer une figure Gantt-like
        fig = go.Figure()

        # Grouper par professeur
        teachers = df['Professeur'].unique()
        colors_list = list(self.colors.values())

        for i, teacher in enumerate(teachers):
            teacher_data = df[df['Professeur'] == teacher]
            color = colors_list[i % len(colors_list)]

            for _, row in teacher_data.iterrows():
                fig.add_trace(go.Bar(
                    name=teacher,
                    x=[row['Jour']],
                    y=[1],
                    text=f"{row['Classe']}<br>{row['Heure début']}-{row['Heure fin']}",
                    textposition='inside',
                    marker_color=color,
                    showlegend=(i == 0)
                ))

        fig.update_layout(
            title=f"Planning - {schedule.schedule_id}",
            xaxis_title="Jour",
            yaxis_title="Créneaux",
            barmode='stack',
            height=600,
            hovermode='x unified'
        )

        return fig

    def export_to_csv(self, schedule: Schedule, filepath: str):
        """Exporte le planning en CSV"""
        df = self.to_dataframe(schedule)
        df.to_csv(filepath, index=False, encoding='utf-8')
        return filepath
