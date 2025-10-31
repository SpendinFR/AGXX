from __future__ import annotations

from typing import Any, Dict, List, Mapping

from AGI_Evolutive.language.understanding import (
    LLMUnderstandingResult,
    SemanticUnderstanding,
)


class _StubLLMManager:
    def __init__(self, responses: List[Mapping[str, Any]]):
        self._responses = list(responses)

    def call_dict(self, spec_key: str, *, input_payload: Any, extra_instructions=None, max_retries: int = 1):
        if not self._responses:
            raise AssertionError(f"Unexpected LLM call for spec '{spec_key}' with payload {input_payload}")
        return self._responses.pop(0)


def test_llm_payload_is_transformed_into_frame():
    stub_response = {
        "intent": "define_term",
        "confidence": 0.92,
        "uncertainty": 0.12,
        "acts": ["INFORM", "CLARIFY"],
        "slots": {
            "definition_candidates": [
                {
                    "term": "polymathie",
                    "description": "Discipline où l'on excelle dans plusieurs domaines",
                }
            ]
        },
        "unknown_terms": ["polymathie"],
        "needs": ["validate_term"],
        "follow_up_questions": ["Veux-tu que je résume chaque discipline ?"],
        "canonical_query": "definition polymathie",
        "tone": "curious",
        "meta": {"confidence_rationale": "pattern: definition"},
    }
    manager = _StubLLMManager([stub_response])
    parser = SemanticUnderstanding(llm_manager=manager)

    frame = parser.parse_utterance("La polymathie est une discipline où l'on excelle dans plusieurs domaines.")

    assert frame.intent == "define_term"
    assert frame.confidence == 0.92
    assert frame.uncertainty == 0.12
    assert frame.slots["definition_candidates"][0]["term"].lower().startswith("polymathie")
    assert frame.meta["canonical_query"] == "definition polymathie"
    assert "follow_up_questions" in frame.meta
    assert parser.state.pending_questions == ["Veux-tu que je résume chaque discipline ?"]


def test_unknown_terms_feed_dialogue_state():
    stub_response = {
        "intent": "ask_info",
        "confidence": 0.78,
        "uncertainty": 0.33,
        "acts": ["ASK"],
        "slots": {},
        "unknown_terms": ["xylotech"],
        "needs": [],
        "follow_up_questions": [],
    }
    manager = _StubLLMManager([stub_response])
    parser = SemanticUnderstanding(llm_manager=manager)

    frame = parser.parse_utterance("Je crois que le Xylotech est un concept étrange 😅")

    assert "xylotech" in frame.unknown_terms
    assert "unknown_terms" in parser.state.user_profile
    assert "xylotech" in parser.state.user_profile["unknown_terms"]


def test_last_result_property_exposes_raw_payload():
    response = {
        "intent": "plan",
        "confidence": 0.81,
        "uncertainty": 0.22,
        "acts": ["REQUEST"],
        "slots": {"objective": "plan stratégique"},
        "meta": {"notes": "plan demandé"},
    }
    parser = SemanticUnderstanding(llm_manager=_StubLLMManager([response]))

    parser.parse_utterance("Plan stratégique Q4")

    assert isinstance(parser.last_result, LLMUnderstandingResult)
    assert parser.last_result.intent == "plan"
    assert parser.last_result.slots["objective"] == "plan stratégique"
