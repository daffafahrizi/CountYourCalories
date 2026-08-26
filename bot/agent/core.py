"""
bot/agent/core.py

Setup dan inisialisasi AI agent sebagai otak dari CountYourCalories bot.
Menggunakan direct asynchronous Gemini 3.6-Flash API dengan dynamic multi-turn tool calling,
serta dilengkapi multi-tier automatic failover (Gemini 3.6 -> Gemini 2.5 -> OpenRouter / OpenAI).
"""

import asyncio
import base64
import json
import logging
import mimetypes
import os
from typing import Any, Optional

import httpx
from dotenv import load_dotenv

# Pastikan .env selalu ter-load dari project root
load_dotenv(os.path.join(os.getcwd(), ".env"), override=True)

from bot.agent.fallback import execute_fallback_chat
from bot.agent.tools import (
    delete_food_entry_by_name,
    delete_last_food_entry,
    edit_food_entry,
    get_today_nutrition_summary,
    get_user_targets,
    log_food_items,
)

logger = logging.getLogger(__name__)

# Timeout per request AI (detik)
AI_TIMEOUT_SECONDS = 30.0

TOOL_MAPPING = {
    "log_food_items": log_food_items,
    "get_today_nutrition_summary": get_today_nutrition_summary,
    "delete_last_food_entry": delete_last_food_entry,
    "delete_food_entry_by_name": delete_food_entry_by_name,
    "edit_food_entry": edit_food_entry,
    "get_user_targets": get_user_targets,
}

GEMINI_TOOLS_SCHEMA = [
    {
        "function_declarations": [
            {
                "name": "log_food_items",
                "description": "Menyimpan item makanan yang diidentifikasi ke database untuk pengguna.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "items": {
                            "type": "ARRAY",
                            "description": "Daftar makanan yang teridentifikasi.",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "meal_name": {"type": "STRING", "description": "Nama makanan"},
                                    "calories": {"type": "INTEGER", "description": "Estimasi total kalori (kkal)"},
                                    "protein_g": {"type": "NUMBER", "description": "Estimasi protein (gram)"},
                                    "carbs_g": {"type": "NUMBER", "description": "Estimasi karbohidrat (gram)"},
                                    "fat_g": {"type": "NUMBER", "description": "Estimasi lemak (gram)"},
                                    "source": {"type": "STRING", "enum": ["photo", "text"]}
                                },
                                "required": ["meal_name", "calories", "protein_g"]
                            }
                        }
                    },
                    "required": ["items"]
                }
            },
            {
                "name": "get_today_nutrition_summary",
                "description": "Mengambil total nutrisi yang sudah dikonsumsi pengguna hari ini.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "delete_last_food_entry",
                "description": "Menghapus entri makanan terakhir yang dicatat hari ini (undo).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "delete_food_entry_by_name",
                "description": "Menghapus entri makanan hari ini berdasarkan nama makanan.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "meal_name": {"type": "STRING", "description": "Nama makanan yang ingin dihapus"}
                    },
                    "required": ["meal_name"]
                }
            }
        ]
    }
]

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
## Formatting Rules (CRITICAL):
- Do NOT wrap your entire response in markdown code blocks (``` or ```markdown).
- Write normal readable Telegram message text using bold (*text*), emojis, and line breaks.
- Never output code blocks unless showing a specific raw snippet.

## Response Format Examples:

### When language is Indonesian (`id`):
✅ *Berhasil dicatat!*

🍛 *Nasi Goreng Telur* — 350 kkal
  Protein: 12g | Karbo: 45g | Lemak: 14g

📊 *Progress hari ini:*
🔥 Kalori: 850/1700 kkal (850 kkal sisa)
💪 Protein: 42/130g (88g sisa)

### When language is English (`en`):
✅ *Logged successfully!*

🍛 *Fried Rice with Egg* — 350 kcal
  Protein: 12g | Carbs: 45g | Fat: 14g

