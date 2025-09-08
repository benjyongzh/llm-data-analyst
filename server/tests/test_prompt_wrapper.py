import pathlib
import sys
import types

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

schemas_stub = types.ModuleType("schemas")


class _StubLLMResponse:
    @classmethod
    def model_json_schema(cls):
        return {"title": "LLMResponse", "type": "object", "properties": {"response": {}}}


schemas_stub.LLMResponse = _StubLLMResponse
sys.modules.setdefault("schemas", schemas_stub)

import services.prompt_wrapper as pw


def test_wrap_prompt_adds_prefix_and_suffix():
    prompt = "Hello"
    wrapped = pw.wrap_prompt(prompt)
    expected = f"{pw.PROMPT_PREFIX.strip()}\n{prompt}\n{pw.PROMPT_SUFFIX.strip()}"
    assert wrapped == expected


def test_prompt_prefix_mentions_json_requirements():
    assert "100% requirement" in pw.PROMPT_PREFIX
    assert "response" in pw.PROMPT_PREFIX
    assert "place that JSON inside the `response` field" in pw.PROMPT_PREFIX


def test_prompt_suffix_requires_only_json():
    assert "nothing else" in pw.PROMPT_SUFFIX
