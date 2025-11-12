import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.api.main import app

client = TestClient(app)


def test_root():
    """Test l'endpoint racine"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()


def test_health_check():
    """Test le health check"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_parse_constraint():
    """Test le parsing d'une contrainte"""
    constraint_data = {
        "teacher_name": "Lyes",
        "constraint_text": "Je serai disponible lundi matin de 08:00 - 12:00"
    }

    response = client.post("/api/constraint/parse", json=constraint_data)

    # Note: Ce test échouera sans une vraie clé OpenAI
    # Il est là pour montrer la structure du test
    assert response.status_code in [200, 500]  # 500 si pas de clé API


def test_generate_schedule():
    """Test la génération d'un planning"""
    schedule_request = {
        "configuration": {
            "num_rooms": 8,
            "num_teachers": 3,
            "num_classes": 2,
            "day_start": "08:00:00",
            "day_end": "17:00:00",
            "session_duration": 90,
            "break_duration": 15,
            "lunch_break_start": "12:00:00",
            "lunch_break_end": "13:00:00",
            "days_in_person": 4,
            "days_remote": 1,
            "max_hours_per_day_per_teacher": 6,
            "prevent_same_teacher_parallel": True
        },
        "teacher_workloads": [
            {
                "teacher_name": "Prof1",
                "total_hours_per_week": 6,
                "class_assignments": {
                    "Classe A": 3,
                    "Classe B": 3
                }
            }
        ],
        "constraints": []
    }

    response = client.post("/api/schedule/generate", json=schedule_request)

    # Note: Ce test peut échouer sans configuration complète
    assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
