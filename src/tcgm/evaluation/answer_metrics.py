"""Answer-level metrics for LongMemEval-V2 and related QA tasks.

This module mirrors the released LongMemEval-V2 evaluator where possible.
Deterministic evaluators are implemented directly. LLM-judge evaluators support
two modes:

- strict mode: require an OpenAI-compatible judge endpoint, matching the public
  benchmark behavior more closely
- heuristic mode: provide a deterministic offline approximation for local
  development before full judge wiring is available
"""

from __future__ import annotations

import inspect
import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any, Callable, Iterable, Optional, Sequence


DEFAULT_SEPARATORS: Sequence[str] = (",", ";")
UNKNOWN_ANSWER = "unknown"

_ABSTENTION_CUES = (
    "there is no",
    "there are no",
    "no ",
    "none",
    "nothing",
    "does not",
    "do not",
    "did not",
    "cannot",
    "can't",
    "not part of",
    "not under",
    "not shown",
    "no extra",
    "no second",
    "no third",
    "only one",
)

_CONTRADICTION_CUES = (
    "instead",
    "rather than",
    "not",
    "does not",
    "do not",
    "cannot",
    "can't",
)

_MULTI_SELECT_FILLER_WORDS = {
    "AND",
    "ANSWER",
    "ANSWERS",
    "CHOICE",
    "CHOICES",
    "FINAL",
    "LETTER",
    "LETTERS",
    "OPTION",
    "OPTIONS",
}


@dataclass(frozen=True)
class AnswerScore:
    question_id: Optional[str]
    eval_name: str
    correct: bool
    exact_match: float
    token_f1: float
    parsed_prediction: str
    reference_answer: str
    used_llm_judge: bool
    used_heuristic_fallback: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_phrase(
    text: str | None,
    *,
    lower: bool = True,
    normalize_hyphen: bool = True,
    strip_punct: bool = True,
) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    if lower:
        text = text.lower()
    if normalize_hyphen:
        text = text.replace("-", " ").replace("_", " ")
    text = re.sub(r"[,;]", " ", text)
    if strip_punct:
        text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_phrases(
    text: str | None,
    *,
    separators: Iterable[str] = DEFAULT_SEPARATORS,
    **normalize_kwargs: bool,
) -> list[str]:
    if text is None:
        return []
    separator_list = list(separators)
    if not separator_list:
        normalized = normalize_phrase(text, **normalize_kwargs)
        return [normalized] if normalized else []
    pattern = "|".join(re.escape(sep) for sep in separator_list)
    parts = re.split(pattern, text)
    normalized_parts = [normalize_phrase(part, **normalize_kwargs) for part in parts]
    return [part for part in normalized_parts if part]


def token_f1_score(prediction: str | None, answer: str | None) -> float:
    pred_tokens = normalize_phrase(prediction).split()
    ans_tokens = normalize_phrase(answer).split()
    if not pred_tokens or not ans_tokens:
        return 0.0
    pred_counts: dict[str, int] = {}
    ans_counts: dict[str, int] = {}
    for token in pred_tokens:
        pred_counts[token] = pred_counts.get(token, 0) + 1
    for token in ans_tokens:
        ans_counts[token] = ans_counts.get(token, 0) + 1
    overlap = 0
    for token, count in pred_counts.items():
        if token in ans_counts:
            overlap += min(count, ans_counts[token])
    if overlap == 0:
        return 0.0
    precision = overlap / len(pred_tokens)
    recall = overlap / len(ans_tokens)
    return 2 * precision * recall / (precision + recall)


def exact_match_score(prediction: str | None, answer: str | None) -> float:
    return float(normalize_phrase(prediction) == normalize_phrase(answer))


def norm_phrase_set_match(
    prediction: str | None,
    answer: str | None,
    *,
    separators: Iterable[str] = DEFAULT_SEPARATORS,
    require_non_empty: bool = True,
    **normalize_kwargs: bool,
) -> bool:
    normalized_pred = normalize_phrase(prediction, **normalize_kwargs)
    answer_phrases = split_phrases(answer, separators=separators, **normalize_kwargs)
    if require_non_empty and (not normalized_pred or not answer_phrases):
        return False
    for phrase in set(answer_phrases):
        pattern = r"\b%s\b" % re.escape(phrase)
        if re.search(pattern, normalized_pred) is None:
            return False
    return True


def norm_phrase_set_match_ordered(
    prediction: str | None,
    answer: str | None,
    *,
    separators: Iterable[str] = DEFAULT_SEPARATORS,
    require_non_empty: bool = True,
    **normalize_kwargs: bool,
) -> bool:
    normalized_pred = normalize_phrase(prediction, **normalize_kwargs)
    answer_phrases = split_phrases(answer, separators=separators, **normalize_kwargs)
    if require_non_empty and (not normalized_pred or not answer_phrases):
        return False
    start = 0
    for phrase in answer_phrases:
        pattern = r"\b%s\b" % re.escape(phrase)
        match = re.search(pattern, normalized_pred[start:])
        if match is None:
            return False
        start += match.end()
    return True


