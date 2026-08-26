"""
bot/handlers/text.py

Handler untuk pesan teks — input manual makanan dan perintah adjustment (Bilingual).
"""

import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from bot.db import supabase as db
from bot.agent.core import process_text_message
from bot.locales import t

# Kata kunci yang mengindikasikan perintah adjustment (Indonesian + English)
ADJUSTMENT_KEYWORDS = [
    # Indonesian
    "hapus", "delete", "undo", "batalkan", "koreksi",
    "edit", "ubah", "ganti", "update", "perbarui",
    "salah", "kurangi", "tambah", "kurang",
    # English
    "remove", "cancel", "correct", "modify", "change",
    "wrong", "reduce", "decrease", "increase", "add",
]


def _is_adjustment_command(text: str) -> bool:
    """Cek apakah pesan adalah perintah adjustment, bukan input makanan baru."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in ADJUSTMENT_KEYWORDS)


def _build_user_context(user: dict) -> str:
    """Bangun string konteks user untuk dikirim ke agent."""
    lang = user.get("language", "id")
    return (
        f"user_id={user['id']}, "
        f"telegram_id={user['telegram_id']}, "
        f"nama={user['name']}, "
        f"target_kalori={user['target_calories']} kkal, "
        f"target_protein={user['target_protein']}g, "
        f"bahasa={lang}"
    )


async def handle_catat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk command /catat — input manual makanan via teks.
    Contoh: /catat nasi goreng 1 porsi + telur dadar
    """
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)
    lang = user.get("language", "id") if user else (update.effective_user.language_code or "id")

    # Ambil argumen setelah /catat
    if not context.args:
        await update.message.reply_text(t("catat_usage", lang), parse_mode="Markdown")
        return

    food_text = " ".join(context.args)

    # Verifikasi user terdaftar
    if not user:
        await update.message.reply_text(t("not_registered", lang))
        return

    processing_msg = await update.message.reply_text(
        t("catat_processing", lang, food_text=food_text),
        parse_mode="Markdown",
    )

    try:
        user_context = _build_user_context(user)
        prompt = (
            f"Manually log the following food items (not from photo): {food_text}"
            if lang.startswith("en")
            else f"Catat makanan berikut secara manual (bukan dari foto): {food_text}"
        )
        response_text = await process_text_message(
            user_message=prompt,
            user_context=user_context,
            language=lang,
        )

        try:
            await update.message.reply_text(response_text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(response_text)

        try:
            await processing_msg.delete()
        except Exception:
            pass

    except asyncio.TimeoutError:
        timeout_msg = t("catat_timeout", lang)
        try:
            await processing_msg.edit_text(timeout_msg)
        except Exception:
            await update.message.reply_text(timeout_msg)
        print("[TIMEOUT] handle_catat: agent tidak merespons")

    except Exception as e:
        print(f"[ERROR] handle_catat: {e}")
        err_msg = t("catat_error", lang, error=str(e)[:100])
        try:
            await processing_msg.edit_text(err_msg)
        except Exception:
            await update.message.reply_text(err_msg)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk pesan teks bebas — fokus untuk perintah adjustment."""
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    # 1. Verifikasi user terdaftar
    user = db.get_user_by_telegram_id(telegram_id)
    lang = user.get("language", "id") if user else (update.effective_user.language_code or "id")

    if not user:
        await update.message.reply_text(t("not_registered", lang))
        return

    # 2. Jika bukan adjustment, arahkan ke /catat
    if not _is_adjustment_command(text):
        await update.message.reply_text(
            t("text_hint_catat", lang, text=text),
            parse_mode="Markdown",
        )
        return

    processing_msg = await update.message.reply_text(t("text_processing", lang))

    try:
        user_context = _build_user_context(user)
        response_text = await process_text_message(
            user_message=text,
            user_context=user_context,
            language=lang,
        )

        try:
            await update.message.reply_text(response_text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(response_text)

        try:
            await processing_msg.delete()
        except Exception:
            pass

    except asyncio.TimeoutError:
        timeout_msg = t("catat_timeout", lang)
        try:
            await processing_msg.edit_text(timeout_msg)
        except Exception:
            await update.message.reply_text(timeout_msg)
        print("[TIMEOUT] handle_text: agent tidak merespons")

    except Exception as e:
        print(f"[ERROR] handle_text: {e}")
        err_msg = t("catat_error", lang, error=str(e)[:100])
        try:
            await processing_msg.edit_text(err_msg)
        except Exception:
            await update.message.reply_text(err_msg)
