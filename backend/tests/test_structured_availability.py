"""
Test pour valider le nouveau système de disponibilités structurées
"""
import requests
import json
from datetime import time

API_URL = "http://localhost:8000"


def test_structured_availability_api():
    """Test de génération de planning avec disponibilités structurées"""

    # Configuration de test
    request_data = {
        "configuration": {
            "num_rooms": 5,
            "num_teachers": 3,
            "num_classes": 2,
            "day_start": "08:00:00",
            "day_end": "17:00:00",
            "session_duration": 90,
            "break_duration": 15,
            "lunch_break_start": "12:00:00",
            "lunch_break_end": "13:00:00",
            "days_in_person": 5,
            "days_remote": 0,
            "max_hours_per_day_per_teacher": 6,
            "prevent_same_teacher_parallel": True,
            "max_consecutive_sessions": 3
        },
        "teacher_workloads": [
            {
                "teacher_name": "Prof_1",
                "total_hours_per_week": 4.5,
                "class_assignments": {
                    "Classe A": 3.0,
                    "Classe B": 1.5
                }
            },
            {
                "teacher_name": "Prof_2",
                "total_hours_per_week": 4.5,
                "class_assignments": {
                    "Classe A": 1.5,
                    "Classe B": 3.0
                }
            },
            {
                "teacher_name": "Prof_3",
                "total_hours_per_week": 3.0,
                "class_assignments": {
                    "Classe A": 1.5,
                    "Classe B": 1.5
                }
            }
        ],
        "structured_availabilities": [
            {
                "teacher_name": "Prof_1",
                "availabilities": [
                    {
                        "teacher_name": "Prof_1",
                        "day": "lundi",
                        "time_slots": [
                            {"start": "08:00:00", "end": "12:00:00"}
                        ]
                    },
                    {
                        "teacher_name": "Prof_1",
                        "day": "mardi",
                        "time_slots": [
                            {"start": "08:00:00", "end": "12:00:00"}
                        ]
                    }
                ]
            },
            {
                "teacher_name": "Prof_2",
                "availabilities": [
                    {
                        "teacher_name": "Prof_2",
                        "day": "mercredi",
                        "time_slots": [
                            {"start": "08:00:00", "end": "12:00:00"}
                        ]
                    },
                    {
                        "teacher_name": "Prof_2",
                        "day": "jeudi",
                        "time_slots": [
                            {"start": "08:00:00", "end": "17:00:00"}
                        ]
                    }
                ]
            },
            {
                "teacher_name": "Prof_3",
                "availabilities": [
                    {
                        "teacher_name": "Prof_3",
                        "day": "vendredi",
                        "time_slots": [
                            {"start": "08:00:00", "end": "17:00:00"}
                        ]
                    }
                ]
            }
        ]
    }

    print("🧪 Test 1: Vérifier la santé de l'API...")
    health_response = requests.get(f"{API_URL}/health")
    assert health_response.status_code == 200, "API non accessible"
    print("✅ API accessible")

    print("\n🧪 Test 2: Générer un planning avec disponibilités structurées...")
    response = requests.post(
        f"{API_URL}/api/schedule/generate",
        json=request_data,
        timeout=60
    )

    print(f"Status code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Planning généré avec succès!")
        print(f"   Message: {result['message']}")
        print(f"   Nombre de créneaux: {len(result['schedule']['slots'])}")

        # Vérifier que les contraintes sont respectées
        print("\n🔍 Vérification des contraintes:")

        # Regrouper les slots par prof et classe
        prof_class_days = {}
        for slot in result['schedule']['slots']:
            key = (slot['teacher'], slot['class_name'])
            if key not in prof_class_days:
                prof_class_days[key] = set()
            prof_class_days[key].add(slot['day'])

        # Vérifier qu'un prof n'enseigne une classe que sur un seul jour
        all_single_day = True
        for (prof, class_name), days in prof_class_days.items():
            if len(days) > 1:
                print(f"   ❌ {prof} → {class_name} dispersé sur {len(days)} jours: {days}")
                all_single_day = False
            else:
                print(f"   ✅ {prof} → {class_name} groupé sur 1 jour: {list(days)[0]}")

        if all_single_day:
            print("\n✅ Toutes les contraintes de regroupement sont respectées!")

        # Vérifier les disponibilités
        print("\n🔍 Vérification des disponibilités:")
        for slot in result['schedule']['slots']:
            teacher_name = slot['teacher']
            day = slot['day']
            print(f"   {teacher_name} a un cours le {day}")

        return True

    else:
        print(f"❌ Erreur: {response.status_code}")
        print(response.json())
        return False


def test_empty_availability():
    """Test avec un prof sans contrainte de disponibilité"""

    request_data = {
        "configuration": {
            "num_rooms": 3,
            "num_teachers": 1,
            "num_classes": 1,
            "day_start": "08:00:00",
            "day_end": "12:00:00",
            "session_duration": 90,
            "break_duration": 15,
            "lunch_break_start": "12:00:00",
            "lunch_break_end": "13:00:00",
            "days_in_person": 5,
            "days_remote": 0,
            "max_hours_per_day_per_teacher": 6,
            "prevent_same_teacher_parallel": True,
            "max_consecutive_sessions": 3
        },
        "teacher_workloads": [
            {
                "teacher_name": "Prof_1",
                "total_hours_per_week": 1.5,
                "class_assignments": {
                    "Classe A": 1.5
                }
            }
        ],
        "structured_availabilities": []  # Pas de contraintes
    }

    print("\n🧪 Test 3: Planning sans contrainte de disponibilité...")
    response = requests.post(
        f"{API_URL}/api/schedule/generate",
        json=request_data,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Planning généré sans contrainte!")
        print(f"   Créneaux: {len(result['schedule']['slots'])}")
        return True
    else:
        print(f"❌ Erreur: {response.status_code}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("TESTS - Système de disponibilités structurées")
    print("=" * 60)

    try:
        success1 = test_structured_availability_api()
        success2 = test_empty_availability()

        print("\n" + "=" * 60)
        if success1 and success2:
            print("✅ TOUS LES TESTS PASSÉS!")
        else:
            print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")
        import traceback
        traceback.print_exc()
