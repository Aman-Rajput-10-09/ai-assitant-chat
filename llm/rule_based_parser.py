import re

from models.filters import FilterCondition, FilterExtractionResult


FIELD_ALIASES = {
    "name": "name",
    "cgpa": "cgpa",
    "skill": "skills",
    "skills": "skills",
    "activity": "activities",
    "activities": "activities",
    "project": "projects",
    "projects": "projects",
}

TEXT_VALUE_PATTERN = re.compile(
    r"\b(name|skill|skills|activity|activities|project|projects)\s*(?:=|is|has|with)\s*([a-zA-Z][a-zA-Z0-9 .+-]*)",
    re.IGNORECASE,
)
CGPA_PATTERN = re.compile(r"\bcgpa\s*(>=|<=|>|<|=)\s*(\d+(?:\.\d+)?)", re.IGNORECASE)


class RuleBasedParser:
    def parse(self, question: str) -> FilterExtractionResult:
        filters: dict[str, FilterCondition] = {}
        filters.update(self._parse_cgpa(question))
        filters.update(self._parse_text_fields(question))
        return FilterExtractionResult(filters=filters)

    def _parse_cgpa(self, question: str) -> dict[str, FilterCondition]:
        match = CGPA_PATTERN.search(question)
        if not match:
            return {}

        operator, value = match.groups()
        numeric_value = float(value)
        condition = FilterCondition()
        if operator == ">":
            condition.gt = numeric_value
        elif operator == "<":
            condition.lt = numeric_value
        elif operator == "=":
            condition.eq = numeric_value
        elif operator == ">=":
            condition.gt = numeric_value - 0.01
        elif operator == "<=":
            condition.lt = numeric_value + 0.01

        return {"cgpa": condition}

    def _parse_text_fields(self, question: str) -> dict[str, FilterCondition]:
        filters: dict[str, FilterCondition] = {}
        for raw_field, raw_value in TEXT_VALUE_PATTERN.findall(question):
            field_name = FIELD_ALIASES[raw_field.casefold()]
            cleaned_value = raw_value.strip().rstrip(".,?")
            if not cleaned_value:
                continue
            if field_name == "name":
                filters[field_name] = FilterCondition(eq=cleaned_value)
            else:
                filters[field_name] = FilterCondition(contains=cleaned_value)
        return filters
