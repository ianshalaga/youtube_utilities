"""Domain validation types for the YouTube album workflow.

This module contains domain-level validation results and errors.
It does not perform infrastructure operations or modify remote state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationError:
    """Represents a single domain validation error."""

    field: str
    message: str


class ValidationResult:
    """Represents the result of validating a domain object."""

    def __init__(self, errors: list[ValidationError] | None = None) -> None:
        self._errors = list(errors) if errors is not None else []

    @property
    def is_valid(self) -> bool:
        """Return whether the validation completed without errors."""
        return not self._errors

    @property
    def errors(self) -> tuple[ValidationError, ...]:
        """Return the validation errors."""
        return tuple(self._errors)

    def add_error(self, field: str, message: str) -> None:
        """Add a validation error to the result."""
        self._errors.append(
            ValidationError(
                field=field,
                message=message,
            )
        )