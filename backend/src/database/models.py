from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Time, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Configuration(Base):
    """Table pour stocker les configurations système"""
    __tablename__ = "configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    num_rooms = Column(Integer, default=8)
    num_teachers = Column(Integer, default=7)
    num_classes = Column(Integer, default=3)

    day_start = Column(Time, nullable=False)
    day_end = Column(Time, nullable=False)

    session_duration = Column(Integer, default=90)  # minutes
    break_duration = Column(Integer, default=15)  # minutes
    lunch_break_start = Column(Time, nullable=False)
    lunch_break_end = Column(Time, nullable=False)

    days_in_person = Column(Integer, default=4)
    days_remote = Column(Integer, default=1)

    max_hours_per_day_per_teacher = Column(Integer, default=9)
    prevent_same_teacher_parallel = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    teachers = relationship("Teacher", back_populates="configuration")
    schedules = relationship("ScheduleModel", back_populates="configuration")


class Teacher(Base):
    """Table pour stocker les informations des professeurs"""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    email = Column(String, unique=True, nullable=True)
    total_hours_per_week = Column(Float)
    class_assignments = Column(JSON)  # {"Classe A": 4.5, "Classe B": 4.5}

    configuration_id = Column(Integer, ForeignKey("configurations.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    configuration = relationship("Configuration", back_populates="teachers")
    availabilities = relationship("TeacherAvailabilityModel", back_populates="teacher")


class TeacherAvailabilityModel(Base):
    """Table pour stocker les disponibilités des professeurs"""
    __tablename__ = "teacher_availabilities"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    day_of_week = Column(String)  # lundi, mardi, etc.
    start_time = Column(Time)
    end_time = Column(Time)
    is_available = Column(Boolean, default=True)  # True = disponible, False = indisponible

    raw_constraint = Column(String, nullable=True)  # Contrainte en langage naturel original

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    teacher = relationship("Teacher", back_populates="availabilities")


class ScheduleModel(Base):
    """Table pour stocker les plannings générés"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(String, unique=True, index=True)
    configuration_id = Column(Integer, ForeignKey("configurations.id"))

    week_start_date = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    configuration = relationship("Configuration", back_populates="schedules")
    slots = relationship("ScheduleSlotModel", back_populates="schedule")


class ScheduleSlotModel(Base):
    """Table pour stocker les créneaux individuels d'un planning"""
    __tablename__ = "schedule_slots"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"))

    day_of_week = Column(String)  # lundi, mardi, etc.
    start_time = Column(Time)
    end_time = Column(Time)

    teacher_name = Column(String)
    class_name = Column(String)
    room_name = Column(String)
    subject = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    schedule = relationship("ScheduleModel", back_populates="slots")


class Room(Base):
    """Table pour stocker les informations des salles"""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    capacity = Column(Integer, nullable=True)
    equipment = Column(JSON, nullable=True)  # ["projecteur", "ordinateurs", etc.]

    created_at = Column(DateTime, default=datetime.utcnow)


class Class(Base):
    """Table pour stocker les informations des classes"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    num_students = Column(Integer, nullable=True)
    level = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
