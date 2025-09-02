import asyncio
from typing import Any, Dict

from langgraph.checkpoint.memory import InMemorySaver
from openai import OpenAI

from config import get_settings

settings = get_settings()
from services import checkpoint_service


class ConversationCheckpointer(InMemorySaver):
    """In-memory checkpointer that persists to Postgres and summarizes history."""

    def __init__(self, k: int = 5) -> None:
        super().__init__()
        self.k = k
        self._client: OpenAI | None = None

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=settings.LLM_API_KEY)
        return self._client

    def _summarize(self, summary: str, messages: list[Dict[str, Any]]) -> str:
        if not messages:
            return summary
        parts = []
        if summary:
            parts.append(f"Existing summary:\n{summary}")
        formatted = []
        for m in messages:
            content = m.get("content", {})
            if isinstance(content, dict):
                text = content.get("text") or content.get("response") or str(content)
            else:
                text = str(content)
            formatted.append(f"{m['role']}: {text}")
        parts.append("New messages:\n" + "\n".join(formatted))
        prompt = "\n\n".join(parts)
        try:
            resp = self.client.responses.create(
                model=settings.LLM_RESPONSE_MODEL,
                input=(
                    "Update the conversation summary to reflect the entire conversation so far.\n"
                    + prompt
                ),
            )
            return resp.output[0].content[0].text.strip()
        except Exception:
            return summary

    def _load_from_db(self, conversation_id: str) -> Dict[str, Any] | None:
        try:
            return asyncio.run(checkpoint_service.get_checkpoint(conversation_id))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                checkpoint_service.get_checkpoint(conversation_id)
            )

    def _save_to_db(self, conversation_id: str, data: Dict[str, Any]) -> None:
        try:
            asyncio.run(checkpoint_service.upsert_checkpoint(conversation_id, data))
        except RuntimeError:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(
                checkpoint_service.upsert_checkpoint(conversation_id, data)
            )

    def load(self, conversation_id: str) -> Dict[str, Any]:
        """Load memory for a conversation."""
        config = {
            "configurable": {"thread_id": conversation_id, "checkpoint_ns": "memory"}
        }
        checkpoint = super().get(config)
        if checkpoint is None:
            data = self._load_from_db(conversation_id) or {}
            history = data.get("history", {"summary": "", "messages": []})
            cp = {
                "id": "history",
                "channel_values": {"history": history},
            }
            super().put(
                config,
                cp,
                {},
                {"history": self.get_next_version(None, None)},
            )
            return history
        return checkpoint.get("history", {"summary": "", "messages": []})

    def save(self, conversation_id: str, history: Dict[str, Any]) -> None:
        messages = history.get("messages", [])
        summary = history.get("summary", "")
        if len(messages) > self.k:
            old = messages[:-self.k]
            messages = messages[-self.k:]
            summary = self._summarize(summary, old)
        new_history = {"summary": summary, "messages": messages}
        config = {
            "configurable": {"thread_id": conversation_id, "checkpoint_ns": "memory"}
        }
        cp = {"id": "history", "channel_values": {"history": new_history}}
        super().put(
            config,
            cp,
            {},
            {"history": self.get_next_version(None, None)},
        )
        self._save_to_db(conversation_id, {"history": new_history})
