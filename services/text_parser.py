"""Deterministic rule-based parsing of free-text symptom descriptions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from knowledge_base.schema import KnowledgeBase

MAX_TEXT_LENGTH = 1000
FUZZY_THRESHOLD = 0.90
_NEGATION = re.compile(
    r"(?:^|\s)(?:no|not|without|denies|deny|denied|never\s+had)"
    r"(?:\s+\w+){0,4}\s*$"
)
_DURATION = re.compile(
    r"\b(?P<amount>\d+|a|an|one|two|three)\s+"
    r"(?P<unit>day|days|week|weeks|month|months|year|years)\b"
)
_SINCE_YESTERDAY = re.compile(r"\bsince yesterday\b")
_SINCE_LAST_NIGHT = re.compile(r"\bsince last night\b")
_SEVERITY_PHRASES = {
    "very bad": 9,
    "really bad": 9,
    "severe": 8,
    "bad": 7,
    "moderate": 5,
    "mild": 2,
}
_NUMBER_WORDS = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
}
_FILLER = re.compile(
    r"\b(?:i|we|you|he|she|they|have|has|had|been|am|are|was|were|"
    r"feel|feeling|felt|with|my|a|an|the|of|for|and|but|then|also|"
    r"no|not|without|denies|deny|denied|never|since|yesterday|last|"
    r"mild|moderate|severe|bad|very|really|day|days|week|weeks|"
    r"month|months|year|years)\b",
    re.IGNORECASE,
)


@dataclass
class ParseResult:
    """Matched symptoms and non-fatal parser notes."""

    symptoms: list[dict[str, str | int | bool | None]] = field(default_factory=list)
    unrecognized_phrases: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _Mention:
    start: int
    end: int
    symptom_id: str


def _normalize(text: str) -> str:
    """Lowercase text, remove punctuation, and collapse whitespace."""
    normalized = text.casefold()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    return re.sub(r"\s+", " ", normalized).strip()


def _aliases(kb: KnowledgeBase) -> list[tuple[str, str]]:
    aliases: list[tuple[str, str]] = []
    for symptom in kb.symptoms:
        terms = [symptom.id.replace("_", " "), symptom.display_name]
        terms.extend(symptom.synonyms or [])
        for term in terms:
            normalized = _normalize(term)
            if normalized:
                aliases.append((normalized, symptom.id))
    return sorted(set(aliases), key=lambda item: (-len(item[0]), item[0], item[1]))


def _overlaps(start: int, end: int, spans: list[tuple[int, int]]) -> bool:
    return any(start < other_end and end > other_start for other_start, other_end in spans)


def _find_exact_matches(
    text: str,
    aliases: list[tuple[str, str]],
) -> list[_Mention]:
    found: list[_Mention] = []
    occupied: list[tuple[int, int]] = []
    for phrase, symptom_id in aliases:
        pattern = re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)")
        for match in pattern.finditer(text):
            if not _overlaps(match.start(), match.end(), occupied):
                found.append(_Mention(match.start(), match.end(), symptom_id))
                occupied.append((match.start(), match.end()))
    return sorted(found, key=lambda mention: (mention.start, mention.end, mention.symptom_id))


def _find_fuzzy_matches(
    text: str,
    aliases: list[tuple[str, str]],
    exact_matches: list[_Mention],
) -> list[_Mention]:
    exact_spans = [(mention.start, mention.end) for mention in exact_matches]
    tokens = list(re.finditer(r"\S+", text))
    aliases_by_word_count: dict[int, list[tuple[str, str]]] = {}
    for phrase, symptom_id in aliases:
        if len(phrase) < 5:
            continue
        aliases_by_word_count.setdefault(len(phrase.split()), []).append((phrase, symptom_id))

    fuzzy: list[_Mention] = []
    for word_count, candidates in aliases_by_word_count.items():
        for index in range(len(tokens) - word_count + 1):
            window = tokens[index : index + word_count]
            start, end = window[0].start(), window[-1].end()
            if _overlaps(start, end, exact_spans):
                continue
            candidate_text = text[start:end]
            scored = sorted(
                (
                    SequenceMatcher(None, candidate_text, phrase).ratio(),
                    symptom_id,
                )
                for phrase, symptom_id in candidates
            )
            if not scored:
                continue
            best_score = scored[-1][0]
            best_ids = {symptom_id for score, symptom_id in scored if score == best_score}
            if best_score >= FUZZY_THRESHOLD and len(best_ids) == 1:
                fuzzy.append(_Mention(start, end, next(iter(best_ids))))

    combined = exact_matches + fuzzy
    selected: list[_Mention] = []
    used_ids: set[str] = set()
    occupied: list[tuple[int, int]] = []
    for mention in sorted(
        combined,
        key=lambda item: (item.start, item.end - item.start, item.symptom_id),
    ):
        if mention.symptom_id not in used_ids and not _overlaps(
            mention.start, mention.end, occupied
        ):
            selected.append(mention)
            occupied.append((mention.start, mention.end))
            used_ids.add(mention.symptom_id)
    return sorted(selected, key=lambda mention: mention.start)


def _is_negated(text: str, start: int) -> bool:
    preceding = text[max(0, start - 60) : start].split()
    for boundary in ("and", "but", "then"):
        if boundary in preceding:
            preceding = preceding[preceding.index(boundary) + 1 :]
    nearby = preceding[-5:]
    return bool(_NEGATION.search(" ".join(nearby)))


def _duration_days(unit: str, amount_text: str) -> int:
    amount = _NUMBER_WORDS.get(amount_text, int(amount_text) if amount_text.isdigit() else 1)
    multiplier = {
        "day": 1,
        "days": 1,
        "week": 7,
        "weeks": 7,
        "month": 30,
        "months": 30,
        "year": 365,
        "years": 365,
    }[unit]
    return min(3650, amount * multiplier)


def _attach_nearest(
    matches: list[_Mention],
    spans: list[tuple[int, int, int]],
    target: dict[str, int | None],
) -> set[tuple[int, int]]:
    consumed: set[tuple[int, int]] = set()
    for start, end, value in spans:
        if not matches:
            continue
        nearest = min(
            matches,
            key=lambda mention: (
                max(mention.start - end, start - mention.end, 0),
                mention.start,
            ),
        )
        distance = max(nearest.start - end, start - nearest.end, 0)
        if distance <= 80:
            target[nearest.symptom_id] = value
            consumed.add((start, end))
    return consumed


def _unrecognized(
    text: str,
    mentions: list[_Mention],
    consumed_spans: set[tuple[int, int]],
) -> list[str]:
    characters = list(text)
    spans = [(mention.start, mention.end) for mention in mentions] + list(consumed_spans)
    for start, end in spans:
        characters[start:end] = " " * (end - start)
    remainder = "".join(characters)
    phrases: list[str] = []
    for piece in re.split(r"\b(?:and|but|then|also)\b", remainder):
        cleaned = _FILLER.sub(" ", piece)
        cleaned = re.sub(r"\b\d+\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if len(cleaned) >= 3 and cleaned not in phrases:
            phrases.append(cleaned)
    return phrases


def parse_symptom_text(text: object, kb: KnowledgeBase) -> ParseResult:
    """Parse free text into safety-layer-compatible symptom records."""
    if not isinstance(text, str):
        return ParseResult(warnings=["Symptom description must be text."])
    if not text.strip():
        return ParseResult(warnings=["No symptom text was provided."])

    warnings: list[str] = []
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
        warnings.append(
            f"Description was limited to the first {MAX_TEXT_LENGTH} characters."
        )
    normalized = _normalize(text)
    if not normalized:
        return ParseResult(warnings=warnings + ["No readable symptom text was found."])

    aliases = _aliases(kb)
    exact = _find_exact_matches(normalized, aliases)
    mentions = _find_fuzzy_matches(normalized, aliases, exact)
    if not mentions:
        return ParseResult(
            unrecognized_phrases=_unrecognized(normalized, [], set()),
            warnings=warnings,
        )

    durations: list[tuple[int, int, int]] = []
    consumed: set[tuple[int, int]] = set()
    for match in _DURATION.finditer(normalized):
        days = _duration_days(match.group("unit"), match.group("amount"))
        raw_amount = match.group("amount")
        if raw_amount.isdigit() and int(raw_amount) * {
            "day": 1, "days": 1, "week": 7, "weeks": 7,
            "month": 30, "months": 30, "year": 365, "years": 365,
        }[match.group("unit")] > 3650:
            warnings.append("A duration exceeded 3650 days and was capped.")
        durations.append((match.start(), match.end(), days))
    for duration_match in (_SINCE_YESTERDAY, _SINCE_LAST_NIGHT):
        for match in duration_match.finditer(normalized):
            durations.append((match.start(), match.end(), 1))
    severity_spans: list[tuple[int, int, int]] = []
    occupied_severity_spans: list[tuple[int, int]] = []
    for phrase, value in sorted(
        _SEVERITY_PHRASES.items(), key=lambda item: -len(item[0])
    ):
        for match in re.finditer(rf"\b{re.escape(phrase)}\b", normalized):
            if not _overlaps(
                match.start(),
                match.end(),
                occupied_severity_spans,
            ):
                severity_spans.append((match.start(), match.end(), value))
                occupied_severity_spans.append((match.start(), match.end()))

    attached_durations: dict[str, int | None] = {}
    attached_severities: dict[str, int | None] = {}
    consumed.update(_attach_nearest(mentions, durations, attached_durations))
    consumed.update(_attach_nearest(mentions, severity_spans, attached_severities))

    result_symptoms = [
        {
            "symptom_id": mention.symptom_id,
            "present": not _is_negated(normalized, mention.start),
            "severity": attached_severities.get(mention.symptom_id),
            "duration_days": attached_durations.get(mention.symptom_id),
        }
        for mention in mentions
    ]
    return ParseResult(
        symptoms=result_symptoms,
        unrecognized_phrases=_unrecognized(normalized, mentions, consumed),
        warnings=warnings,
    )
