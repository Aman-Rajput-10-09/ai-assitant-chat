import json


STUDENT_SCHEMA = {
    "name": "string",
    "cgpa": "float",
    "skills": ["string"],
    "activities": ["string"],
    "projects": ["string"],
}

FILTER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "filters": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "gt": {"type": "number"},
                    "lt": {"type": "number"},
                    "eq": {
                        "anyOf": [
                            {"type": "string"},
                            {"type": "number"},
                            {"type": "boolean"},
                        ]
                    },
                    "contains": {"type": "string"},
                },
                "additionalProperties": False,
            },
        }
    },
    "required": ["filters"],
    "additionalProperties": False,
}


def build_filter_prompt(question: str, role: str) -> str:
    return (
        "You convert natural language into JSON filters for a student dataset.\n"
        "Return JSON only.\n"
        "Do not include explanations, markdown, or extra text.\n"
        "Use only these exact fields from the schema: name, cgpa, skills, activities, projects.\n"
        "Never invent new fields.\n"
        "Professor queries may use broad terms like technical, AI, backend, frontend, startup, communication, or competitive programming.\n"
        "Map those broad terms to the most relevant schema field instead of inventing new field names.\n"
        "For list fields like skills, activities, and projects, prefer contains instead of eq.\n"
        "Examples:\n"
        '{"filters":{"cgpa":{"gt":9},"projects":{"contains":"software"}}}\n'
        '{"filters":{"skills":{"contains":"technical"}}}\n'
        '{"filters":{"activities":{"contains":"hackathon"}}}\n'
        f"Role: {role}\n"
        f"Student schema: {json.dumps(STUDENT_SCHEMA)}\n"
        "Supported operators: gt, lt, eq, contains.\n"
        "If a field is not mentioned, do not include it.\n"
        f"Question: {question}"
    )


def build_no_results_prompt(question: str, role: str, filters: dict[str, object]) -> str:
    return (
        "Write one short professional sentence for an API response.\n"
        "The sentence should explain that no students were found for the user's query.\n"
        "Use clear English.\n"
        "Do not use markdown.\n"
        "Do not invent students or results.\n"
        f"Role: {role}\n"
        f"Question: {question}\n"
        f"Applied filters: {json.dumps(filters, default=str)}"
    )
