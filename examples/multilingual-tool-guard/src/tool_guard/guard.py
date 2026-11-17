"""Deterministic argument guard for LLM tool calls in Sindhi, Urdu, Roman Sindhi/Urdu and English.

The model proposes a call. The guard checks it against the words the user actually typed and
returns one of three actions: execute, confirm (ask the user first) or block.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from tool_guard.normalize import extract_numbers, normalize, tokens

Action = Literal["execute", "confirm", "block"]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    numbers: tuple[str, ...] = ()       # integer args that must appear in the user's text
    identifiers: tuple[str, ...] = ()   # string args that must appear in the user's text
    roles: dict[str, str] = field(default_factory=dict)  # arg -> "source" | "destination"
    writes: bool = False                # changes state -> always ask before executing
    max_value: dict[str, int] = field(default_factory=dict)

    @property
    def args(self) -> set[str]:
        return set(self.numbers) | set(self.identifiers)


TOOLS: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in (
        ToolSpec("account.balance", identifiers=("account_id",)),
        ToolSpec(
            "bank.transfer",
            numbers=("amount_pkr",),
            identifiers=("from_account", "to_account"),
            roles={"from_account": "source", "to_account": "destination"},
            writes=True,
            max_value={"amount_pkr": 1_000_000},
        ),
        ToolSpec("bill.pay", numbers=("amount_pkr",), identifiers=("consumer_id",), writes=True,
                 max_value={"amount_pkr": 500_000}),
        ToolSpec("bus.book", numbers=("seats",), identifiers=("route_id",), writes=True,
                 max_value={"seats": 10}),
    )
}

# Role cues. Urdu/Sindhi use postpositions (after the ID); English uses prepositions (before it).
_SOURCE_AFTER = {"مان", "سے", "maan", "man", "se", "say", "sey", "kha", "khan"}
_DEST_AFTER = {"۾", "ڏانهن", "کي", "میں", "کو", "mein", "me", "main", "ko", "khe", "kho", "dahan", "daanhan"}
_SOURCE_BEFORE = {"from"}
_DEST_BEFORE = {"to", "into"}
_SOURCE_AFTER = {normalize(w) for w in _SOURCE_AFTER}
_DEST_AFTER = {normalize(w) for w in _DEST_AFTER}
_WINDOW = 2  # tokens; allows "A-100 account se" and "from account A-100"


@dataclass(frozen=True)
class GuardConfig:
    """Switches used by the ablation. The default is the full guard."""
    script_digits: bool = True   # read ۱۵۰۰ / ١٥٠٠ as 1500
    number_words: bool = True    # read "panj hazar", "پانچ ہزار", "five thousand"
    roles: bool = True           # check from/to against se/مان/سے/۾/to/from cues


FULL = GuardConfig()


@dataclass
class Issue:
    code: str
    arg: str | None
    detail: str


@dataclass
class Decision:
    action: Action
    issues: list[Issue]
    language: str
    confirmation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "language": self.language,
            "issues": [issue.__dict__ for issue in self.issues],
            "confirmation": self.confirmation,
        }


_SINDHI_ONLY = set("ڪٻٽڏڇڄڃڳڱڻڦٺڀٿڌڊڍڙ۾")
_ROMAN_HINTS = {"mein", "se", "maan", "mokilyo", "bhejo", "karo", "kareen", "rupay", "rupiya", "hazar",
                "munhinji", "mera", "meray", "mere", "ji", "jo", "tasdeeq", "budhayo", "batao", "seat",
                "seatoon", "sitoon", "bhar", "bharo", "khe", "kho", "ka", "kitna", "hai", "par", "ko", "karo"}


def detect_language(text: str) -> str:
    """sd, ur, roman or en. Small heuristic: enough to choose a confirmation template."""
    if any(ch in _SINDHI_ONLY for ch in text):
        return "sd"
    if re.search(r"[؀-ۿ]", text):
        return "ur"
    words = set(re.findall(r"[a-z']+", text.lower()))
    return "roman" if len(words & _ROMAN_HINTS) >= 2 else "en"


def _role_of(value: str, toks: list[str]) -> str | None:
    """Return the role the user's grammar gives an identifier, or None if no cue is present."""
    try:
        i = toks.index(value)
    except ValueError:
        return None
    after = set(toks[i + 1 : i + 1 + _WINDOW])
    before = set(toks[max(0, i - _WINDOW) : i])
    source = bool(after & _SOURCE_AFTER or before & _SOURCE_BEFORE)
    dest = bool(after & _DEST_AFTER or before & _DEST_BEFORE)
    if source == dest:  # none or contradictory cues: do not guess
        return None
    return "source" if source else "destination"


