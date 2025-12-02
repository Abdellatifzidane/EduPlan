"""
Test pour reproduire le bug : Prof_1 disponible UNIQUEMENT le vendredi
mais le système lui assigne des cours mardi et mercredi
"""
import requests

API_URL = "http://localhost:8000"


def test_prof_only_available_friday():
    """
    Test critique: Prof_1 est disponible UNIQUEMENT le vendredi
    Le système NE DOIT PAS lui assigner de cours d'autres jours
    """

    request_data = {
        "configuration": {
            "num_rooms": 3,
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
                "total_hours_per_week": 3.0,
                "class_assignments": {
                    "Classe A": 1.5,
                    "Classe B": 1.5
                }
            },
            {
                "teacher_name": "Prof_2",
                "total_hours_per_week": 3.0,
                "class_assignments": {
                    "Classe A": 1.5,
                    "Classe B": 1.5
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
                        "day": "vendredi",  # UNIQUEMENT LE VENDREDI
                        "time_slots": [
                            {"start": "08:00:00", "end": "17:00:00"}
                        ]
                    }
                ]
            }
            # Prof_2 et Prof_3 n'ont pas de contraintes (disponibles tous les jours)
        ]
    }

    print("=" * 70)
    print("TEST CRITIQUE: Prof_1 disponible UNIQUEMENT le vendredi")
    print("=" * 70)

    response = requests.post(
        f"{API_URL}/api/schedule/generate",
        json=request_data,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Planning généré: {len(result['schedule']['slots'])} créneaux")

        # Vérifier les jours où Prof_1 a des cours
        prof1_days = set()
        print("\n📅 Créneaux de Prof_1:")
        for slot in result['schedule']['slots']:
            if slot['teacher'] == "Prof_1":
                prof1_days.add(slot['day'])
                print(f"   {slot['day']} {slot['start_time']} - {slot['end_time']} → {slot['class_name']}")

        print("\n🔍 Vérification:")
        if prof1_days == {"vendredi"}:
            print("   ✅ Prof_1 n'a des cours QUE le vendredi (correct!)")
            return True
        else:
            print(f"   ❌ BUG DÉTECTÉ! Prof_1 a des cours sur: {prof1_days}")
            print(f"   ❌ Attendu: {{'vendredi'}}")
            print(f"   ❌ Prof_1 ne devrait PAS avoir de cours {prof1_days - {'vendredi'}}")
            return False

    else:
        print(f"❌ Erreur API: {response.status_code}")
        print(response.json())
        return False


if __name__ == "__main__":
    print("\n🧪 Reproduction du bug de disponibilité...\n")
    success = test_prof_only_available_friday()

    print("\n" + "=" * 70)
    if success:
        print("✅ TEST PASSÉ - Bug corrigé!")
    else:
        print("❌ TEST ÉCHOUÉ - Bug toujours présent")
    print("=" * 70)
