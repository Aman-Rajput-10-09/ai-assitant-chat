from pydantic import BaseModel


class Student(BaseModel):
    roll_no: str
    name: str
    cgpa: float
    skills: list[str]
    activities: list[str]
    projects: list[str]
