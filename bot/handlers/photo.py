"""
bot/handlers/photo.py

Handler untuk pesan foto makanan dari pengguna (Bilingual).
"""

import asyncio
import os
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import supabase as db
from bot.agent.core import process_photo_message
from bot.locales import t


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


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler utama untuk pesan foto makanan."""
    telegram_id = update.effective_user.id

    # 1. Verifikasi user terdaftar
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        tg_lang = update.effective_user.language_code or "id"
        await update.message.reply_text(t("not_registered", tg_lang))
        return

    lang = user.get("language", "id")

    # 2. Kirim pesan "sedang diproses"
    processing_msg = await update.message.reply_text(t("photo_analyzing", lang))

    # 3. Download foto (ambil resolusi tertinggi)
    photo = update.message.photo[-1]
    caption = update.message.caption or ""

    try:
        file = await context.bot.get_file(photo.file_id)

        # Simpan foto ke file temp
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        await file.download_to_drive(tmp_path)

        # 4. Proses dengan Antigravity agent
        user_context = _build_user_context(user)
        response_text = await process_photo_message(
            image_path=tmp_path,
            user_context=user_context,
            caption=caption,
            language=lang,
        )

        # 5. Kirim hasil (dengan fallback jika format Markdown gagal diparse Telegram)
        try:
            await update.message.reply_text(response_text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(response_text)

        # Hapus pesan "sedang diproses" setelah hasil terkirim
        try:
            await processing_msg.delete()
        except Exception:
            pass

    except asyncio.TimeoutError:
        timeout_msg = t("photo_timeout", lang)
        try:
            await processing_msg.edit_text(timeout_msg)
        except Exception:
            await update.message.reply_text(timeout_msg)
        print("[TIMEOUT] handle_photo: agent timeout")

    except Exception as e:
        print(f"[ERROR] handle_photo: {e}")
        err_msg = t("photo_error", lang, error=str(e)[:100])
        try:
            await processing_msg.edit_text(err_msg)
        except Exception:
            await update.message.reply_text(err_msg)

    finally:
        # Hapus file temp dengan aman
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
