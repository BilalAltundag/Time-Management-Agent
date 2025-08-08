from __future__ import annotations

import os
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


DEFAULT_PROFILE_ENV_KEY = "CALENDAR_CLI_PROFILE"
DEFAULT_PROFILE_PATH = "user_profile.yaml"


class UserProfile(BaseModel):
    timezone: Optional[str] = Field(
        default=None, description="IANA timezone, e.g., Europe/Istanbul"
    )
    workdays: Optional[List[str]] = Field(
        default=None, description="List of active work days, e.g., ['mon','tue','wed','thu','fri']"
    )
    working_hours: Optional[Dict[str, str]] = Field(
        default=None, description="Per-day working window, e.g., {'mon': '09:00-18:00'}"
    )
    lunch: Optional[str] = Field(
        default=None, description="Lunch break window, e.g., '12:30-13:30'"
    )
    no_meetings: Optional[List[str]] = Field(
        default=None, description="List of time windows to avoid meetings, e.g., ['Fri 14:00-16:00']"
    )
    preferred_deep_work: Optional[List[str]] = Field(
        default=None, description="Preferred deep work windows, e.g., ['09:00-11:00','16:00-18:00']"
    )
    avoid_times: Optional[List[str]] = Field(
        default=None, description="General avoid windows, e.g., ['18:00-21:00']"
    )
    notes: Optional[str] = Field(default=None, description="Free-form notes")


PROFILE_TEMPLATE = """
# User profile for Calendar CLI
#
# Rename or relocate via CALENDAR_CLI_PROFILE env var, or pass --path argument on commands.
# Comments start with '#'. Keep times in 24h 'HH:MM-HH:MM' format.

timezone: Europe/Istanbul
workdays: [mon, tue, wed, thu, fri]
working_hours:
  mon: "09:00-18:00"
  tue: "09:00-18:00"
  wed: "09:00-18:00"
  thu: "09:00-18:00"
  fri: "09:00-18:00"
lunch: "12:30-13:30"
no_meetings: ["Fri 14:00-16:00"]
preferred_deep_work: ["09:00-11:00", "16:00-18:00"]
avoid_times: ["18:00-21:00"]
notes: "Personal preferences: avoid late-night heavy tasks."
"""


def get_default_profile_path() -> str:
    return os.getenv(DEFAULT_PROFILE_ENV_KEY, DEFAULT_PROFILE_PATH)


def write_default_profile_template(path: Optional[str] = None) -> str:
    """Write a starter YAML profile if it doesn't exist. Returns the path written."""
    target_path = path or get_default_profile_path()
    if os.path.exists(target_path):
        return target_path
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(PROFILE_TEMPLATE.strip() + "\n")
    return target_path


def load_user_profile(path: Optional[str] = None) -> Optional[UserProfile]:
    """Load user profile from YAML if present; return None if missing or invalid."""
    target_path = path or get_default_profile_path()
    if not os.path.exists(target_path):
        return None
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return UserProfile.model_validate(data)
    except Exception:
        return None


def summarize_profile_for_system(profile: UserProfile) -> str:
    """Create a short, LLM-friendly summary of profile constraints/preferences."""
    lines: List[str] = ["Kullanıcı Profili:"]
    if profile.timezone:
        lines.append(f"- Zaman dilimi: {profile.timezone}")
    if profile.workdays:
        days = ", ".join(profile.workdays)
        lines.append(f"- Çalışma günleri: {days}")
    if profile.working_hours:
        parts = [f"{d}: {w}" for d, w in profile.working_hours.items()]
        lines.append("- Çalışma saatleri: " + "; ".join(parts))
    if profile.lunch:
        lines.append(f"- Öğle arası: {profile.lunch}")
    if profile.no_meetings:
        lines.append("- Toplantı kaçınma: " + "; ".join(profile.no_meetings))
    if profile.preferred_deep_work:
        lines.append("- Derin odak tercihleri: " + "; ".join(profile.preferred_deep_work))
    if profile.avoid_times:
        lines.append("- Kaçınılacak saatler: " + "; ".join(profile.avoid_times))
    return "\n".join(lines)