def mc_choice_match(
    prediction: str | None,
    answer: str | None,
    *,
    strip_chars: str = ".",
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    if prediction is None or answer is None:
        return False
    if not isinstance(prediction, str):
        prediction = str(prediction)
    if not isinstance(answer, str):
        answer = str(answer)
    boxed_match = re.search(r"\\boxed\{([^}]*)\}", prediction.lower())
    candidate = boxed_match.group(1) if boxed_match else prediction
    cleaned = re.sub(r"\b(choice|option)\b", "", candidate, flags=re.IGNORECASE)
    for ch in strip_chars:
        cleaned = cleaned.replace(ch, "")
    cleaned = cleaned.strip().upper()
    expected = answer.strip().upper()
    if require_non_empty and (not cleaned or not expected):
        return False
    return cleaned == expected


def _extract_multi_select_letters(text: str | None) -> list[str]:
    if text is None:
        return []
    if not isinstance(text, str):
        text = str(text)
    chunks = re.findall(r"[A-Z]+", text.upper())
    letters: list[str] = []
    for chunk in chunks:
        if chunk in _MULTI_SELECT_FILLER_WORDS:
            continue
        letters.extend(list(chunk))
    return letters


def mc_choice_set_match(
    prediction: str | None,
    answer: str | None,
    *,
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    pred_letters = _extract_multi_select_letters(prediction)
    answer_letters = _extract_multi_select_letters(answer)
    if require_non_empty and (not pred_letters or not answer_letters):
        return False
    return set(pred_letters) == set(answer_letters)


def extract_boxed_answer(text: str) -> str:
    marker = "\\boxed{"
    idx = text.rfind(marker)
    if idx == -1:
        return text.strip()
    i = idx + len(marker)
    depth = 1
    out: list[str] = []
    while i < len(text) and depth > 0:
        ch = text[i]
        if ch == "{":
            depth += 1
            out.append(ch)
        elif ch == "}":
            depth -= 1
            if depth == 0:
                break
            out.append(ch)
        else:
            out.append(ch)
        i += 1
    parsed = "".join(out).strip()
    return parsed if parsed else text.strip()


def is_unknown(parsed_answer: str) -> bool:
    return parsed_answer.strip().lower() == UNKNOWN_ANSWER


def eval_name(eval_spec: str) -> str:
    return eval_spec.split("|", 1)[0].strip()


def _stringify_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _parse_eval_value(key: str, value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"none", "null"}:
        return None
    if key in {"separators", "separator"}:
        if not value:
            return []
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            return json.loads(stripped)
        return [ch for ch in value if not ch.isspace()]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def parse_eval_function_spec(spec: str) -> tuple[Callable[..., Any], dict[str, Any]]:
    if not spec or not isinstance(spec, str):
        raise ValueError("eval function spec must be a non-empty string.")
    parts = [part.strip() for part in spec.split("|")]
    name = parts[0]
    if not name:
        raise ValueError("eval function spec missing function name.")
    func = globals().get(name)
    if func is None or not callable(func):
        raise ValueError(f"Unknown eval function: {name}")
    kwargs: dict[str, Any] = {}
    for part in parts[1:]:
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"Invalid eval function option: {part}")
        key, value = part.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid eval function option: {part}")
        if key in kwargs:
            raise ValueError(f"Duplicate eval function option: {key}")
        kwargs[key] = _parse_eval_value(key, value)
    return func, kwargs


def _is_abstention_like(text: str) -> bool:
    normalized = normalize_phrase(text)
    return any(cue in normalized for cue in _ABSTENTION_CUES)


def _clause_list(text: str) -> list[str]:
    normalized = normalize_phrase(text)
    if not normalized:
        return []
    return [clause.strip() for clause in re.split(r"\b(?:and|or|but|instead|;|,)\b", normalized) if clause.strip()]


def _contains_reference_contradiction(prediction: str, answer: str) -> bool:
    pred = normalize_phrase(prediction)
    ref = normalize_phrase(answer)
    if not pred or not ref:
        return False
    if _is_abstention_like(ref) and not _is_abstention_like(pred):
        return True
    if _is_abstention_like(pred) and not _is_abstention_like(ref):
        return True
    return False


def _heuristic_abstention_match(prediction: str | None, answer: str | None) -> bool:
    pred = _stringify_text(prediction)
    ref = _stringify_text(answer)
    if not pred or not ref:
        return False
    if _contains_reference_contradiction(pred, ref):
        return False
    if normalize_phrase(pred) == normalize_phrase(ref):
        return True
    return _is_abstention_like(pred) and token_f1_score(pred, ref) >= 0.45


def _heuristic_gotchas_match(prediction: str | None, answer: str | None) -> bool:
    pred = _stringify_text(prediction)
    ref = _stringify_text(answer)
    if not pred or not ref:
        return False
    if _contains_reference_contradiction(pred, ref):
        return False
    if normalize_phrase(pred) == normalize_phrase(ref):
        return True
    ref_clauses = _clause_list(ref)
    pred_norm = normalize_phrase(pred)
    for clause in ref_clauses:
        if clause and clause in pred_norm:
            return True
    return token_f1_score(pred, ref) >= 0.55


def llm_abstention_checker(
    prediction: str | None,
    answer: str | None,
    *,
    evaluator_model: str | None = None,
    evaluator_base_url: str | None = None,
    evaluator_api_key: str | None = None,
    evaluator_api_key_env: str = "OPENAI_API_KEY",
    allow_heuristic_fallback: bool = False,
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    prediction_text = _stringify_text(prediction)
    answer_text = _stringify_text(answer)
    if require_non_empty and (not prediction_text or not answer_text):
        return False
    if not evaluator_model:
        if allow_heuristic_fallback:
            return _heuristic_abstention_match(prediction_text, answer_text)
        raise ValueError("llm_abstention_checker requires evaluator_model or allow_heuristic_fallback=True.")
    if evaluator_api_key is None:
        evaluator_api_key = os.getenv(evaluator_api_key_env)
    if evaluator_base_url and not evaluator_api_key:
        evaluator_api_key = "EMPTY"
    if not evaluator_base_url and not evaluator_api_key:
        raise ValueError("llm_abstention_checker requires evaluator_api_key (or set evaluator_api_key_env).")
    # For now, keep strict mode explicit rather than silently diverging.
    raise NotImplementedError("Strict OpenAI judge execution is not wired in this repo yet. Use allow_heuristic_fallback=True for offline development.")


def llm_gotchas_checker(
    prediction: str | None,
    answer: str | None,
    *,
    evaluator_model: str | None = None,
    evaluator_base_url: str | None = None,
    evaluator_api_key: str | None = None,
    evaluator_api_key_env: str = "OPENAI_API_KEY",
    allow_heuristic_fallback: bool = False,
    require_non_empty: bool = True,
    **_: Any,
) -> bool:
    prediction_text = _stringify_text(prediction)
    answer_text = _stringify_text(answer)
    if require_non_empty and (not prediction_text or not answer_text):
        return False
    if not evaluator_model:
        if allow_heuristic_fallback:
            return _heuristic_gotchas_match(prediction_text, answer_text)
        raise ValueError("llm_gotchas_checker requires evaluator_model or allow_heuristic_fallback=True.")
    if evaluator_api_key is None:
        evaluator_api_key = os.getenv(evaluator_api_key_env)
    if evaluator_base_url and not evaluator_api_key:
        evaluator_api_key = "EMPTY"
    if not evaluator_base_url and not evaluator_api_key:
        raise ValueError("llm_gotchas_checker requires evaluator_api_key (or set evaluator_api_key_env).")
    raise NotImplementedError("Strict OpenAI judge execution is not wired in this repo yet. Use allow_heuristic_fallback=True for offline development.")


class LongMemEvalAnswerEvaluator:
    """Evaluate predictions against LongMemEval-V2 question items."""

    def __init__(self, *, allow_heuristic_llm_fallback: bool = True) -> None:
        self.allow_heuristic_llm_fallback = allow_heuristic_llm_fallback

    def evaluate(
        self,
        *,
        question_item: dict[str, Any],
        prediction: str | None,
        model_response: str | None = None,
    ) -> AnswerScore:
        eval_spec = question_item["eval_function"]
        answer = _stringify_text(question_item.get("answer"))
        parsed_prediction = extract_boxed_answer(_stringify_text(prediction or ""))
        parsed_final = parsed_prediction if parsed_prediction else _stringify_text(prediction)
        func, kwargs = parse_eval_function_spec(eval_spec)
        used_heuristic_fallback = False
        used_llm_judge = eval_name(eval_spec).startswith("llm_")
        if used_llm_judge and self.allow_heuristic_llm_fallback:
            kwargs["allow_heuristic_fallback"] = True
            used_heuristic_fallback = True
        if used_llm_judge:
            call_kwargs = {
                "question_item": question_item,
                "parsed_prediction": parsed_final,
                "model_response": model_response,
                **kwargs,
            }
        else:
            call_kwargs = dict(kwargs)
            signature = inspect.signature(func)
            if not any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
                call_kwargs = {
                    key: value
                    for key, value in call_kwargs.items()
                    if key in signature.parameters
                }
        correct = bool(
            func(
                parsed_final,
                answer,
                **call_kwargs,
            )
        )
        return AnswerScore(
            question_id=question_item.get("id"),
            eval_name=eval_name(eval_spec),
            correct=correct,
            exact_match=exact_match_score(parsed_final, answer),
            token_f1=token_f1_score(parsed_final, answer),
            parsed_prediction=parsed_final,
            reference_answer=answer,
            used_llm_judge=used_llm_judge,
            used_heuristic_fallback=used_heuristic_fallback,
        )

    def batch_evaluate(
        self,
        question_items: Iterable[dict[str, Any]],
        predictions: dict[str, str],
    ) -> list[AnswerScore]:
        scores: list[AnswerScore] = []
        for item in question_items:
            question_id = item["id"]
            scores.append(
                self.evaluate(
                    question_item=item,
                    prediction=predictions.get(question_id, ""),
                )
            )
        return scores