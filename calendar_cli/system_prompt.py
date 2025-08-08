from __future__ import annotations

import os
from typing import Optional


DEFAULT_SYSTEM_PROMPT_ENV_KEY = "CALENDAR_CLI_SYSTEM_PROMPT"
DEFAULT_SYSTEM_PROMPT_PATH = "system_prompt.md"


DEFAULT_SYSTEM_PROMPT_TEMPLATE = """
# System Prompt (You can edit freely)

Rol: Zaman Yönetimi Danışmanı ve takvim ajanı.
Amaç: Kullanıcı talebini kısa ve net yanıtlamak; gerektiğinde takvimde güvenli işlemler yapmak.
İletişim: Gereksiz uzatma yok. Sonunda yalnızca "Öneri ve kısa bilimsel açıklama eklememi ister misiniz? (E/H)" diye sor.

İç kurallar (özet):
- Biyolojik saat: 09:00–11:00 ve 16:00–18:00 zirve; ~14:00 ve geç saatlerde odak azalır.
- Zaman yönetimi: Planlama (önemli işler zirvede), Tutum (ertelemeden kaçın), Tuzaklar (gereksiz toplantı/sosyal medya vb.).
- Mola/sağlık: 20-20-20; 60–90 dk’da 5–10 dk aktif mola; postür değişikliği/esneme.
- Süreç: Zaman kütüğü → önem–aciliyet → uygula → gün sonu değerlendirme.
- Yerleşim: Yüksek odak işler zirvede; rutin işler düşük enerji; yaratıcı işler sabah erken/akşam sakin.

Not: Bu metni değiştirebilir, kendi metodolojinizi yazabilirsiniz.
"""


def get_default_system_prompt_path() -> str:
    return os.getenv(DEFAULT_SYSTEM_PROMPT_ENV_KEY, DEFAULT_SYSTEM_PROMPT_PATH)


def write_default_system_prompt_template(path: Optional[str] = None) -> str:
    target_path = path or get_default_system_prompt_path()
    if os.path.exists(target_path):
        return target_path
    with open(target_path, "w", encoding="utf-8") as f:
        f.write(DEFAULT_SYSTEM_PROMPT_TEMPLATE.strip() + "\n")
    return target_path


def load_system_prompt(path: Optional[str] = None) -> Optional[str]:
    target_path = path or get_default_system_prompt_path()
    if not os.path.exists(target_path):
        return None
    try:
        with open(target_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

