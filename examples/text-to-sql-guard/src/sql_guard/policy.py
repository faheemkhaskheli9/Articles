"""What the LLM-generated SQL is allowed to touch."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Policy:
    """An allow-list. Anything not listed here is refused by the database."""

    # table -> readable columns. "" is the pseudo-column SQLite reports for COUNT(*).
    tables: dict[str, frozenset[str]] = field(default_factory=dict)
    functions: frozenset[str] = frozenset()
    max_rows: int = 200
    # SQLite VM instructions between progress callbacks, and how many callbacks we allow.
    progress_every: int = 1_000
    max_progress_calls: int = 5_000  # about 5 million VM steps


def default_policy() -> Policy:
    """Analytics policy for the sample shop: no PII columns, no salary table."""
    return Policy(
        tables={
            "customers": frozenset({"", "id", "name", "city", "created_at"}),
            "products": frozenset({"", "id", "name", "category", "unit_price_pkr"}),
            "orders": frozenset({"", "id", "customer_id", "status", "total_pkr",
                                 "last_update", "created_at"}),
            "order_items": frozenset({"", "id", "order_id", "product_id", "quantity"}),
        },
        functions=frozenset({
            "count", "sum", "avg", "min", "max", "total", "round", "abs",
            "lower", "upper", "length", "substr", "coalesce", "ifnull", "nullif",
            "date", "strftime", "like", "glob", "cast", "group_concat",
        }),
    )
