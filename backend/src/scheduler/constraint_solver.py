from ortools.sat.python import cp_model
from typing import List, Dict, Tuple
from datetime import time, timedelta, datetime
from ..models.schemas import (
    SystemConfiguration,
    TeacherWorkload,
    ParsedConstraint,
    ScheduleSlot,
    DayOfWeek
)


class ScheduleGenerator:
    """Générateur de planning utilisant OR-Tools CP-SAT"""

    def __init__(self, configuration: SystemConfiguration):
        self.config = configuration
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        # Génération des créneaux horaires possibles
        self.time_slots = self._generate_time_slots()
        self.days = [day.value for day in DayOfWeek][:5]  # Lundi à Vendredi

    def _generate_time_slots(self) -> List[Tuple[time, time]]:
        """Génère tous les créneaux horaires possibles dans une journée"""
        slots = []
        current_time = datetime.combine(datetime.today(), self.config.day_start)
        end_time = datetime.combine(datetime.today(), self.config.day_end)

        lunch_start = datetime.combine(datetime.today(), self.config.lunch_break_start)
        lunch_end = datetime.combine(datetime.today(), self.config.lunch_break_end)

        while current_time < end_time:
            slot_end = current_time + timedelta(minutes=self.config.session_duration)

            # Éviter la pause déjeuner
            if not (current_time < lunch_end and slot_end > lunch_start):
                if slot_end <= end_time:
                    slots.append((current_time.time(), slot_end.time()))

            # Ajouter la durée de la séance + pause
            current_time = slot_end + timedelta(minutes=self.config.break_duration)

        return slots

    def generate(
        self,
        teacher_workloads: List[TeacherWorkload],
        constraints: List[ParsedConstraint]
    ) -> List[ScheduleSlot]:
        """
        Génère un planning complet en respectant toutes les contraintes
        """
        teachers = [tw.teacher_name for tw in teacher_workloads]
        classes = list(set(
            class_name
            for tw in teacher_workloads
            for class_name in tw.class_assignments.keys()
        ))
        rooms = [f"Salle {i+1}" for i in range(self.config.num_rooms)]

        # Variables de décision : x[t][c][d][s][r] = 1 si prof t enseigne à classe c le jour d au slot s dans salle r
        x = {}
        for t_idx, teacher in enumerate(teachers):
            for c_idx, class_name in enumerate(classes):
                for d_idx, day in enumerate(self.days):
                    for s_idx, slot in enumerate(self.time_slots):
                        for r_idx, room in enumerate(rooms):
                            var_name = f"x_t{t_idx}_c{c_idx}_d{d_idx}_s{s_idx}_r{r_idx}"
                            x[(t_idx, c_idx, d_idx, s_idx, r_idx)] = self.model.NewBoolVar(var_name)

        # CONTRAINTE 1: Un prof ne peut pas être dans deux endroits en même temps
        if self.config.prevent_same_teacher_parallel:
            for t_idx in range(len(teachers)):
                for d_idx in range(len(self.days)):
                    for s_idx in range(len(self.time_slots)):
                        self.model.Add(
                            sum(
                                x[(t_idx, c_idx, d_idx, s_idx, r_idx)]
                                for c_idx in range(len(classes))
                                for r_idx in range(len(rooms))
                            ) <= 1
                        )

        # CONTRAINTE 2: Une salle ne peut accueillir qu'un cours à la fois
        for r_idx in range(len(rooms)):
            for d_idx in range(len(self.days)):
                for s_idx in range(len(self.time_slots)):
                    self.model.Add(
                        sum(
                            x[(t_idx, c_idx, d_idx, s_idx, r_idx)]
                            for t_idx in range(len(teachers))
                            for c_idx in range(len(classes))
                        ) <= 1
                    )

        # CONTRAINTE 3: Une classe ne peut avoir qu'un cours à la fois
        for c_idx in range(len(classes)):
            for d_idx in range(len(self.days)):
                for s_idx in range(len(self.time_slots)):
                    self.model.Add(
                        sum(
                            x[(t_idx, c_idx, d_idx, s_idx, r_idx)]
                            for t_idx in range(len(teachers))
                            for r_idx in range(len(rooms))
                        ) <= 1
                    )

        # CONTRAINTE 4: Respecter la charge de travail de chaque prof par classe
        for t_idx, tw in enumerate(teacher_workloads):
            for class_name, required_hours in tw.class_assignments.items():
                c_idx = classes.index(class_name)
                # Convertir heures en nombre de séances
                num_sessions = int(required_hours / (self.config.session_duration / 60))

                self.model.Add(
                    sum(
                        x[(t_idx, c_idx, d_idx, s_idx, r_idx)]
                        for d_idx in range(len(self.days))
                        for s_idx in range(len(self.time_slots))
                        for r_idx in range(len(rooms))
                    ) == num_sessions
                )

        # CONTRAINTE 5: Respecter le max d'heures par jour par prof
        max_slots_per_day = int(self.config.max_hours_per_day_per_teacher / (self.config.session_duration / 60))
        for t_idx in range(len(teachers)):
            for d_idx in range(len(self.days)):
                self.model.Add(
                    sum(
                        x[(t_idx, c_idx, d_idx, s_idx, r_idx)]
                        for c_idx in range(len(classes))
                        for s_idx in range(len(self.time_slots))
                        for r_idx in range(len(rooms))
                    ) <= max_slots_per_day
                )

        # CONTRAINTE 6: Appliquer les disponibilités des profs
        for constraint in constraints:
            t_idx = teachers.index(constraint.teacher_name)

            for availability in constraint.availabilities:
                d_idx = self.days.index(availability.day.value)

                # Marquer les créneaux disponibles et indisponibles
                for s_idx, (slot_start, slot_end) in enumerate(self.time_slots):
                    is_available = False

                    # Vérifier si le créneau est dans les plages de disponibilité
                    for time_slot in availability.time_slots:
                        if slot_start >= time_slot.start and slot_end <= time_slot.end:
                            is_available = True
                            break

                    # Si pas disponible, interdire ce créneau
                    if not is_available:
                        for c_idx in range(len(classes)):
                            for r_idx in range(len(rooms)):
                                self.model.Add(x[(t_idx, c_idx, d_idx, s_idx, r_idx)] == 0)

        # Résoudre le problème
        status = self.solver.Solve(self.model)

        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            return self._extract_schedule(x, teachers, classes, rooms)
        else:
            raise Exception("Impossible de générer un planning avec ces contraintes")

    def _extract_schedule(
        self,
        x: Dict,
        teachers: List[str],
        classes: List[str],
        rooms: List[str]
    ) -> List[ScheduleSlot]:
        """Extrait le planning de la solution"""
        schedule = []

        for (t_idx, c_idx, d_idx, s_idx, r_idx), var in x.items():
            if self.solver.Value(var) == 1:
                schedule.append(ScheduleSlot(
                    day=DayOfWeek(self.days[d_idx]),
                    start_time=self.time_slots[s_idx][0],
                    end_time=self.time_slots[s_idx][1],
                    teacher=teachers[t_idx],
                    class_name=classes[c_idx],
                    room=rooms[r_idx]
                ))

        # Trier par jour puis par heure
        day_order = {day: i for i, day in enumerate(self.days)}
        schedule.sort(key=lambda s: (day_order[s.day.value], s.start_time))

        return schedule
