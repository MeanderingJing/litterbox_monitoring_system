"""Thin wrapper around Anthropic Messages API for DB-ask chat and tool use."""

from anthropic import Anthropic
from anthropic.types import Message


class Claude:
    """Claude API client for chat with optional tools."""

    def __init__(self, model: str):
        self.client = Anthropic()
        self.model = model

    def add_user_message(self, messages: list, message) -> None:
        user_message = {
            "role": "user",
            "content": message.content
            if isinstance(message, Message)
            else message,
        }
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message: Message) -> None:
        assistant_message = {
            "role": "assistant",
            "content": message.content
            if isinstance(message, Message)
            else message,
        }
        messages.append(assistant_message)

    def text_from_message(self, message: Message) -> str:
        return "\n".join(
            [block.text for block in message.content if block.type == "text"]
        )

    def chat(
        self,
        messages: list,
        system: str | None = None,
        temperature: float = 0.0,
        stop_sequences: list[str] | None = None,
        tools: list | None = None,
    ) -> Message:
        params: dict = {
            "model": self.model,
            "max_tokens": 8192,
            "messages": messages,
            "temperature": temperature,
            "stop_sequences": stop_sequences or [],
        }
        if tools:
            params["tools"] = tools
        if system:
            params["system"] = system
        return self.client.messages.create(**params)
