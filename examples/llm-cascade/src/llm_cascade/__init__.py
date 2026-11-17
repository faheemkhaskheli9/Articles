"""Rules first, local model second, paid model last, with checks before every escalation."""
from .cascade import Cascade, Outcome
from .schema import FIELDS, FieldResult

__all__ = ["Cascade", "Outcome", "FIELDS", "FieldResult"]
