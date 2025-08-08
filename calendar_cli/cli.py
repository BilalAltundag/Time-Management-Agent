from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import box
from rich.text import Text
from dotenv import load_dotenv, set_key, find_dotenv
from pyfiglet import Figlet, FigletFont

from .agent import build_agent_executor, build_calendar_tools
from .profile import (
    write_default_profile_template,
    load_user_profile,
    summarize_profile_for_system,
    get_default_profile_path,
)
from .system_prompt import (
    write_default_system_prompt_template,
    load_system_prompt,
)


app = typer.Typer(help="LangChain + Gemini Google Calendar CLI")
console = Console()

# Load .env early
load_dotenv()


def require_google_api_key():
    if not os.getenv("GOOGLE_API_KEY"):
        console.print("[bold red]GOOGLE_API_KEY not set.[/bold red]")
        console.print("Set it in your environment or in a .env file.")
        raise typer.Exit(1)


@app.command(name="env-info")
def env_info():
    """Show environment variables used by the CLI."""
    table = Table(title="Environment", box=box.SIMPLE_HEAVY)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_row("GOOGLE_API_KEY", "SET" if os.getenv("GOOGLE_API_KEY") else "-")
    table.add_row("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    table.add_row("LANGSMITH_TRACING", os.getenv("LANGSMITH_TRACING", "-"))
    table.add_row("LANGSMITH_ENDPOINT", os.getenv("LANGSMITH_ENDPOINT", "-"))
    table.add_row("LANGSMITH_PROJECT", os.getenv("LANGSMITH_PROJECT", "-"))
    table.add_row("LANGSMITH_API_KEY", "SET" if os.getenv("LANGSMITH_API_KEY") else "-")
    table.add_row("CLI_BANNER_COLOR", os.getenv("CLI_BANNER_COLOR", "bright_blue"))
    table.add_row("CLI_FIGLET_FONT", os.getenv("CLI_FIGLET_FONT", "standard"))
    table.add_row("CLI_DEFAULT_TIMEZONE", os.getenv("CLI_DEFAULT_TIMEZONE", "Etc/UTC"))
    console.print(table)


@app.command()
def tools():
    """List available Google Calendar tools."""
    require_google_api_key()
    toolkit_tools = build_calendar_tools()
    table = Table(title="Calendar Tools", box=box.ROUNDED)
    table.add_column("#")
    table.add_column("Name", style="bold")
    for idx, tool in enumerate(toolkit_tools, 1):
        table.add_row(str(idx), tool.name)
    console.print(table)


@app.command()
def ask(prompt: Optional[str] = typer.Argument(None, help="Start the conversation with this message")):
    """Chat with the agent to execute calendar actions."""
    require_google_api_key()

    # Fancy banner similar to ASCII art intro
    try:
        banner_color = os.getenv("CLI_BANNER_COLOR", "bright_blue")
        fig = Figlet(font=os.getenv("CLI_FIGLET_FONT", "standard"))
        # Split into two blocks to better fit terminal widths
        banner = fig.renderText("Time Management") + "\n" + fig.renderText("Agent")
        renderable = Text(banner, style=f"bold {banner_color}")
        console.print(Panel.fit(renderable, title=f"[bold {banner_color}]Welcome", border_style=banner_color))
    except Exception:
        console.print(Panel.fit("Time Management Agent", title="Welcome", border_style="bright_blue"))
    agent = build_agent_executor()

    if not prompt:
        prompt = Prompt.ask("You", default="Create a green event for tomorrow 10:00-10:30 named Standup")

    # Build a system prompt that sets role, current datetime context, and optional user profile
    # Prefer profile timezone if provided for display/context
    profile_tz_name = None
    user_profile = load_user_profile()
    if user_profile:
        profile_tz_name = user_profile.timezone or None
    try:
        now_local = (
            datetime.now(ZoneInfo(profile_tz_name)) if profile_tz_name else datetime.now().astimezone()
        )
    except Exception:
        now_local = datetime.now().astimezone()
    now_utc = datetime.now(timezone.utc)

    profile_note = ""
    if user_profile:
        profile_note = "\n\n" + summarize_profile_for_system(user_profile)
    # Prefer external system prompt if present
    external_prompt = load_system_prompt()
    system_instructions = (
        "Rol: Sen, insan biyolojisi, sirkadiyen ritim, nörobilim, ergonomi ve üretkenlik konularında uzman "
        "bir Zaman Yönetimi Danışmanı ve takvim ajanısın. Amaç: Kullanıcının talebini en kısa ve net şekilde "
        "yanıtlamak ve gerektiğinde takvim üzerinde güvenli işlemler yapmak (oluştur/ara/güncelle/taşı/sil). "
        "Çakışmaları ve kısıtları kontrol et; izinsiz/yıkıcı değişiklik yapma.\n\n"
        "Varsayılan iletişim tarzı: Soruyu doğrudan yanıtla; gereksiz tavsiye ve uzun açıklamalardan kaçın. "
        "Yanıt sonunda yalnızca şu soruyu sor: 'Öneri ve kısa bilimsel açıklama eklememi ister misiniz? (E/H)'. "
        "Kullanıcı 'E' derse kısaca öneriler + kısa gerekçe ekle; 'H' derse ekleme.\n\n"
        "Planlama ilkeleri (iç kurallar):\n"
        "- Biyolojik saat: 09:00–11:00 ve 16:00–18:00 zihinsel zirve; ~14:00 ve geç saatlerde odak azalır.\n"
        "- Zaman yönetiminin 3 boyutu: Planlama (önemli işleri zirve saatlere koy), Tutum (zaman sınırlı; erteleme), "
        "Tuzaklar (gereksiz toplantı/habersiz ziyaret/sosyal medya; gerektiğinde 'hayır' de).\n"
        "- Mola ve sağlık: 20-20-20 göz kuralı; 60–90 dk’da bir 5–10 dk aktif mola; postür değişikliği/esneme.\n"
        "- Süreç: Günlük zaman kütüğü ile analiz → önem–aciliyet matrisi → uygula → gün sonunda sapmaları değerlendir.\n"
        "- Görev yerleşimi: Yüksek odak işler zirvede; rutin işler düşük enerji saatlerinde; yaratıcı işler sabah erken "
        "veya akşam sakin saatlerde (kişisel ritme bağlı).\n"
        "- Boş zaman verilirse uygun görevlerle doldur; verilmezse alternatif zaman pencereleri sun.\n\n"
        "Çıktı davranışı: Kullanıcı açıkça 'günlük plan' isterse 'Saat Bazlı Görev Planı'nı üret. "
        "Mola/Egzersiz, Göz/Postür, Zorluk Sırası, Bilimsel Açıklama bölümlerini yalnızca kullanıcı 'E' yanıtını verdikten sonra ekle.\n\n"
        f"Şu anki tarih-saat (yerel): {now_local.strftime('%Y-%m-%d %H:%M:%S %Z%z')}\n"
        f"Şu anki tarih-saat (UTC):   {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"
        f"{profile_note}"
    )
    if external_prompt:
        # If user provided an external prompt, prepend it and keep dynamic context below
        system_instructions = external_prompt.strip() + "\n\n" + system_instructions

    console.rule("Agent")
    # Maintain conversation until user types exit/quit/q
    messages: List = [("system", system_instructions), ("user", prompt)]
    while True:
        last_messages: Optional[List] = None
        events = agent.stream({"messages": messages}, stream_mode="values")
        for event in events:
            message = event["messages"][-1]
            last_messages = event["messages"]
            try:
                content = getattr(message, "content", None) or str(message)
                console.print(Panel.fit(str(content)))
            except Exception:
                console.print(str(message))

        if last_messages is not None:
            messages = last_messages

        user_input = Prompt.ask("You (type 'exit' to quit)", default="").strip()
        if user_input.lower() in {"exit", "quit", "q"}:
            break
        if not user_input:
            continue
        messages.append(("user", user_input))


@app.command(name="quick-create")
def quick_create(
    summary: str = typer.Argument(..., help="Event title"),
    start: str = typer.Argument(..., help="Start datetime (YYYY-MM-DD HH:MM)"),
    end: str = typer.Argument(..., help="End datetime (YYYY-MM-DD HH:MM)"),
    timezone: Optional[str] = typer.Option(None, help="IANA timezone, e.g., Europe/Istanbul"),
    location: Optional[str] = typer.Option(None, help="Event location"),
    description: Optional[str] = typer.Option(None, help="Event description"),
    color_id: Optional[str] = typer.Option(None, help="Google Calendar color id (1-11)"),
):
    """Create an event directly using the CalendarCreateEvent tool."""
    require_google_api_key()
    from langchain_google_community.calendar.create_event import CalendarCreateEvent

    # Validate datetime format early
    for dt in (start, end):
        try:
            datetime.strptime(dt, "%Y-%m-%d %H:%M")
        except ValueError:
            console.print(f"[red]Invalid datetime format:[/red] {dt} (expected YYYY-MM-DD HH:MM)")
            raise typer.Exit(1)

    # Choose timezone: CLI arg > profile > env > default
    pf = load_user_profile()
    chosen_tz = timezone or (pf.timezone if pf else None) or os.getenv("CLI_DEFAULT_TIMEZONE", "Etc/UTC")
    # Normalize timezone (avoid libraries that fail on plain 'UTC')
    tz = chosen_tz.strip() if isinstance(chosen_tz, str) else "Etc/UTC"
    if tz.upper() == "UTC":
        tz = "Etc/UTC"

    payload = {
        "summary": summary,
        "start_datetime": start + ":00",
        "end_datetime": end + ":00",
        "timezone": tz,
    }
    if location:
        payload["location"] = location
    if description:
        payload["description"] = description
    if color_id:
        payload["color_id"] = color_id

    tool = CalendarCreateEvent()
    result = tool.invoke(payload)
    console.print(Panel.fit(str(result), title="Create Event", border_style="green"))


@app.command(name="list-calendars")
def list_calendars():
    """List calendars via toolkit tool."""
    require_google_api_key()
    from langchain_google_community.calendar.get_calendars_info import (
        GetCalendarsInfo,
    )

    tool = GetCalendarsInfo()
    out = tool.invoke({})
    try:
        data = json.loads(out) if isinstance(out, str) else out
    except Exception:
        data = out

    table = Table(title="Calendars", box=box.SIMPLE_HEAVY)
    table.add_column("Summary", style="bold")
    table.add_column("ID", style="cyan")
    if isinstance(data, list):
        for cal in data:
            table.add_row(str(cal.get("summary", "")), str(cal.get("id", "")))
    else:
        table.add_row("(unparsed)", str(out))
    console.print(table)


@app.command(name="configure-langsmith")
def configure_langsmith(
    tracing: bool = typer.Option(True, help="Enable LangSmith tracing"),
    endpoint: str = typer.Option("https://api.smith.langchain.com", help="LangSmith API endpoint"),
    api_key: Optional[str] = typer.Option(None, prompt="LangSmith API Key", hide_input=True),
    project: Optional[str] = typer.Option(None, prompt="LangSmith Project Name"),
):
    """Persist LangSmith settings into .env so you don't need to export them each time."""
    env_path = find_dotenv(usecwd=True)
    if not env_path:
        env_path = ".env"

    set_key(env_path, "LANGSMITH_TRACING", "true" if tracing else "false")
    if endpoint:
        set_key(env_path, "LANGSMITH_ENDPOINT", endpoint)
    if api_key:
        set_key(env_path, "LANGSMITH_API_KEY", api_key)
    if project:
        set_key(env_path, "LANGSMITH_PROJECT", project)

    # Reload .env for this process
    load_dotenv(override=True)

    table = Table(title="LangSmith configured", box=box.ROUNDED)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_row("LANGSMITH_TRACING", os.getenv("LANGSMITH_TRACING", "-"))
    table.add_row("LANGSMITH_ENDPOINT", os.getenv("LANGSMITH_ENDPOINT", "-"))
    table.add_row("LANGSMITH_PROJECT", os.getenv("LANGSMITH_PROJECT", "-"))
    table.add_row("LANGSMITH_API_KEY", "SET" if os.getenv("LANGSMITH_API_KEY") else "-")
    console.print(Panel.fit(table, title="Saved to .env"))


@app.command(name="init-profile")
def init_profile(path: Optional[str] = typer.Option(None, help="Custom profile path (YAML)")):
    """Create a starter user_profile.yaml if it doesn't exist."""
    target = write_default_profile_template(path)
    console.print(Panel.fit(f"Profile ready: {target}", border_style="cyan"))


@app.command(name="show-profile")
def show_profile(path: Optional[str] = typer.Option(None, help="Profile path (YAML)")):
    """Show the current user profile that the agent will use, if any."""
    pf = load_user_profile(path)
    if not pf:
        console.print("No profile found. Run: python -m calendar_cli.cli init-profile")
        return
    summary = summarize_profile_for_system(pf)
    console.print(Panel.fit(summary, title="User Profile", border_style="magenta"))


@app.command(name="init-system-prompt")
def init_system_prompt(path: Optional[str] = typer.Option(None, help="Custom system prompt path (Markdown)")):
    """Create an editable system_prompt.md if it doesn't exist and prefer it as system message."""
    target = write_default_system_prompt_template(path)
    console.print(Panel.fit(f"System prompt ready: {target}", border_style="cyan"))


@app.command(name="configure-google")
def configure_google(
    api_key: Optional[str] = typer.Option(None, prompt="Google API Key", hide_input=True),
    model: str = typer.Option("gemini-2.5-flash", help="Gemini model name"),
):
    """Persist Google API settings into .env (GOOGLE_API_KEY, GEMINI_MODEL)."""
    env_path = find_dotenv(usecwd=True)
    if not env_path:
        env_path = ".env"

    if api_key:
        set_key(env_path, "GOOGLE_API_KEY", api_key)
    if model:
        set_key(env_path, "GEMINI_MODEL", model)

    load_dotenv(override=True)

    table = Table(title="Google config saved", box=box.ROUNDED)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    table.add_row("GOOGLE_API_KEY", "SET" if os.getenv("GOOGLE_API_KEY") else "-")
    table.add_row("GEMINI_MODEL", os.getenv("GEMINI_MODEL", "-"))
    console.print(Panel.fit(table, title="Saved to .env"))


@app.command(name="preview-banner")
def preview_banner(
    font: str = typer.Option("isometric1", help="pyfiglet font name"),
    color: str = typer.Option("bright_blue", help="rich color style"),
):
    """Preview banner with given font and color (no changes saved)."""
    try:
        if font not in FigletFont.getFonts():
            console.print(f"[red]Unknown font:[/red] {font}")
            return
        fig = Figlet(font=font)
        banner = fig.renderText("Time Management") + "\n" + fig.renderText("Agent")
        console.print(Panel.fit(Text(banner, style=f"bold {color}"), title=f"[bold {color}]Preview", border_style=color))
    except Exception as e:
        console.print(f"[red]Preview failed:[/red] {e}")


@app.command(name="configure-banner")
def configure_banner(
    font: Optional[str] = typer.Option(None, help="pyfiglet font name (e.g., isometric1, slant, 3-d, banner3-D)"),
    color: Optional[str] = typer.Option(None, help="rich color (e.g., bright_blue, cyan, magenta)"),
):
    """Persist banner font/color into .env. Great choices: isometric1, isometric2, 3-d, banner3-D, slant."""
    env_path = find_dotenv(usecwd=True) or ".env"
    if font:
        set_key(env_path, "CLI_FIGLET_FONT", font)
    if color:
        set_key(env_path, "CLI_BANNER_COLOR", color)
    load_dotenv(override=True)
    console.print(Panel.fit(f"Banner updated: font={os.getenv('CLI_FIGLET_FONT')}, color={os.getenv('CLI_BANNER_COLOR')}", border_style=os.getenv("CLI_BANNER_COLOR", "bright_blue")))


def main():
    app()


if __name__ == "__main__":
    main()

