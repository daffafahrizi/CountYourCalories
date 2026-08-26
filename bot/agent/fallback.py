"""
bot/agent/fallback.py

Fallback AI engine yang kompatibel dengan OpenRouter dan OpenAI.
Digunakan otomatis jika provider utama (Gemini) mengalami 503, 429, atau timeout.
"""

import base64
import json
import logging
import mimetypes
import os
from typing import Any

import httpx

from bot.agent.tools import (
    delete_food_entry_by_name,
    delete_last_food_entry,
    edit_food_entry,
    get_today_nutrition_summary,
    get_user_targets,
    log_food_items,
)

logger = logging.getLogger(__name__)

# Daftar tools dalam format OpenAPI / OpenAI Function Calling
FALLBACK_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "log_food_items",
            "description": "Menyimpan satu atau beberapa item makanan ke database untuk pengguna tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "UUID pengguna di database Supabase.",
                    },
                    "items": {
                        "type": "array",
                        "description": "Daftar item makanan yang teridentifikasi.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "meal_name": {"type": "string"},
                                "calories": {"type": "integer"},
                                "protein_g": {"type": "number"},
                                "carbs_g": {"type": "number"},
                                "fat_g": {"type": "number"},
                                "source": {
                                    "type": "string",
                                    "enum": ["photo", "text"],
                                },
                            },
                            "required": ["meal_name", "calories", "protein_g"],
                        },
                    },
                },
                "required": ["user_id", "items"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_today_nutrition_summary",
            "description": "Mengambil total nutrisi yang sudah dikonsumsi pengguna hari ini.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "UUID pengguna di database Supabase.",
                    }
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_last_food_entry",
            "description": "Menghapus entry makanan terakhir yang diinput hari ini (undo).",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "UUID pengguna di database Supabase.",
                    }
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_food_entry_by_name",
            "description": "Menghapus entry makanan hari ini yang cocok dengan nama tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "UUID pengguna di database Supabase.",
                    },
                    "meal_name": {"type": "string"},
                },
                "required": ["user_id", "meal_name"],
            },
        },
    },
]

TOOL_MAPPING = {
    "log_food_items": log_food_items,
    "get_today_nutrition_summary": get_today_nutrition_summary,
    "delete_last_food_entry": delete_last_food_entry,
    "delete_food_entry_by_name": delete_food_entry_by_name,
    "edit_food_entry": edit_food_entry,
    "get_user_targets": get_user_targets,
}


def _image_to_base64_url(image_path: str) -> str:
    """Mengubah file gambar lokal menjadi data URI base64."""
    mime, _ = mimetypes.guess_type(image_path)
    mime = mime or "image/jpeg"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def _get_fallback_config() -> tuple[str, str, str]:
    """
    Mengambil API key, base URL, dan model untuk fallback.
    Mendukung OpenRouter atau OpenAI langsung.
    """
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if openrouter_key:
        # Default model OpenRouter: gratis vision model atau pilihan user
        model = os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.2-11b-vision-instruct:free"
        )
        return openrouter_key, "https://openrouter.ai/api/v1", model

    if openai_key:
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return openai_key, "https://api.openai.com/v1", model

    raise RuntimeError(
        "Tidak ada API key fallback yang dikonfigurasi (OPENROUTER_API_KEY atau OPENAI_API_KEY)."
    )


async def execute_fallback_chat(
    system_prompt: str,
    messages: list[dict[str, Any]],
    timeout: float = 60.0,
) -> str:
    """
    Menjalankan chat completions dengan tool calling melalui provider fallback (OpenRouter/OpenAI).
    """
    api_key, base_url, model = _get_fallback_config()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/daffafahrizi/CountYourCalories",
        "X-Title": "CountYourCalories Telegram Bot",
    }

    formatted_messages = [{"role": "system", "content": system_prompt}] + messages

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Turn 1: Kirim prompt + foto + tool definitions
        payload = {
            "model": model,
            "messages": formatted_messages,
            "tools": FALLBACK_TOOLS,
            "tool_choice": "auto",
        }

        resp = await client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )

        if resp.status_code != 200:
            raise RuntimeError(
                f"Fallback API error ({resp.status_code}): {resp.text[:200]}"
            )

        data = resp.json()
        choice = data["choices"][0]
        msg = choice["message"]

        # Jika model meminta pemanggilan tool (tool_calls)
        tool_calls = msg.get("tool_calls")
        if tool_calls:
            formatted_messages.append(msg)

            for tc in tool_calls:
                fn_name = tc["function"]["name"]
                fn_args_str = tc["function"].get("arguments", "{}")
                try:
                    fn_args = json.loads(fn_args_str)
                except Exception:
                    fn_args = {}

                fn = TOOL_MAPPING.get(fn_name)
                if fn:
                    try:
                        tool_result = fn(**fn_args)
                    except Exception as e:
                        tool_result = f"Error executing tool {fn_name}: {e}"
                else:
                    tool_result = f"Tool {fn_name} not found."

                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": fn_name,
                    "content": json.dumps(tool_result) if not isinstance(tool_result, str) else tool_result,
                })

            # Turn 2: Kirim hasil tool kembali ke model untuk mendapatkan formatted response akhir
            payload_turn2 = {
                "model": model,
                "messages": formatted_messages,
            }
            resp_turn2 = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload_turn2,
            )

            if resp_turn2.status_code == 200:
                data_turn2 = resp_turn2.json()
                return data_turn2["choices"][0]["message"].get("content", "")

        return msg.get("content", "")
