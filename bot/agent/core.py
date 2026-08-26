"""
bot/agent/core.py

Setup dan inisialisasi Antigravity agent sebagai otak dari CountYourCalories bot.
Mendukung multi-provider fallback otomatis (Gemini -> OpenRouter / OpenAI).
"""

import asyncio
import logging
import os
from typing import Optional

from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import Image

from bot.agent.fallback import _image_to_base64_url, execute_fallback_chat
from bot.agent.tools import (
    delete_food_entry_by_name,
    delete_last_food_entry,
    edit_food_entry,
    get_today_nutrition_summary,
    get_user_targets,
    log_food_items,
)

logger = logging.getLogger(__name__)

# Timeout dalam detik untuk pemrosesan agent
AGENT_TIMEOUT_SECONDS = 90

SYSTEM_PROMPT = """
You are CountYourCalories, a smart nutrition assistant bot on Telegram.
Your mission is to help users effortlessly log and track their daily calories and macronutrients.

## Core Capabilities:
1. **Photo Analysis**: When a user sends a food photo, identify ALL visible food components (e.g. rice, chicken, vegetables, sauce, etc.) and estimate their individual nutritional values.
2. **Manual Text Logging**: When a user describes food via text, estimate the nutritional values.
3. **Database Logging**: After analyzing, ALWAYS save the items using the `log_food_items` tool.
4. **Corrections & Adjustments**: Help users undo, edit, or delete inaccurate entries.
5. **Daily Summaries**: Show current progress vs daily goals.

## Language Rules (CRITICAL):
- Check `[Konteks pengguna]` / `[User Context]` for the user's language: `bahasa=id` (Indonesian) or `language=en` (English).
- If `bahasa=id`: ALWAYS reply in warm, natural Indonesian.
- If `language=en`: ALWAYS reply in warm, natural English.
- If not specified, match the user's input language.

## Estimation Rules:
- Identify ALL visible foods, not just the primary dish.
- After saving to the database, ALWAYS show a friendly summary of what was logged + remaining daily targets.
- Format: calories as whole numbers, protein/carbs/fat with 1 decimal place.
- Keep responses concise, clean, and nicely formatted.

## Response Format Examples:

### When language is Indonesian (`id`):
```
✅ Berhasil dicatat!

[Emoji] [Nama Makanan] — [kalori] kkal
  Protein: [x]g | Karbo: [x]g | Lemak: [x]g

📊 Progress hari ini:
🔥 Kalori: [total]/[target] kkal ([sisa] sisa)
💪 Protein: [total]/[target]g ([sisa]g sisa)
```

### When language is English (`en`):
```
✅ Logged successfully!

[Emoji] [Food Name] — [calories] kcal
  Protein: [x]g | Carbs: [x]g | Fat: [x]g

📊 Today's Progress:
🔥 Calories: [total]/[target] kcal ([remaining] left)
💪 Protein: [total]/[target]g ([remaining]g left)
```
""".strip()


