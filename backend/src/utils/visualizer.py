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
        """Génère une visualisation HTML du planning"""
        df = self.to_dataframe(schedule)

        # Créer le tableau HTML avec style
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
                .schedule-container {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th {{
                    background-color: #667eea;
                    color: white;
                    padding: 12px;
                    text-align: left;
                    font-weight: 600;
                    text-transform: uppercase;
                    font-size: 0.85em;
                    letter-spacing: 0.5px;
                }}
                td {{
                    padding: 12px;
                    border-bottom: 1px solid #e0e0e0;
                }}
                tr:hover {{
                    background-color: #f8f9fa;
                }}
                .day-cell {{
                    font-weight: 600;
                    color: #667eea;
                }}
                .time-cell {{
                    color: #666;
                    font-family: 'Courier New', monospace;
                }}
                .teacher-cell {{
                    color: #2c3e50;
                    font-weight: 500;
                }}
                .class-badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 15px;
                    background-color: #e3f2fd;
                    color: #1976d2;
                    font-size: 0.9em;
                    font-weight: 500;
                }}
                .room-badge {{
                    display: inline-block;
                    padding: 4px 12px;
                    border-radius: 15px;
                    background-color: #f3e5f5;
                    color: #7b1fa2;
                    font-size: 0.9em;
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
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📅 Planning Scolaire</h1>
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
                    <div class="stat-value">{len(set(s.class_name for s in schedule.slots))}</div>
                    <div class="stat-label">Classes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(set(s.room for s in schedule.slots))}</div>
                    <div class="stat-label">Salles utilisées</div>
                </div>
            </div>

            <div class="schedule-container">
                <table>
                    <thead>
                        <tr>
                            <th>Jour</th>
                            <th>Horaire</th>
                            <th>Professeur</th>
                            <th>Classe</th>
                            <th>Salle</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        for _, row in df.iterrows():
            html += f"""
                        <tr>
                            <td class="day-cell">{row['Jour']}</td>
                            <td class="time-cell">{row['Heure début']} - {row['Heure fin']}</td>
                            <td class="teacher-cell">{row['Professeur']}</td>
                            <td><span class="class-badge">{row['Classe']}</span></td>
                            <td><span class="room-badge">{row['Salle']}</span></td>
                        </tr>
            """

        html += """
                    </tbody>
                </table>
            </div>
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
