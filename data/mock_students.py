from models.domain import Student


MOCK_STUDENTS: list[Student] = [
    Student(
        name="Aarav Sharma",
        cgpa=8.7,
        skills=["Python", "FastAPI", "Machine Learning"],
        activities=["Hackathon", "Coding Club"],
        projects=["AI Research Assistant", "Campus Helpdesk Bot"],
    ),
    Student(
        name="Diya Patel",
        cgpa=7.9,
        skills=["Java", "Spring Boot", "SQL"],
        activities=["Debate", "Volunteer"],
        projects=["Attendance Tracker", "Library Manager"],
    ),
    Student(
        name="Rohan Iyer",
        cgpa=9.1,
        skills=["Python", "Data Science", "NLP"],
        activities=["Research", "Hackathon"],
        projects=["Resume Screener", "Student Recommendation Engine"],
    ),
    Student(
        name="Meera Nair",
        cgpa=8.2,
        skills=["React", "Node.js", "UI Design"],
        activities=["Design Club", "Startup Cell"],
        projects=["Portfolio Builder", "Event Platform"],
    ),

    Student(
        name="Ankit Gopal Anand",
        cgpa=6.8,
        skills=["React", "Node.js", "UI Design","Android Development","Kotlin","Python","Competitive Programming"],
        activities=["Design Club", "Startup Cell","CP"],
        projects=["Portfolio Builder", "Event Platform","Competitive Programming Tracker"],
    ),

    Student(
        name="Anurag Ankita Aman Hero",
        cgpa=6.8,
        skills=["Communication", "Teamwork", "Leadership"],
        activities=["Startup Cell"],
        projects=["Campus Event Organizer", "Student Mentorship Program"],
    ),
]
