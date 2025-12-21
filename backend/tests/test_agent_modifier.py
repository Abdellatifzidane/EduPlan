"""
Test de l'agent modificateur de planning
"""
from datetime import time
from src.nlp_agent.agent_modifier import AgentModifier
from src.models.schemas import ScheduleSlot, DayOfWeek


def create_sample_schedule():
    """Créer un planning exemple"""
    return [
        ScheduleSlot(
            day=DayOfWeek.MONDAY,
            start_time=time(8, 0),
            end_time=time(9, 30),
            teacher="Prof_1",
            class_name="Classe A",
            room="Salle 1"
        ),
        ScheduleSlot(
            day=DayOfWeek.MONDAY,
            start_time=time(9, 45),
            end_time=time(11, 15),
            teacher="Prof_1",
            class_name="Classe A",
            room="Salle 1"
        ),
        ScheduleSlot(
            day=DayOfWeek.TUESDAY,
            start_time=time(10, 0),
            end_time=time(11, 30),
            teacher="Prof_2",
            class_name="Classe B",
            room="Salle 3"
        ),
        ScheduleSlot(
            day=DayOfWeek.FRIDAY,
            start_time=time(14, 0),
            end_time=time(15, 30),
            teacher="Prof_3",
            class_name="Classe A",
            room="Salle 5"
        ),
    ]


def test_delete_action():
    """Test de suppression d'un créneau"""
    print("\n🧪 Test 1: Supprimer un créneau")
    print("=" * 60)

    agent = AgentModifier()
    schedule = create_sample_schedule()

    print(f"Planning initial: {len(schedule)} créneaux")

    # Demande de suppression
    user_message = "Supprimer le cours de Prof_1 le lundi à 8h"

    print(f"Demande: '{user_message}'")

    action_data = agent.parse_modification_request(user_message, schedule)

    print(f"\n📋 Action parsée:")
    print(f"   Type: {action_data.get('action')}")
    print(f"   Paramètres: {action_data.get('parameters')}")

    # Appliquer la modification
    modified_schedule, message = agent.apply_modification(action_data, schedule)

    print(f"\n✅ Résultat: {message}")
    print(f"   Planning modifié: {len(modified_schedule)} créneaux")

    assert len(modified_schedule) == len(schedule) - 1, "Un créneau devrait être supprimé"
    print("✅ Test réussi!\n")


def test_add_action():
    """Test d'ajout d'un créneau"""
    print("\n🧪 Test 2: Ajouter un créneau")
    print("=" * 60)

    agent = AgentModifier()
    schedule = create_sample_schedule()

    print(f"Planning initial: {len(schedule)} créneaux")

    # Demande d'ajout
    user_message = "Ajouter un cours de Prof_2 pour Classe A le jeudi de 9h à 10h30 dans Salle 2"

    print(f"Demande: '{user_message}'")

    action_data = agent.parse_modification_request(user_message, schedule)

    print(f"\n📋 Action parsée:")
    print(f"   Type: {action_data.get('action')}")
    print(f"   Paramètres: {action_data.get('parameters')}")

    # Appliquer la modification
    modified_schedule, message = agent.apply_modification(action_data, schedule)

    print(f"\n✅ Résultat: {message}")
    print(f"   Planning modifié: {len(modified_schedule)} créneaux")

    assert len(modified_schedule) == len(schedule) + 1, "Un créneau devrait être ajouté"
    print("✅ Test réussi!\n")


def test_modify_room():
    """Test de changement de salle"""
    print("\n🧪 Test 3: Changer la salle d'un cours")
    print("=" * 60)

    agent = AgentModifier()
    schedule = create_sample_schedule()

    print(f"Planning initial: {len(schedule)} créneaux")
    print(f"Salle initiale Prof_1 lundi 8h: {schedule[0].room}")

    # Demande de changement de salle
    user_message = "Changer la salle du cours de Prof_1 lundi 8h en Salle 10"

    print(f"Demande: '{user_message}'")

    action_data = agent.parse_modification_request(user_message, schedule)

    print(f"\n📋 Action parsée:")
    print(f"   Type: {action_data.get('action')}")
    print(f"   Paramètres: {action_data.get('parameters')}")

    # Appliquer la modification
    modified_schedule, message = agent.apply_modification(action_data, schedule)

    print(f"\n✅ Résultat: {message}")
    print(f"   Nouvelle salle: {modified_schedule[0].room}")

    assert modified_schedule[0].room == "Salle 10", "La salle devrait être changée"
    print("✅ Test réussi!\n")


def test_delete_all_friday():
    """Test de suppression de tous les cours d'un jour"""
    print("\n🧪 Test 4: Supprimer tous les cours du vendredi")
    print("=" * 60)

    agent = AgentModifier()
    schedule = create_sample_schedule()

    print(f"Planning initial: {len(schedule)} créneaux")

    # Demande de suppression massive
    user_message = "Supprimer tous les cours du vendredi"

    print(f"Demande: '{user_message}'")

    action_data = agent.parse_modification_request(user_message, schedule)

    print(f"\n📋 Action parsée:")
    print(f"   Type: {action_data.get('action')}")
    print(f"   Paramètres: {action_data.get('parameters')}")

    # Appliquer la modification
    modified_schedule, message = agent.apply_modification(action_data, schedule)

    print(f"\n✅ Résultat: {message}")
    print(f"   Planning modifié: {len(modified_schedule)} créneaux")

    # Vérifier qu'il ne reste plus de cours le vendredi
    friday_courses = [s for s in modified_schedule if s.day == DayOfWeek.FRIDAY]
    assert len(friday_courses) == 0, "Tous les cours du vendredi devraient être supprimés"
    print("✅ Test réussi!\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTS - Agent Modificateur de Planning")
    print("=" * 60)

    try:
        test_delete_action()
        test_add_action()
        test_modify_room()
        test_delete_all_friday()

        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS PASSÉS!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
