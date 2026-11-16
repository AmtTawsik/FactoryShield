from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, model_validator


class PatchModel(BaseModel):
    """Base for PATCH bodies: omitted fields stay unchanged, and null is only accepted for nullable columns."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> Self:
        for field in self.model_fields_set - self.nullable_fields:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self

    def changes(self) -> dict:
        return self.model_dump(exclude_unset=True)
