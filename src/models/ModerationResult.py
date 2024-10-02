from pydantic import BaseModel, Field, field_validator


class ModerationResult(BaseModel):
    """Represents the result of a moderation API call."""
    flagged: bool
    categories: dict[str, bool] = Field(default_factory=dict)
    category_scores: dict[str, float] = Field(default_factory=dict)

    @field_validator('categories', mode='before')
    def replace_none_in_categories(cls, value):
        """
        Replace any None values in the 'categories' dictionary with False.
        """
        if not isinstance(value, dict):
            raise TypeError("categories must be a dictionary")
        return {k: (v if v is not None else False) for k, v in value.items()}

    @field_validator('category_scores', mode='before')
    def replace_none_in_category_scores(cls, value):
        """
        Replace any None values in the 'category_scores' dictionary with 0.0.
        """
        if not isinstance(value, dict):
            raise TypeError("category_scores must be a dictionary")
        return {k: (v if v is not None else 0.0) for k, v in value.items()}