def check_call(
    user_text: str,
    call: dict[str, Any],
    tools: dict[str, ToolSpec] = TOOLS,
    config: GuardConfig = FULL,
) -> Decision:
    """Check one proposed call {"name": ..., "arguments": {...}} against the user's text."""
    lang = detect_language(user_text)
    issues: list[Issue] = []
    spec = tools.get(call.get("name", ""))
    if spec is None:
        return Decision("block", [Issue("unknown_tool", None, str(call.get("name")))], lang)

    args = call.get("arguments") or {}
    for missing in sorted(spec.args - args.keys()):
        issues.append(Issue("missing_argument", missing, "required by the tool"))
    for extra in sorted(args.keys() - spec.args):
        issues.append(Issue("unexpected_argument", extra, "not in the tool schema"))

    numbers = extract_numbers(user_text, config.script_digits, config.number_words)
    for name in spec.numbers:
        if name not in args:
            continue
        value = args[name]
        if type(value) is not int:
            issues.append(Issue("wrong_type", name, f"expected integer, got {type(value).__name__}"))
        elif value <= 0:
            issues.append(Issue("out_of_range", name, f"{value} must be positive"))
        elif value not in numbers:
            issues.append(Issue("ungrounded_number", name,
                                f"{value} not found; user wrote {sorted(numbers) or 'no numbers'}"))
        elif value > spec.max_value.get(name, value):
            issues.append(Issue("out_of_range", name, f"{value} exceeds {spec.max_value[name]}"))

    toks = tokens(user_text)
    for name in spec.identifiers:
        if name not in args:
            continue
        value = normalize(str(args[name]))
        if value not in toks:
            issues.append(Issue("ungrounded_identifier", name, f"{args[name]!r} not in the request"))
            continue
        expected_role = spec.roles.get(name)
        if expected_role and config.roles:
            found = _role_of(value, toks)
            if found is not None and found != expected_role:
                issues.append(Issue("role_mismatch", name, f"user marked {args[name]} as {found}"))

    if issues:
        return Decision("block", issues, lang)
    if spec.writes:
        return Decision("confirm", [], lang, confirmation_message(spec.name, args, lang))
    return Decision("execute", [], lang)


_TEMPLATES = {
    "bank.transfer": {
        "en": "Confirm: send PKR {amount_pkr:,} from {from_account} to {to_account}? Reply yes or no.",
        "roman": "Tasdeeq karein: {from_account} se {to_account} mein {amount_pkr:,} rupay bhejne hain? Haan ya na?",
        "ur": "تصدیق کریں: {from_account} سے {to_account} میں {amount_pkr:,} روپے بھیجنے ہیں؟ ہاں یا نہیں؟",
        "sd": "تصديق ڪريو: {from_account} مان {to_account} ۾ {amount_pkr:,} رپيا موڪلڻا آهن؟ ها يا نه؟",
    },
    "bill.pay": {
        "en": "Confirm: pay PKR {amount_pkr:,} for consumer {consumer_id}? Reply yes or no.",
        "roman": "Tasdeeq karein: consumer {consumer_id} ka {amount_pkr:,} rupay bill bharna hai? Haan ya na?",
        "ur": "تصدیق کریں: صارف {consumer_id} کا {amount_pkr:,} روپے بل ادا کرنا ہے؟ ہاں یا نہیں؟",
        "sd": "تصديق ڪريو: صارف {consumer_id} جو {amount_pkr:,} رپيا بل ڀرڻو آهي؟ ها يا نه؟",
    },
    "bus.book": {
        "en": "Confirm: book {seats} seat(s) on route {route_id}? Reply yes or no.",
        "roman": "Tasdeeq karein: route {route_id} par {seats} seat book karni hai? Haan ya na?",
        "ur": "تصدیق کریں: روٹ {route_id} پر {seats} نشستیں بک کرنی ہیں؟ ہاں یا نہیں؟",
        "sd": "تصديق ڪريو: روٽ {route_id} تي {seats} سيٽون بڪ ڪرڻيون آهن؟ ها يا نه؟",
    },
}


def confirmation_message(tool: str, args: dict[str, Any], lang: str) -> str:
    """Echo the exact arguments back in the user's language, with ASCII digits."""
    return _TEMPLATES[tool][lang].format(**args)