📊 *Today's Progress:*
🔥 Calories: 850/1700 kcal (850 kcal left)
💪 Protein: 42/130g (88g left)
""".strip()


def _extract_user_id(user_context: str) -> str:
    """Mengambil UUID user_id dari string context."""
    for part in user_context.split(","):
        part = part.strip()
        if part.startswith("user_id="):
            return part.split("user_id=")[1].strip()
    return ""


def _extract_telegram_id(user_context: str) -> int:
    """Mengambil integer telegram_id dari string context."""
    for part in user_context.split(","):
        part = part.strip()
        if part.startswith("telegram_id="):
            try:
                return int(part.split("telegram_id=")[1].strip())
            except ValueError:
                return 0
    return 0


def _image_to_gemini_part(image_path: str) -> dict:
    """Mengubah file gambar lokal menjadi payload inlineData Gemini."""
    mime, _ = mimetypes.guess_type(image_path)
    mime = mime or "image/jpeg"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return {
        "inline_data": {
            "mime_type": mime,
            "data": encoded
        }
    }


async def _execute_gemini_turns(
    contents: list[dict],
    user_id: str,
    telegram_id: int = 0,
    model: str = "gemini-3.6-flash",
    max_turns: int = 5,
    timeout: float = AI_TIMEOUT_SECONDS,
) -> str:
    """
    Menjalankan percakapan Gemini dengan dynamic multi-turn tool calling loop via HTTP.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY tidak ditemukan di .env!")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    async with httpx.AsyncClient(timeout=timeout) as client:
        for turn in range(max_turns):
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": contents,
                "tools": GEMINI_TOOLS_SCHEMA,
            }
            res = await client.post(url, json=payload)
            if res.status_code != 200:
                raise RuntimeError(f"Gemini {model} API error ({res.status_code}): {res.text[:200]}")

            data = res.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return ""

            parts = candidates[0].get("content", {}).get("parts", [])
            fn_call = next((p for p in parts if "functionCall" in p), None)

            if fn_call:
                fn_name = fn_call["functionCall"]["name"]
                fn_args = fn_call["functionCall"].get("args", {})
                logger.info(f"⚙️ [TOOL CALL Turn {turn+1}] {fn_name} with args: {fn_args}")

                try:
                    if fn_name == "log_food_items":
                        tool_res = log_food_items(user_id=user_id, items=fn_args.get("items", []))
                    elif fn_name == "get_today_nutrition_summary":
                        tool_res = get_today_nutrition_summary(user_id=user_id)
                    elif fn_name == "delete_last_food_entry":
                        tool_res = delete_last_food_entry(user_id=user_id)
                    elif fn_name == "delete_food_entry_by_name":
                        tool_res = delete_food_entry_by_name(user_id=user_id, meal_name=fn_args.get("meal_name", ""))
                    elif fn_name == "edit_food_entry":
                        tool_res = edit_food_entry(user_id=user_id, meal_name=fn_args.get("meal_name", ""), new_values=fn_args.get("new_values", {}))
                    elif fn_name == "get_user_targets":
                        tg_id = int(fn_args.get("telegram_id", 0)) or telegram_id
                        tool_res = get_user_targets(user_id=user_id, telegram_id=tg_id)
                    else:
                        tool_res = f"Tool {fn_name} not found."
                except Exception as e:
                    tool_res = f"Error executing {fn_name}: {e}"

                # Append model tool_call & user functionResponse
                contents.append({"role": "model", "parts": [fn_call]})
                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": fn_name,
                            "response": {"result": tool_res}
                        }
                    }]
                })
                # Lanjut ke turn berikutnya
                continue

            # Jika tidak ada function call, kita sudah mendapatkan respon teks akhir
            text_parts = [p.get("text", "") for p in parts if "text" in p]
            final_text = "".join(text_parts).strip()
            
            # Bersihkan jika LLM tidak sengaja membungkus seluruh teks dengan ```markdown atau ```
            if final_text.startswith("```"):
                lines = final_text.splitlines()
                if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
                    final_text = "\n".join(lines[1:-1]).strip()
            
            return final_text

    return ""


