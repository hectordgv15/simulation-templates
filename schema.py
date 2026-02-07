from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class TextSource(BaseModel):
    text: str = Field(
        description = "The relevant text from the chunk to extract the result."
    )
    chunk_id: str = Field(
        description = "The unique identifier for the text chunk."
    )
    chunk_document: str = Field(
        description = "The document id from which the text chunk was extracted."
    )
    chunk_page: List[int] = Field(
        description = "The page numbers in the document where the text chunk is located."
    )


class BaseOutputField(BaseModel):
    text_source: List[TextSource] = Field(
        description = "List of text sources contributing to this field."
    )
    justification: str = Field(
        description = "Justification on how the value was extracted from the text sources."
    )
    synonyms_found: List[str] = Field(
        description = "List of synonyms found in the text sources."
    )


class OutputSchemaCritic(BaseModel):
    is_valid: bool = Field(
        description = "Indicates if extracted data is a valid result."
    )
    confidence: float = Field(
        description = "Confidence score about the validity of is_valid flag."
    )
    justification: str = Field(
        description = "Justification for the validity assessment."
    )


class StringField(BaseModel):
    text: str = Field(description = "The string value extracted.", default = "")


class OutputStringField(BaseOutputField):
    result_field: StringField = Field(description = "The StringField extracted.")


class TableField(BaseModel):
    columns: Optional[List[str]] = Field(
        default=None,
        description=(
            "List of column titles EXACTLY as they appear in the table. "
            "Minimum 1 column when provided. Use empty string '' if applicable."
        ),
        min_length=1,  # aplica si columns != None
    )

    rows: Optional[List[List[str]]] = Field(
        default = None,
        description = (
            "2D array with ALL table rows.\n"
            "- Each inner list = 1 row with EXACTLY len(columns) string values\n"
            "- Extract EVERY visible row from the table\n"
            '- Use "" for empty cells\n'
            "- Minimum 1 row unless table is completely empty\n"
            "- Example: [['Apple', '100', 'USD'], ['Google', '200', 'USD']]"
        ),
    )

    @model_validator(mode = "after")
    def validate_table_shape(self):
        if self.columns is None:
            if self.rows not in (None, []):
                raise ValueError("If columns is null, rows must be null or [].")
            return self

        if self.rows is None:
            return self
        
        for i, row in enumerate(self.rows):
            if len(row) != len(self.columns):
                raise ValueError(
                    f"Row {i} has {len(row)} cells but expected {len(self.columns)}."
                )
        return self


class OutputTableField(BaseOutputField):
    result_field: TableField = Field(description = "The table extracted.")


_UNIT_CODE_MAP = {"unit": 1, "pct": 7, "yrs": 8, "x": 9}


class NumericValue(BaseModel):
    value: Optional[float] = Field(
        default = None,
        description = "The numeric value if found."
    )

    unit: int = Field(
        default = 1,
        description = (
            "The unit of the numeric value, as an id, where the unit code map is: "
            f"{_UNIT_CODE_MAP}. If missing or null, it is treated as 1 (unit)."
        ),
    )

    currency: str = Field(
        default = "",
        description = "The currency code if applicable (e.g., USD, EUR). If missing or null, it is treated as empty string.",
    )

    @field_validator("unit", mode="before")
    def unit_none_to_default(cls, v):
        return 1 if v is None else v

    @field_validator("currency", mode = "before")
    def currency_none_to_default(cls, v):
        return "" if v is None else v
    

class OutputNumericField(BaseOutputField):
    result_field: NumericValue = Field(
        description = "The numeric value extracted."
    )