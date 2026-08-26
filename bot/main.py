"""
bot/main.py

Entry point utama CountYourCalories Telegram Bot (Bilingual).
Menginisialisasi Application, mendaftarkan semua handler, dan memulai polling.
"""

import os
import asyncio
import logging

from dotenv import load_dotenv
from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.handlers.start import get_onboarding_handler
from bot.handlers.language import (
    handle_language_command,
    handle_language_callback,
)
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
        BotCommand("catat", "Catat makanan / Log food (cth: /catat ayam bakar)"),
        BotCommand("summary", "Ringkasan hari ini / Today's nutrition summary"),
        BotCommand("today", "Alias untuk /summary"),
        BotCommand("undo", "Hapus entry terakhir / Delete last logged entry"),
        BotCommand("hapus", "Hapus entry by nama / Delete entry by name"),
        BotCommand("settarget", "Ubah target / Update targets (cth: /settarget 2000 150)"),
        BotCommand("lang", "Ganti bahasa / Switch language (ID/EN)"),
        BotCommand("help", "Panduan lengkap / User guide & commands"),
        BotCommand("start", "Mulai atau setup profil / Setup profile"),
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

    # ── Language Switcher ─────────────────────────────────────────────────────
    app.add_handler(CommandHandler(["lang", "language"], handle_language_command))
    app.add_handler(CallbackQueryHandler(handle_language_callback, pattern=r"^set_lang:"))

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
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