async def _run_gemini_with_fallback(
    contents: list[dict],
    user_context: str,
    language: str = "id",
) -> str:
    """
    Menjalankan Gemini 3.6-flash, dengan fallback bertingkat:
    1. Gemini 3.6-flash (Primary - Ultra Fast)
    2. Gemini 2.5-flash (Secondary Gemini)
    3. OpenRouter / OpenAI (Tertiary Fallback)
    """
    user_id = _extract_user_id(user_context)
    telegram_id = _extract_telegram_id(user_context)

    # 1. Coba Gemini 3.6-flash
    try:
        res = await _execute_gemini_turns(contents=contents, user_id=user_id, telegram_id=telegram_id, model="gemini-3.6-flash")
        if res:
            return res
    except Exception as e1:
        logger.warning(f"⚠️ [PRIMARY AI] Gemini 3.6-flash terkendala: {e1}. Mencoba Gemini 2.5-flash...")

    # 2. Coba Gemini 2.5-flash
    try:
        res = await _execute_gemini_turns(contents=contents, user_id=user_id, telegram_id=telegram_id, model="gemini-2.5-flash")
        if res:
            return res
    except Exception as e2:
        logger.warning(f"⚠️ [PRIMARY AI] Gemini 2.5-flash terkendala: {e2}. Mengecek OpenRouter/OpenAI fallback...")

    # 3. Coba OpenRouter / OpenAI fallback
    if os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"):
        logger.info("⚡ [FAILOVER] Mengaktifkan provider cadangan (OpenRouter/OpenAI)...")
        # Ekstrak teks dari contents untuk format OpenAI
        text_prompt = ""
        image_part = None
        for c in contents:
            for p in c.get("parts", []):
                if "text" in p:
                    text_prompt += p["text"] + "\n"
                elif "inline_data" in p:
                    mime = p["inline_data"].get("mime_type", "image/jpeg")
                    data = p["inline_data"].get("data", "")
                    image_part = f"data:{mime};base64,{data}"

        messages = []
        if image_part:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                    {"type": "image_url", "image_url": {"url": image_part}},
                ]
            })
        else:
            messages.append({
                "role": "user",
                "content": text_prompt
            })

        return await execute_fallback_chat(
            system_prompt=SYSTEM_PROMPT,
            messages=messages,
            user_context=user_context,
            timeout=AI_TIMEOUT_SECONDS,
        )

    raise RuntimeError("Seluruh AI provider sedang tidak dapat dijangkau. Silakan coba sesaat lagi.")


async def process_photo_message(
    image_path: str,
    user_context: str,
    caption: str = "",
    language: str = "id",
) -> str:
    """
    Memproses foto makanan menggunakan Vision AI.
    """
    is_en = language.startswith("en")
    if is_en:
        prompt_text = (
            f"[User Context]: {user_context}\n\n"
            f"This is a photo of the food I just ate. "
            f"{'Note: ' + caption if caption else ''}\n"
            f"Please analyze all food items in this photo, estimate their nutritional values, "
            f"and save them to the database using log_food_items."
        )
    else:
        prompt_text = (
            f"[Konteks pengguna]: {user_context}\n\n"
            f"Ini adalah foto makanan yang baru saja saya makan. "
            f"{'Keterangan: ' + caption if caption else ''}\n"
            f"Tolong analisis semua makanan di foto ini, estimasikan nutrisinya, "
            f"dan simpan ke database menggunakan log_food_items."
        )

    image_part = _image_to_gemini_part(image_path)
    contents = [
        {
            "role": "user",
            "parts": [
                {"text": prompt_text},
                image_part,
            ]
        }
    ]

    return await _run_gemini_with_fallback(contents, user_context, language)


async def process_text_message(
    user_message: str,
    user_context: str,
    language: str = "id",
) -> str:
    """
    Memproses pesan teks pencatatan atau adjustment makanan.
    """
    prompt_text = f"[Konteks pengguna / User Context]: {user_context}\n\n{user_message}"
    contents = [
        {
            "role": "user",
            "parts": [{"text": prompt_text}]
        }
    ]
    return await _run_gemini_with_fallback(contents, user_context, language)
