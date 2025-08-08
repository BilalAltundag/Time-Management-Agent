## Time Management Agent CLI (LangChain + Gemini + Google Calendar)

<img width="505" height="418" alt="TimeManagementAgent" src="https://github.com/user-attachments/assets/61f2a0d5-9b51-4bbc-b902-e44b018fb4d8" />

A fast, easy CLI to manage Google Calendar with an opinionated time-management agent. Beautiful output, editable system prompt and user profile, and one-line setup.

### What you can do
- Create / search / update / move / delete events (Google Calendar Toolkit)
- Chat agent with conversation memory (until `exit`) and colored banner
- Editable system prompt (`system_prompt.md`) and user profile (`user_profile.yaml`)
- LangSmith tracing (optional)

### Prerequisites
- Python 3.10+
- Google Cloud Console → OAuth 2.0 Client → Application type: Desktop app (Important)
  - Download `credentials.json` and place it in the repo root
- Gemini API key for `GOOGLE_API_KEY`

### Quick start (Windows PowerShell)
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure API keys into .env (masked in CLI)
python -m calendar_cli.cli configure-google
python -m calendar_cli.cli configure-langsmith  # optional

# First-time helpers (optional)
python -m calendar_cli.cli init-system-prompt   # creates system_prompt.md (editable)
python -m calendar_cli.cli init-profile         # creates user_profile.yaml (editable)

# Verify
python -m calendar_cli.cli env-info

# Use
python -m calendar_cli.cli tools
python -m calendar_cli.cli ask "Yarın 10:00-11:00 derin odak, 14:00 e-posta temizliği, 16:00-17:00 zor görev"
python -m calendar_cli.cli quick-create "Standup" "2025-07-11 10:00" "2025-07-11 10:15" --timezone "Europe/Istanbul" --color-id 2
python -m calendar_cli.cli list-calendars
```

### Timezone behavior
- CLI resolves timezone in this order: `--timezone` arg > `user_profile.yaml` → `CLI_DEFAULT_TIMEZONE` (env, defaults to `Etc/UTC`).

### Customize
- Edit `system_prompt.md`: change the philosophy/rules freely; your life, your rules.
- Edit `user_profile.yaml`: set workdays, working hours, lunch, no-meeting windows, deep-work prefs.
- Colors/fonts: set in `.env` (examples below).

### .env keys (examples)
```bash
GOOGLE_API_KEY=your_gemini_key
GEMINI_MODEL=gemini-2.5-flash
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=your_project
CLI_BANNER_COLOR=bright_blue
CLI_FIGLET_FONT=standard
CLI_DEFAULT_TIMEZONE=Etc/UTC
```

### References
- Google Calendar Toolkit: `https://python.langchain.com/docs/integrations/tools/google_calendar/`
- Google OAuth (Desktop app is required for loopback redirect): `https://developers.google.com/identity/protocols/oauth2/web-server`

### Git hygiene
- Do NOT commit `.env`, `token.json`, or your local venv.
- Recommended `.gitignore` entries:
```
.env
token.json
.venv/
venv/
__pycache__/
```

