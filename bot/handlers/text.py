"""
bot/handlers/text.py

Handler untuk pesan teks — input manual makanan dan perintah adjustment.
"""

import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from bot.db import supabase as db
from bot.agent.core import process_text_message

# Kata kunci yang mengindikasikan perintah adjustment (bukan log makanan baru)
ADJUSTMENT_KEYWORDS = [
    "hapus", "delete", "undo", "batalkan", "koreksi",
    "edit", "ubah", "ganti", "update", "perbarui",
    "salah", "kurangi", "tambah",
]


def _is_adjustment_command(text: str) -> bool:
    """Cek apakah pesan adalah perintah adjustment, bukan input makanan baru."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in ADJUSTMENT_KEYWORDS)


def _build_user_context(user: dict) -> str:
    """Bangun string konteks user untuk dikirim ke agent."""
    return (
        f"user_id={user['id']}, "
        f"telegram_id={user['telegram_id']}, "
        f"nama={user['name']}, "
        f"target_kalori={user['target_calories']} kkal, "
        f"target_protein={user['target_protein']}g"
    )


async def handle_catat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk command /catat — input manual makanan via teks.
    Contoh: /catat nasi goreng 1 porsi + telur dadar
    """
    telegram_id = update.effective_user.id

    # Ambil argumen setelah /catat
    if not context.args:
        await update.message.reply_text(
            "ℹ️ *Cara pakai /catat:*\n"
            "`/catat <nama makanan>`\n\n"
            "*Contoh:*\n"
            "• `/catat nasi goreng 1 porsi`\n"
            "• `/catat ayam bakar + nasi putih`\n"
            "• `/catat 2 butir telur rebus`\n\n"
            "_Atau kirim foto makanan langsung untuk log otomatis!_ 📸",
            parse_mode="Markdown",
        )
        return

    food_text = " ".join(context.args)

    # Verifikasi user terdaftar
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text(
            "⚠️ Kamu belum terdaftar! Ketik /start untuk setup profil dulu ya."
        )
        return

    processing_msg = await update.message.reply_text(
        f"✍️ Mencatat *{food_text}*... Tunggu sebentar!",
        parse_mode="Markdown",
    )

    try:
        user_context = _build_user_context(user)
        # Beri petunjuk ke agent bahwa ini input manual
        prompt = f"Catat makanan berikut secara manual (bukan dari foto): {food_text}"
        response_text = await process_text_message(
            user_message=prompt,
            user_context=user_context,
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
        try:
            await processing_msg.edit_text(
                "⏱️ Maaf, prosesnya terlalu lama. Coba lagi ya!",
            )
        except Exception:
            await update.message.reply_text("⏱️ Maaf, prosesnya timeout. Coba lagi ya!")
        print("[TIMEOUT] handle_catat: agent tidak merespons")

    except Exception as e:
        print(f"[ERROR] handle_catat: {e}")
        try:
            await processing_msg.edit_text(
                f"❌ Terjadi kesalahan: {e}"
            )
        except Exception:
            await update.message.reply_text(f"❌ Terjadi kesalahan: {e}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk pesan teks bebas — fokus untuk perintah adjustment."""
    telegram_id = update.effective_user.id
    text = update.message.text.strip()

    # 1. Verifikasi user terdaftar
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text(
            "⚠️ Kamu belum terdaftar! Ketik /start untuk setup profil dulu ya."
        )
        return

    # 2. Jika bukan adjustment, arahkan ke /catat
    if not _is_adjustment_command(text):
        await update.message.reply_text(
            "💡 Untuk mencatat makanan secara manual, gunakan:\n"
            f"`/catat {text}`\n\n"
            "Atau kirim *foto makanan* langsung untuk log otomatis! 📸",
            parse_mode="Markdown",
        )
        return

    processing_msg = await update.message.reply_text("⚙️ Memproses permintaanmu...")

    try:
        user_context = _build_user_context(user)
        response_text = await process_text_message(
            user_message=text,
            user_context=user_context,
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
        try:
            await processing_msg.edit_text(
                "⏱️ Maaf, prosesnya terlalu lama. Coba kirim pesan lagi ya!",
            )
        except Exception:
            await update.message.reply_text("⏱️ Maaf, prosesnya timeout. Coba kirim pesan lagi ya!")
        print("[TIMEOUT] handle_text: agent tidak merespons")

    except Exception as e:
        print(f"[ERROR] handle_text: {e}")
        try:
            await processing_msg.edit_text(
                f"❌ Terjadi kesalahan: {e}"
            )
        except Exception:
            await update.message.reply_text(f"❌ Terjadi kesalahan: {e}")
