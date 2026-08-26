"""
bot/agent/core.py

Setup dan inisialisasi Antigravity agent sebagai otak dari CountYourCalories bot.
"""

import asyncio
import os
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import Image

from bot.agent.tools import (
    log_food_items,
    get_today_nutrition_summary,
    delete_last_food_entry,
    delete_food_entry_by_name,
    edit_food_entry,
    get_user_targets,
)

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


async def process_photo_message(
    image_path: str,
    user_context: str,
    caption: str = "",
    language: str = "id",
) -> str:
    """
    Memproses foto makanan menggunakan Antigravity agent + Gemini multimodal.

    Args:
        image_path: Path lokal ke file gambar yang sudah didownload.
        user_context: String berisi konteks user (id, nama, target, bahasa).
        caption: Caption foto dari Telegram (jika ada).
        language: Bahasa preferensi ('id' atau 'en').

    Returns:
        Respons teks dari agent.
    """
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


async def process_text_message(
    user_message: str,
    user_context: str,
    language: str = "id",
) -> str:
    """
    Memproses pesan teks dari user (input manual atau perintah adjustment).

    Args:
        user_message: Pesan teks dari pengguna.
        user_context: String berisi konteks user (id, nama, target, bahasa).
        language: Bahasa preferensi ('id' atau 'en').

    Returns:
        Respons teks dari agent.
    """
    config = create_agent_config()
    full_prompt = f"[Konteks pengguna / User Context]: {user_context}\n\n{user_message}"

    async def _run():
        async with Agent(config) as agent:
            response = await agent.chat(full_prompt)
            return await _collect_response(response)

    return await asyncio.wait_for(_run(), timeout=AGENT_TIMEOUT_SECONDS)
