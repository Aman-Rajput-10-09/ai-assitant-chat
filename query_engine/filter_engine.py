from models.domain import Student
from models.filters import FilterCondition
from query_engine.semantic_rules import SEMANTIC_CONTAINS_RULES


class QueryEngine:
    def filter_data(
        self,
        data: list[Student],
        filters: dict[str, FilterCondition],
    ) -> list[Student]:
        return [item for item in data if self._matches_all(item, filters)]

    def _matches_all(self, item: Student, filters: dict[str, FilterCondition]) -> bool:
        item_data = item.model_dump()
        for field_name, condition in filters.items():
            value = item_data.get(field_name)
            if value is None or not self._matches_condition(field_name, value, condition):
                return False
        return True

    def _matches_condition(
        self,
        field_name: str,
        value: object,
        condition: FilterCondition,
    ) -> bool:
        if condition.gt is not None and not self._compare_numeric(value, condition.gt, "gt"):
            return False
        if condition.lt is not None and not self._compare_numeric(value, condition.lt, "lt"):
            return False
        if condition.eq is not None and not self._equals(value, condition.eq):
            return False
        if condition.contains is not None and not self._contains(field_name, value, condition.contains):
            return False
        return True

    def _compare_numeric(self, value: object, target: float, operator: str) -> bool:
        if not isinstance(value, (int, float)):
            return False
        if operator == "gt":
            return float(value) > target
        return float(value) < target

    def _equals(self, value: object, target: object) -> bool:
        if isinstance(value, str) and isinstance(target, str):
            return value.casefold() == target.casefold()
        return value == target

    def _contains(self, field_name: str, value: object, target: str) -> bool:
        lookup = target.casefold()
        if isinstance(value, str):
            return lookup in value.casefold()
        if isinstance(value, list):
            values = [str(item).casefold() for item in value]
            if any(lookup in item for item in values):
                return True
            return self._matches_semantic_contains(field_name, values, lookup)
        return False

    def _matches_semantic_contains(
        self,
        field_name: str,
        values: list[str],
        lookup: str,
    ) -> bool:
        aliases = SEMANTIC_CONTAINS_RULES.get(field_name, {}).get(lookup, set())
        if not aliases:
            return False
        return any(alias in value for alias in aliases for value in values)
