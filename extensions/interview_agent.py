"""
Future: Conversational Interview Agent

Replace (or wrap) ui/interview_form.py with an LLM-driven dialogue that
asks clarifying questions and fills WitnessProfile fields automatically.

Suggested interface:
    class InterviewAgent:
        def start_session(self) -> str: ...
        def respond(self, user_message: str) -> tuple[str, dict]: ...
        def to_profile(self) -> WitnessProfile: ...
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from utils.profile import WitnessProfile


class InterviewAgent:
    """Stub — not implemented in the 50% MVP."""

    def start_session(self) -> str:
        raise NotImplementedError("Interview agent is a post-MVP extension.")

    def respond(self, user_message: str) -> tuple[str, dict]:
        raise NotImplementedError("Interview agent is a post-MVP extension.")

    def to_profile(self) -> "WitnessProfile":
        raise NotImplementedError("Interview agent is a post-MVP extension.")
