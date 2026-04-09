from models.domain import Student


RANKING_KEYWORDS = {"top", "best", "performing", "performance", "strongest", "rank"}
CGPA_SORT_KEYWORDS = {
    "by cgpa",
    "based on cgpa",
    "highest cgpa",
    "cgpa wise",
    "academic topper",
    "academically strongest",
}
SINGLE_RESULT_KEYWORDS = {
    "only one",
    "one student",
    "single student",
    "top student",
    "best student",
}


class RankingEngine:
    def should_rank(self, question: str) -> bool:
        normalized = question.casefold()
        return any(keyword in normalized for keyword in RANKING_KEYWORDS)

    def should_sort_by_cgpa(self, question: str) -> bool:
        normalized = question.casefold()
        return any(keyword in normalized for keyword in CGPA_SORT_KEYWORDS)

    def requested_result_limit(self, question: str) -> int | None:
        normalized = question.casefold()
        if any(keyword in normalized for keyword in SINGLE_RESULT_KEYWORDS):
            return 1
        return None

    def rank_students(self, students: list[Student], question: str) -> list[Student]:
        if not students:
            return []

        if self.should_sort_by_cgpa(question):
            return sorted(
                students,
                key=lambda student: (student.cgpa, len(student.projects), len(student.skills)),
                reverse=True,
            )

        return sorted(students, key=self._overall_score, reverse=True)

    def _overall_score(self, student: Student) -> float:
        # Skills, projects, and activities matter more than CGPA for broad "best/top" queries.
        normalized_skills = min(len(student.skills) / 4, 1.0)
        normalized_projects = min(len(student.projects) / 3, 1.0)
        normalized_activities = min(len(student.activities) / 3, 1.0)
        normalized_cgpa = student.cgpa / 10

        return (
            normalized_skills * 0.35
            + normalized_projects * 0.30
            + normalized_activities * 0.25
            + normalized_cgpa * 0.10
        )
