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

            # Si le créneau chevauche la pause déjeuner, reprendre après la pause
            if current_time < lunch_end and slot_end > lunch_start:
                # Reprendre directement après la pause déjeuner
                current_time = lunch_end
                continue

            # Ajouter le créneau si valide
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

            # Identifier les jours où le prof est disponible
            available_days = set(av.day.value for av in constraint.availabilities)

            # ÉTAPE 1: Interdire TOUS les jours NON mentionnés
            for d_idx, day in enumerate(self.days):
                if day not in available_days:
                    # Ce jour n'est PAS disponible -> interdire TOUS les créneaux
                    for s_idx in range(len(self.time_slots)):
                        for c_idx in range(len(classes)):
                            for r_idx in range(len(rooms)):
                                self.model.Add(x[(t_idx, c_idx, d_idx, s_idx, r_idx)] == 0)

            # ÉTAPE 2: Pour les jours disponibles, vérifier les créneaux horaires
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

        # CONTRAINTE 7: Maximum de séances consécutives par (professeur, classe)
        # Pour chaque couple (prof, classe), limiter les séances consécutives
        max_consecutive = getattr(self.config, 'max_consecutive_sessions', 3)

        for t_idx in range(len(teachers)):
            for c_idx in range(len(classes)):
                for d_idx in range(len(self.days)):
                    # Si on a assez de créneaux pour vérifier
                    if len(self.time_slots) > max_consecutive:
                        for s_idx in range(len(self.time_slots) - max_consecutive):
                            # Vérifier une fenêtre de (max_consecutive + 1) créneaux consécutifs
                            self.model.Add(
                                sum(
                                    x[(t_idx, c_idx, d_idx, s_idx + offset, r_idx)]
                                    for r_idx in range(len(rooms))
                                    for offset in range(max_consecutive + 1)
                                ) <= max_consecutive  # Maximum X cours consécutifs pour ce (prof, classe)
                            )

        # CONTRAINTE 8: FORCER tous les cours d'un (prof, classe) à être sur un seul jour
        # Créer une variable par (prof, classe, jour) indiquant si ce jour est utilisé
        day_used = {}
        for t_idx in range(len(teachers)):
            for c_idx in range(len(classes)):
                for d_idx in range(len(self.days)):
                    var_name = f"day_used_t{t_idx}_c{c_idx}_d{d_idx}"
                    day_used[(t_idx, c_idx, d_idx)] = self.model.NewBoolVar(var_name)

                    # day_used = 1 si au moins un cours ce jour
                    has_course_this_day = [
                        x[(t_idx, c_idx, d_idx, s_idx, r_idx)]
                        for s_idx in range(len(self.time_slots))
                        for r_idx in range(len(rooms))
                    ]

                    # Si au moins un cours ce jour, day_used = 1
                    self.model.Add(sum(has_course_this_day) >= 1).OnlyEnforceIf(day_used[(t_idx, c_idx, d_idx)])
                    self.model.Add(sum(has_course_this_day) == 0).OnlyEnforceIf(day_used[(t_idx, c_idx, d_idx)].Not())

                # FORCER: maximum 1 jour utilisé par (prof, classe)
                # C'est-à-dire : tous les cours du prof pour cette classe doivent être le même jour
                self.model.Add(
                    sum(day_used[(t_idx, c_idx, d_idx)] for d_idx in range(len(self.days))) <= 1
                )

        # CONTRAINTE 8bis: FORCER les cours consécutifs sans trou (pour un même prof, classe, jour)
        for t_idx in range(len(teachers)):
            for c_idx in range(len(classes)):
                for d_idx in range(len(self.days)):
                    # Trouver le premier et dernier créneau de ce (prof, classe, jour)
                    for s_start in range(len(self.time_slots)):
                        for s_end in range(s_start + 2, len(self.time_slots)):
                            # Créer des variables pour premier et dernier créneau
                            has_start = self.model.NewBoolVar(f"start_t{t_idx}_c{c_idx}_d{d_idx}_s{s_start}")
                            has_end = self.model.NewBoolVar(f"end_t{t_idx}_c{c_idx}_d{d_idx}_s{s_end}")

                            # has_start = 1 si cours au slot s_start
                            self.model.Add(sum(x[(t_idx, c_idx, d_idx, s_start, r_idx)] for r_idx in range(len(rooms))) >= 1).OnlyEnforceIf(has_start)
                            self.model.Add(sum(x[(t_idx, c_idx, d_idx, s_start, r_idx)] for r_idx in range(len(rooms))) == 0).OnlyEnforceIf(has_start.Not())

                            # has_end = 1 si cours au slot s_end
                            self.model.Add(sum(x[(t_idx, c_idx, d_idx, s_end, r_idx)] for r_idx in range(len(rooms))) >= 1).OnlyEnforceIf(has_end)
                            self.model.Add(sum(x[(t_idx, c_idx, d_idx, s_end, r_idx)] for r_idx in range(len(rooms))) == 0).OnlyEnforceIf(has_end.Not())

                            # Si cours au slot s_start ET cours au slot s_end, TOUS les slots intermédiaires doivent avoir un cours
                            for s_middle in range(s_start + 1, s_end):
                                has_middle = self.model.NewBoolVar(f"middle_t{t_idx}_c{c_idx}_d{d_idx}_s{s_start}_to_{s_end}_mid{s_middle}")

                                self.model.Add(sum(x[(t_idx, c_idx, d_idx, s_middle, r_idx)] for r_idx in range(len(rooms))) >= 1).OnlyEnforceIf(has_middle)
                                self.model.Add(sum(x[(t_idx, c_idx, d_idx, s_middle, r_idx)] for r_idx in range(len(rooms))) == 0).OnlyEnforceIf(has_middle.Not())

                                # Si has_start=1 ET has_end=1, alors has_middle DOIT être 1
                                # Équivalent: has_start=0 OR has_end=0 OR has_middle=1
                                self.model.AddBoolOr([has_start.Not(), has_end.Not(), has_middle])

        # CONTRAINTE 9: FORCER les cours d'une classe à être TOUS consécutifs dans la journée (sans aucun trou)
        # Pour chaque classe et jour, si elle a des cours, ils doivent être en bloc continu
        for c_idx in range(len(classes)):
            for d_idx in range(len(self.days)):
                # Pour chaque paire de créneaux (début, fin) possibles
                for s_start in range(len(self.time_slots)):
                    for s_end in range(s_start + 2, len(self.time_slots)):
                        # Variables pour premier et dernier créneau de la classe ce jour
                        has_start = self.model.NewBoolVar(f"class{c_idx}_d{d_idx}_start{s_start}")
                        has_end = self.model.NewBoolVar(f"class{c_idx}_d{d_idx}_end{s_end}")

                        # has_start = 1 si la classe a un cours au slot s_start
                        self.model.Add(
                            sum(x[(t_idx, c_idx, d_idx, s_start, r_idx)]
                                for t_idx in range(len(teachers))
                                for r_idx in range(len(rooms))) >= 1
                        ).OnlyEnforceIf(has_start)
                        self.model.Add(
                            sum(x[(t_idx, c_idx, d_idx, s_start, r_idx)]
                                for t_idx in range(len(teachers))
                                for r_idx in range(len(rooms))) == 0
                        ).OnlyEnforceIf(has_start.Not())

                        # has_end = 1 si la classe a un cours au slot s_end
                        self.model.Add(
                            sum(x[(t_idx, c_idx, d_idx, s_end, r_idx)]
                                for t_idx in range(len(teachers))
                                for r_idx in range(len(rooms))) >= 1
                        ).OnlyEnforceIf(has_end)
                        self.model.Add(
                            sum(x[(t_idx, c_idx, d_idx, s_end, r_idx)]
                                for t_idx in range(len(teachers))
                                for r_idx in range(len(rooms))) == 0
                        ).OnlyEnforceIf(has_end.Not())

                        # Si la classe a cours au slot s_start ET s_end, TOUS les slots intermédiaires doivent avoir cours
                        for s_middle in range(s_start + 1, s_end):
                            has_middle = self.model.NewBoolVar(f"class{c_idx}_d{d_idx}_mid{s_start}_{s_end}_{s_middle}")

                            self.model.Add(
                                sum(x[(t_idx, c_idx, d_idx, s_middle, r_idx)]
                                    for t_idx in range(len(teachers))
                                    for r_idx in range(len(rooms))) >= 1
                            ).OnlyEnforceIf(has_middle)
                            self.model.Add(
                                sum(x[(t_idx, c_idx, d_idx, s_middle, r_idx)]
                                    for t_idx in range(len(teachers))
                                    for r_idx in range(len(rooms))) == 0
                            ).OnlyEnforceIf(has_middle.Not())

                            # Si has_start=1 ET has_end=1, alors has_middle DOIT être 1
                            self.model.AddBoolOr([has_start.Not(), has_end.Not(), has_middle])

        # CONTRAINTE 10: Une classe ne change pas de prof entre deux créneaux consécutifs
        # Si une classe a un cours au slot s et un cours au slot s+1, ce doit être le même prof
        for c_idx in range(len(classes)):
            for d_idx in range(len(self.days)):
                for s_idx in range(len(self.time_slots) - 1):
                    # Pour chaque paire de profs différents
                    for t1_idx in range(len(teachers)):
                        for t2_idx in range(len(teachers)):
                            if t1_idx != t2_idx:
                                has_t1_at_s = self.model.NewBoolVar(f"c{c_idx}_t{t1_idx}_d{d_idx}_s{s_idx}")
                                has_t2_at_s_plus_1 = self.model.NewBoolVar(f"c{c_idx}_t{t2_idx}_d{d_idx}_s{s_idx + 1}")

                                # has_t1_at_s = 1 si prof t1 enseigne à classe c au slot s
                                self.model.Add(sum(x[(t1_idx, c_idx, d_idx, s_idx, r_idx)] for r_idx in range(len(rooms))) >= 1).OnlyEnforceIf(has_t1_at_s)
                                self.model.Add(sum(x[(t1_idx, c_idx, d_idx, s_idx, r_idx)] for r_idx in range(len(rooms))) == 0).OnlyEnforceIf(has_t1_at_s.Not())

                                # has_t2_at_s_plus_1 = 1 si prof t2 enseigne à classe c au slot s+1
                                self.model.Add(sum(x[(t2_idx, c_idx, d_idx, s_idx + 1, r_idx)] for r_idx in range(len(rooms))) >= 1).OnlyEnforceIf(has_t2_at_s_plus_1)
                                self.model.Add(sum(x[(t2_idx, c_idx, d_idx, s_idx + 1, r_idx)] for r_idx in range(len(rooms))) == 0).OnlyEnforceIf(has_t2_at_s_plus_1.Not())

                                # Interdire: has_t1_at_s=1 ET has_t2_at_s_plus_1=1
                                self.model.AddBoolOr([has_t1_at_s.Not(), has_t2_at_s_plus_1.Not()])

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
