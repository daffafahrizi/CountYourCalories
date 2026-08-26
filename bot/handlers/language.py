"""
bot/handlers/language.py

Handler untuk command /lang dan /language — mengubah preferensi bahasa bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.db import supabase as db
from bot.locales import t


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Membuat keyboard inline untuk pemilihan bahasa."""
    keyboard = [
        [
            InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="set_lang:id"),
            InlineKeyboardButton("🇬🇧 English", callback_data="set_lang:en"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def handle_language_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler untuk /lang dan /language — menampilkan tombol pemilihan bahasa."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)
    lang = user.get("language", "id") if user else "id"

    # Jika user memberikan argumen langsung (misal: /lang en atau /lang id)
    if context.args:
        arg = context.args[0].lower()
        if arg in ["id", "indonesia", "indo"]:
            target_lang = "id"
        elif arg in ["en", "english", "eng"]:
            target_lang = "en"
        else:
            target_lang = None

        if target_lang:
            if user:
                db.update_user_language(telegram_id, target_lang)
            msg = t("lang_switched_success", target_lang)
            await update.message.reply_text(msg, parse_mode="Markdown")
            return

    # Tampilkan tombol pilihan bahasa
    prompt = t("lang_switch_prompt", lang)
    await update.message.reply_text(
        prompt,
        reply_markup=get_language_keyboard(),
        parse_mode="Markdown",
    )


async def handle_language_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler callback query saat tombol bahasa ditekan di luar onboarding."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if not data.startswith("set_lang:"):
        return

    new_lang = data.split(":")[1]
    telegram_id = update.effective_user.id

    # Update di database
    user = db.get_user_by_telegram_id(telegram_id)
    if user:
        db.update_user_language(telegram_id, new_lang)

    # Edit pesan yang berisi tombol menjadi pesan konfirmasi sukses
    msg = t("lang_switched_success", new_lang)
    await query.edit_message_text(msg, parse_mode="Markdown")
