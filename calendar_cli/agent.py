from __future__ import annotations

import os
from typing import List

from langchain.chat_models import init_chat_model
from langsmith import Client  # noqa: F401 (import ensures availability when env is set)
from langgraph.prebuilt import create_react_agent
from langchain_google_community import CalendarToolkit
from langchain_core.tools import BaseTool


def build_calendar_tools() -> List[BaseTool]:
    """Create and return Google Calendar toolkit tools.

    Authentication flow uses local credentials.json and generates token.json on first run.
    Customize by passing a pre-built api_resource if needed.
    """
    toolkit = CalendarToolkit()
    return toolkit.get_tools()


def build_llm() -> any:
    """Initialize the chat model using Google Gemini via LangChain init_chat_model.

    Requires environment variable GOOGLE_API_KEY to be set.
    """
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return init_chat_model(model_name, model_provider="google_genai")


def build_agent_executor():
    # Optional: LangSmith config is picked from env vars if provided
    # LANGSMITH_TRACING, LANGSMITH_API_KEY, LANGSMITH_PROJECT, LANGSMITH_ENDPOINT
    tools = build_calendar_tools()
    llm = build_llm()
    agent_executor = create_react_agent(llm, tools)
    return agent_executor

