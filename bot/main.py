"""
bot/main.py

Entry point utama CountYourCalories Telegram Bot.
Menginisialisasi Application, mendaftarkan semua handler, dan memulai polling.
"""

import os
import asyncio
import logging

from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.handlers.start import get_onboarding_handler
from bot.handlers.photo import handle_photo
from bot.handlers.text import handle_catat, handle_text
from bot.handlers.summary import handle_summary
from bot.handlers.adjust import (
    handle_undo,
    handle_hapus,
    handle_help,
    handle_settarget,
)

# Load .env
load_dotenv()

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """Daftarkan menu tombol command di antarmuka Telegram."""
    commands = [
        BotCommand("catat", "Catat makanan manual (cth: /catat nasi goreng)"),
        BotCommand("summary", "Lihat ringkasan nutrisi hari ini"),
        BotCommand("today", "Alias untuk /summary"),
        BotCommand("undo", "Hapus entry makanan terakhir"),
        BotCommand("hapus", "Hapus entry by nama (cth: /hapus nasi)"),
        BotCommand("settarget", "Ubah target (cth: /settarget 2000 150)"),
        BotCommand("help", "Panduan dan daftar perintah lengkap"),
        BotCommand("command", "Lihat semua daftar command"),
        BotCommand("start", "Mulai atau atur ulang profil onboarding"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Menu command Telegram berhasil didaftarkan!")


def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN tidak ditemukan! "
            "Pastikan file .env sudah dikonfigurasi."
        )

    # Buat Application
    app = Application.builder().token(token).post_init(post_init).build()

    # ── Onboarding (harus didaftarkan sebelum handler lainnya) ────────────────
    app.add_handler(get_onboarding_handler())

    # ── Commands ──────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler(["summary", "today"], handle_summary))
    app.add_handler(CommandHandler("catat", handle_catat))
    app.add_handler(CommandHandler("undo", handle_undo))
    app.add_handler(CommandHandler("hapus", handle_hapus))
    app.add_handler(CommandHandler("settarget", handle_settarget))
    app.add_handler(CommandHandler(["help", "command", "commands", "menu"], handle_help))

    # ── Message handlers ──────────────────────────────────────────────────────
    # Foto makanan
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # Pesan teks biasa (input manual + adjustment)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # ── Start polling ─────────────────────────────────────────────────────────
    logger.info("🚀 CountYourCalories bot dimulai! Tekan Ctrl+C untuk berhenti.")
    app.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
