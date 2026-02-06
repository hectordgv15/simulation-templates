from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TextSource(BaseModel):
    text: str = Field(
        description="The relevant text from the chunk to extract the result."
    )
    chunk_id: str = Field(
        description="The unique identifier for the text chunk."
    )
    chunk_document: str = Field(
        description="The document id from which the text chunk was extracted."
    )
    chunk_page: List[int] = Field(
        description="The page numbers in the document where the text chunk is located."
    )


class BaseOutputField(BaseModel):
    text_source: List[TextSource] = Field(
        description="List of text sources contributing to this field."
    )
    justification: str = Field(
        description="Justification on how the value was extracted from the text sources."
    )
    synonyms_found: List[str] = Field(
        description="List of synonyms found in the text sources."
    )


class OutputSchemaCritic(BaseModel):
    is_valid: bool = Field(
        description="Indicates if extracted data is a valid result."
    )
    confidence: float = Field(
        description="Confidence score about the validity of is_valid flag."
    )
    justification: str = Field(
        description="Justification for the validity assessment."
    )


UNIT_CODE_MAP = {"unit": 1, "pbs": 6, "%": 7}
MAX_TEXT_LENGTH = 1000


class StringField(BaseModel):
    text: str = Field(description="The string value extracted.")
    summary: str = Field(
        description="A concise summary of the text.",
        max_length=MAX_TEXT_LENGTH,
    )

    @field_validator("summary", mode="before")
    def set_summary(cls, v, values):
        text = values.data.get("text", "")
        if len(text) > 1000:
            return v
        return ""


class OutputStringField(BaseOutputField):
    result_field: StringField = Field(
        description="The StringField extracted."
    )


class TableField(BaseModel):
    columns: List[str] = Field(
        description="""List of column titles EXACTLY as they appear in the table.
        Minimum 1 column. Use empty string '' if applicable.""",
        min_length=1,
    )
    rows: List[List[str]] = Field(
        description="""2D array with ALL table rows.
        - Each inner list = 1 row with EXACTLY len(columns) string values
        - Extract EVERY visible row from the table
        - Use "" for empty cells
        - Minimum 1 row unless table is completely empty
        - Example: [['Apple', '100', 'USD'], ['Google', '200', 'USD']]""",
        min_length=1,
    )


class OutputTableField(BaseOutputField):
    result_field: TableField = Field(
        description="The table extracted."
    )


class NumericValue(BaseModel):
    field: Optional[str] = Field(
        description="The name of the numeric field. Can be none or empty",
        default=""
    )
    value: float = Field(
        description="The numeric value."
    )
    unit: int = Field(
        description=f"""The unit of the numeric value, as an id, where the unit code map is: {UNIT_CODE_MAP}. If no unit, use 1 (unit)."""
    )
    currency: str = Field(
        description="The currency code if applicable, e.g., USD, EUR."
    )


class NumericArrayValue(BaseOutputField):
    values: List[NumericValue] = Field(
        description="List of numeric values."
    )


class OutputNumericArrayField(BaseOutputField):
    result_field: NumericArrayValue = Field(
        description="The numeric array value extracted."
    )


class OutputNumericField(BaseOutputField):
    result_field: NumericValue = Field(
        description="The numeric value extracted."
    )


class CompositeNumericField(BaseOutputField):
    result_field: List[NumericValue] = Field(
        "List of numeric components that make up the composite value."
    )


CONFIDENCE_STR = "Confidence score for the alternative extraction."


class AlternativeExtractionStringField(BaseOutputField):
    result_field: StringField = Field(
        description="The alternative string value extracted."
    )
    confidence: float = Field(
        description="Confidence score for the alternative extraction."
    )


class AlternativeExtractionNumericField(BaseOutputField):
    result_field: NumericValue = Field(
        description="The alternative numeric value extracted."
    )
    confidence: float = Field(description=CONFIDENCE_STR)


class AlternativeExtractionTableField(BaseOutputField):
    result_field: TableField = Field(
        description="The alternative table value extracted."
    )
    confidence: float = Field(description=CONFIDENCE_STR)


class AlternativeExtractionCompositeNumericField(BaseOutputField):
    result_field: List[NumericValue] = Field(
        "List of numeric components that make up the composite value."
    )
    confidence: float = Field(description=CONFIDENCE_STR)
