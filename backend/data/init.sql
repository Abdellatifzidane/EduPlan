-- Script d'initialisation de la base de données PostgreSQL pour EduPlan

-- Créer les extensions nécessaires
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Table des configurations système
CREATE TABLE IF NOT EXISTS configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    num_rooms INTEGER NOT NULL,
    num_teachers INTEGER NOT NULL,
    num_classes INTEGER NOT NULL,
    day_start TIME NOT NULL,
    day_end TIME NOT NULL,
    session_duration INTEGER NOT NULL,
    break_duration INTEGER NOT NULL,
    lunch_break_start TIME NOT NULL,
    lunch_break_end TIME NOT NULL,
    days_in_person INTEGER DEFAULT 4,
    days_remote INTEGER DEFAULT 1,
    max_hours_per_day_per_teacher INTEGER DEFAULT 9,
    prevent_same_teacher_parallel BOOLEAN DEFAULT TRUE,
    max_consecutive_sessions INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des professeurs
CREATE TABLE IF NOT EXISTS teachers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    total_hours_per_week DECIMAL(5,2) NOT NULL,
    class_assignments JSONB,
    configuration_id INTEGER REFERENCES configurations(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, configuration_id)
);

-- Table des plannings avec statut de validation
CREATE TABLE IF NOT EXISTS schedules (
    id SERIAL PRIMARY KEY,
    schedule_id VARCHAR(255) UNIQUE NOT NULL,
    configuration_id INTEGER REFERENCES configurations(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'draft', -- draft, validated, archived
    validated_at TIMESTAMP,
    validated_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Table des créneaux de planning
CREATE TABLE IF NOT EXISTS schedule_slots (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE CASCADE,
    day_of_week VARCHAR(20) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    teacher_name VARCHAR(255) NOT NULL,
    class_name VARCHAR(255) NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(schedule_id, day_of_week, start_time, room_name)
);

-- Table pour l'historique des modifications (audit trail)
CREATE TABLE IF NOT EXISTS schedule_modifications (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE CASCADE,
    user_message TEXT NOT NULL,
    action_taken JSONB NOT NULL,
    modified_by VARCHAR(255),
    success BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour les conversations avec l'agent (stockage persistant)
CREATE TABLE IF NOT EXISTS agent_conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE SET NULL,
    role VARCHAR(50) NOT NULL, -- 'user' ou 'assistant'
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour améliorer les performances
CREATE INDEX idx_schedules_status ON schedules(status);
CREATE INDEX idx_schedules_created_at ON schedules(created_at DESC);
CREATE INDEX idx_schedule_slots_schedule_id ON schedule_slots(schedule_id);
CREATE INDEX idx_schedule_slots_teacher ON schedule_slots(teacher_name);
CREATE INDEX idx_schedule_slots_class ON schedule_slots(class_name);
CREATE INDEX idx_agent_conversations_session ON agent_conversations(session_id);
CREATE INDEX idx_agent_conversations_schedule ON agent_conversations(schedule_id);

-- Fonction pour mettre à jour le timestamp updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour auto-update du timestamp
CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE
    ON configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE
    ON schedules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Vue pour les statistiques de planning
CREATE VIEW schedule_statistics AS
SELECT
    s.id,
    s.schedule_id,
    s.status,
    c.name as configuration_name,
    COUNT(DISTINCT ss.teacher_name) as num_teachers,
    COUNT(DISTINCT ss.class_name) as num_classes,
    COUNT(DISTINCT ss.room_name) as num_rooms,
    COUNT(ss.id) as total_slots,
    s.created_at,
    s.validated_at
FROM schedules s
JOIN configurations c ON s.configuration_id = c.id
LEFT JOIN schedule_slots ss ON s.id = ss.schedule_id
GROUP BY s.id, s.schedule_id, s.status, c.name, s.created_at, s.validated_at;

-- Données de test initiales (optionnel)
INSERT INTO configurations (name, num_rooms, num_teachers, num_classes, day_start, day_end,
                          session_duration, break_duration, lunch_break_start, lunch_break_end)
VALUES ('Configuration par défaut', 8, 7, 3, '08:00', '19:00', 90, 15, '13:00', '14:00')
ON CONFLICT (name) DO NOTHING;