def create_agent_config() -> LocalAgentConfig:
    """Membuat konfigurasi Antigravity agent dengan API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY tidak ditemukan! Pastikan file .env sudah dikonfigurasi."
        )
    return LocalAgentConfig(
        api_key=api_key,
        system_instructions=SYSTEM_PROMPT,
        tools=[
            log_food_items,
            get_today_nutrition_summary,
            delete_last_food_entry,
            delete_food_entry_by_name,
            edit_food_entry,
            get_user_targets,
        ],
    )


async def _collect_response(response) -> str:
    """Kumpulkan semua chunk streaming dari response agent."""
    chunks = []
    async for chunk in response:
        chunks.append(chunk)
    result = "".join(chunks).strip()
    if not result and hasattr(response, "text"):
        result = await response.text()
    return result


def _has_fallback_provider() -> bool:
    """Cek apakah ada provider cadangan di .env."""
    return bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))


async def _run_gemini_photo(
    image_path: str,
    user_context: str,
    caption: str = "",
    language: str = "id",
) -> str:
    """Jalankan analisis foto dengan Gemini Flash via Google Antigravity SDK."""
    config = create_agent_config()
    is_en = language.startswith("en")

    if is_en:
        prompt_parts = [
            f"[User Context]: {user_context}\n\n",
            "This is a photo of the food I just ate. ",
        ]
        if caption:
            prompt_parts.append(f"My note: {caption}. ")
        prompt_parts.append(
            "Please analyze all food items in this photo, estimate their nutritional values, "
            "and save them to the database using log_food_items."
        )
    else:
        prompt_parts = [
            f"[Konteks pengguna]: {user_context}\n\n",
            "Ini adalah foto makanan yang baru saja saya makan. ",
        ]
        if caption:
            prompt_parts.append(f"Keterangan dari saya: {caption}. ")
        prompt_parts.append(
            "Tolong analisis semua makanan yang ada di foto ini, estimasikan nutrisinya, "
            "dan simpan ke database menggunakan log_food_items."
        )

    image = Image.from_file(image_path)
    full_prompt = ["".join(prompt_parts), image]

    async def _run():
        async with Agent(config) as agent:
            response = await agent.chat(full_prompt)
            return await _collect_response(response)

    return await asyncio.wait_for(_run(), timeout=AGENT_TIMEOUT_SECONDS)


async def _run_fallback_photo(
    image_path: str,
    user_context: str,
    caption: str = "",
    language: str = "id",
) -> str:
    """Jalankan analisis foto dengan OpenRouter / OpenAI fallback."""
    is_en = language.startswith("en")
    image_url = _image_to_base64_url(image_path)

    instruction = (
        f"[User Context]: {user_context}\n"
        f"Photo note: {caption}\n"
        "Analyze this food photo, estimate nutrition, and save to database using log_food_items."
        if is_en
        else f"[Konteks pengguna]: {user_context}\n"
        f"Keterangan foto: {caption}\n"
        "Analisis foto makanan ini, estimasikan nutrisinya, dan simpan ke database menggunakan log_food_items."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ]

    return await execute_fallback_chat(
        system_prompt=SYSTEM_PROMPT,
        messages=messages,
        timeout=AGENT_TIMEOUT_SECONDS,
    )


async def process_photo_message(
    image_path: str,
    user_context: str,
    caption: str = "",
    language: str = "id",
) -> str:
    """
    Memproses foto makanan dengan primary Gemini + automatic fallback switcher.
    """
    try:
        return await _run_gemini_photo(
            image_path=image_path,
            user_context=user_context,
            caption=caption,
            language=language,
        )
    except Exception as e:
        logger.warning(
            f"⚠️ [PRIMARY AI] Gemini mengalami kendala: {e}. "
            f"Mengecek ketersediaan provider fallback..."
        )
        if _has_fallback_provider():
            logger.info("⚡ [FAILOVER] Mengaktifkan fallback model (OpenRouter / OpenAI)...")
            try:
                return await _run_fallback_photo(
                    image_path=image_path,
                    user_context=user_context,
                    caption=caption,
                    language=language,
                )
            except Exception as fallback_err:
                logger.error(f"❌ [FALLBACK FAILED] {fallback_err}")
                raise fallback_err
        raise e


async def _run_gemini_text(
    user_message: str,
    user_context: str,
) -> str:
    """Jalankan pemrosesan teks dengan Gemini Flash."""
    config = create_agent_config()
    full_prompt = f"[Konteks pengguna / User Context]: {user_context}\n\n{user_message}"

    async def _run():
        async with Agent(config) as agent:
            response = await agent.chat(full_prompt)
            return await _collect_response(response)

    return await asyncio.wait_for(_run(), timeout=AGENT_TIMEOUT_SECONDS)


async def _run_fallback_text(
    user_message: str,
    user_context: str,
) -> str:
    """Jalankan pemrosesan teks dengan fallback OpenRouter / OpenAI."""
    messages = [
        {
            "role": "user",
            "content": f"[Konteks pengguna / User Context]: {user_context}\n\n{user_message}",
        }
    ]
    return await execute_fallback_chat(
        system_prompt=SYSTEM_PROMPT,
        messages=messages,
        timeout=AGENT_TIMEOUT_SECONDS,
    )


async def process_text_message(
    user_message: str,
    user_context: str,
    language: str = "id",
) -> str:
    """
    Memproses pesan teks dengan primary Gemini + automatic fallback switcher.
    """
    try:
        return await _run_gemini_text(
            user_message=user_message,
            user_context=user_context,
        )
    except Exception as e:
        logger.warning(
            f"⚠️ [PRIMARY AI] Gemini teks mengalami kendala: {e}. "
            f"Mengecek ketersediaan provider fallback..."
        )
        if _has_fallback_provider():
            logger.info("⚡ [FAILOVER] Mengaktifkan fallback model teks (OpenRouter / OpenAI)...")
            try:
                return await _run_fallback_text(
                    user_message=user_message,
                    user_context=user_context,
                )
            except Exception as fallback_err:
                logger.error(f"❌ [FALLBACK FAILED] {fallback_err}")
                raise fallback_err
        raise e
