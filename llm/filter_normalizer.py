from models.filters import FilterCondition, FilterExtractionResult


LIST_FIELDS = {"skills", "activities", "projects"}


class FilterNormalizer:
    def normalize(
        self,
        llm_filters: FilterExtractionResult,
        rule_filters: FilterExtractionResult,
    ) -> FilterExtractionResult:
        merged_filters = {
            field_name: condition.model_copy(deep=True)
            for field_name, condition in llm_filters.filters.items()
        }

        for field_name, condition in rule_filters.filters.items():
            merged_filters[field_name] = condition.model_copy(deep=True)

        normalized_filters = {
            field_name: self._normalize_condition(field_name, condition)
            for field_name, condition in merged_filters.items()
            if self._has_operator(condition)
        }
        return FilterExtractionResult(filters=normalized_filters)

    def _normalize_condition(
        self,
        field_name: str,
        condition: FilterCondition,
    ) -> FilterCondition:
        normalized = condition.model_copy(deep=True)

        if field_name in LIST_FIELDS and isinstance(normalized.eq, str):
            normalized.contains = normalized.eq
            normalized.eq = None

        if isinstance(normalized.contains, str):
            normalized.contains = normalized.contains.strip()

        if isinstance(normalized.eq, str):
            normalized.eq = normalized.eq.strip()

        return normalized

    def _has_operator(self, condition: FilterCondition) -> bool:
        return any(
            value is not None
            for value in (condition.gt, condition.lt, condition.eq, condition.contains)
        )
