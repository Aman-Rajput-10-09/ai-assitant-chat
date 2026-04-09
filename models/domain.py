from pydantic import BaseModel


class Student(BaseModel):
    name: str
    cgpa: float
    skills: list[str]
    activities: list[str]
    projects: list[str]

