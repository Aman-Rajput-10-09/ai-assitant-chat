from sqlalchemy import select
from sqlalchemy.orm import selectinload

from data.db import SessionLocal
from data.tables import ProfileTable, UserTable
from models.domain import Student


class StudentRepository:
    async def list_students(self) -> list[Student]:
        if SessionLocal is None:
            return []

        async with SessionLocal() as session:
            query = (
                select(ProfileTable)
                .join(UserTable, ProfileTable.user_id == UserTable.id)
                .where(UserTable.role == "STUDENT")
                .options(
                    selectinload(ProfileTable.achievements),
                    selectinload(ProfileTable.certifications),
                    selectinload(ProfileTable.tech_events),
                    selectinload(ProfileTable.non_tech_events),
                    selectinload(ProfileTable.organized_events),
                )
            )
            result = await session.execute(query)
            profiles = result.scalars().all()
            return [self._to_student(profile) for profile in profiles]

    def _to_student(self, profile: ProfileTable) -> Student:
        activities = self._build_activities(profile)
        projects = self._build_projects(profile)

        return Student(
            roll_no=profile.roll_no,
            name=profile.name,
            cgpa=profile.cgpa,
            skills=list(profile.skills or []),
            activities=activities,
            projects=projects,
        )

    def _build_activities(self, profile: ProfileTable) -> list[str]:
        values: list[str] = []

        for event in profile.tech_events:
            values.append(event.event_name)
            if event.role:
                values.append(event.role)
            if event.position:
                values.append(event.position)

        for event in profile.non_tech_events:
            values.append(event.event_name)
            if event.category:
                values.append(event.category)
            if event.role:
                values.append(event.role)

        for event in profile.organized_events:
            values.append(event.event_name)
            values.append(event.role)

        return self._dedupe(values)

    def _build_projects(self, profile: ProfileTable) -> list[str]:
        values: list[str] = []

        for achievement in profile.achievements:
            values.append(achievement.title)
            if achievement.desc:
                values.append(achievement.desc)

        for certification in profile.certifications:
            values.append(certification.name)
            values.append(certification.issuer)

        if profile.portfolio:
            values.append("Portfolio")
        if profile.github:
            values.append("GitHub")
        if profile.linkedin:
            values.append("LinkedIn")

        return self._dedupe(values)

    def _dedupe(self, values: list[str]) -> list[str]:
        ordered: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = value.strip()
            if not cleaned:
                continue
            key = cleaned.casefold()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(cleaned)
        return ordered
