from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserTable(Base):
    __tablename__ = "User"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    is_profile_complete: Mapped[bool] = mapped_column("isProfileComplete")
    created_at: Mapped[datetime] = mapped_column("createdAt", DateTime(timezone=True))
    profile: Mapped["ProfileTable | None"] = relationship(back_populates="user")


class ProfileTable(Base):
    __tablename__ = "Profile"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column("userId", ForeignKey("User.id"), unique=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    roll_no: Mapped[str] = mapped_column("rollNo", String, unique=True, nullable=False)
    student_class: Mapped[str] = mapped_column("class", String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    gender: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    parent_name: Mapped[str] = mapped_column("parentName", String, nullable=False)
    parent_phone: Mapped[str] = mapped_column("parentPhone", String, nullable=False)
    cgpa: Mapped[float] = mapped_column(Float, nullable=False)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    linkedin: Mapped[str | None] = mapped_column(String)
    github: Mapped[str | None] = mapped_column(String)
    portfolio: Mapped[str | None] = mapped_column(String)

    user: Mapped[UserTable] = relationship(back_populates="profile")
    achievements: Mapped[list["AchievementTable"]] = relationship(back_populates="profile")
    certifications: Mapped[list["CertificationTable"]] = relationship(back_populates="profile")
    tech_events: Mapped[list["TechEventTable"]] = relationship(back_populates="profile")
    non_tech_events: Mapped[list["NonTechEventTable"]] = relationship(back_populates="profile")
    organized_events: Mapped[list["OrganizedEventTable"]] = relationship(back_populates="profile")


class AchievementTable(Base):
    __tablename__ = "Achievement"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    desc: Mapped[str | None] = mapped_column(Text)
    profile_id: Mapped[str] = mapped_column("profileId", ForeignKey("Profile.id"))
    profile: Mapped[ProfileTable] = relationship(back_populates="achievements")


class CertificationTable(Base):
    __tablename__ = "Certification"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    issuer: Mapped[str] = mapped_column(String, nullable=False)
    issue_date: Mapped[datetime] = mapped_column("issueDate", DateTime(timezone=True))
    credential_url: Mapped[str | None] = mapped_column("credentialUrl", String)
    profile_id: Mapped[str] = mapped_column("profileId", ForeignKey("Profile.id"))
    profile: Mapped[ProfileTable] = relationship(back_populates="certifications")


class TechEventTable(Base):
    __tablename__ = "TechEvent"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_name: Mapped[str] = mapped_column("eventName", String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[str | None] = mapped_column(String)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    profile_id: Mapped[str] = mapped_column("profileId", ForeignKey("Profile.id"))
    profile: Mapped[ProfileTable] = relationship(back_populates="tech_events")


class NonTechEventTable(Base):
    __tablename__ = "NonTechEvent"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_name: Mapped[str] = mapped_column("eventName", String, nullable=False)
    category: Mapped[str | None] = mapped_column(String)
    role: Mapped[str | None] = mapped_column(String)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    profile_id: Mapped[str] = mapped_column("profileId", ForeignKey("Profile.id"))
    profile: Mapped[ProfileTable] = relationship(back_populates="non_tech_events")


class OrganizedEventTable(Base):
    __tablename__ = "OrganizedEvent"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    event_name: Mapped[str] = mapped_column("eventName", String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    participants: Mapped[int | None] = mapped_column(Integer)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    profile_id: Mapped[str] = mapped_column("profileId", ForeignKey("Profile.id"))
    profile: Mapped[ProfileTable] = relationship(back_populates="organized_events")
