from typing import Annotated, ClassVar, Self

from fastapi import Path
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_ID = 2_147_483_647

Id = Annotated[int, Field(ge=1, le=MAX_ID)]
IdPath = Annotated[int, Path(ge=1, le=MAX_ID)]


class PatchModel(BaseModel):

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
