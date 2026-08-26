"""
bot/handlers/start.py

Handler untuk command /start dan alur onboarding bilingual (Bahasa Indonesia & English).
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.db import supabase as db
from bot.locales import t

# States untuk ConversationHandler onboarding
ASK_LANGUAGE, ASK_NAME, ASK_WEIGHT, ASK_HEIGHT, ASK_CALORIES, ASK_PROTEIN = range(6)


def _get_onboarding_lang_keyboard() -> InlineKeyboardMarkup:
    """Tombol pemilihan bahasa khusus onboarding."""
    keyboard = [
        [
            InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="onboard_lang:id"),
            InlineKeyboardButton("🇬🇧 English", callback_data="onboard_lang:en"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point /start — cek apakah user sudah terdaftar atau mulai onboarding."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if user:
        lang = user.get("language", "id")
        msg = t("welcome_existing", lang, name=user["name"])
        await update.message.reply_text(msg, parse_mode="Markdown")
        return ConversationHandler.END

    # User baru — deteksi default bahasa Telegram
    tg_lang = update.effective_user.language_code or "id"
    default_lang = "en" if tg_lang.lower().startswith("en") else "id"
    context.user_data["language"] = default_lang

    # Tampilkan prompt pemilihan bahasa
    prompt = t("choose_language", default_lang)
    await update.message.reply_text(
        prompt,
        reply_markup=_get_onboarding_lang_keyboard(),
        parse_mode="Markdown",
    )
    return ASK_LANGUAGE


async def received_language_choice(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Menerima pilihan bahasa dari inline button dan lanjut tanya nama."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    chosen_lang = data.split(":")[1] if data.startswith("onboard_lang:") else "id"
    context.user_data["language"] = chosen_lang

    # Edit pesan tombol menjadi sambutan dan tanya nama
    welcome_text = t("welcome_intro", chosen_lang)
    await query.edit_message_text(welcome_text, parse_mode="Markdown")
    return ASK_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima nama user dan tanya berat badan."""
    lang = context.user_data.get("language", "id")
    name = update.message.text.strip()
    context.user_data["name"] = name

    msg = t("ask_weight", lang, name=name)
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ASK_WEIGHT


async def received_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima berat badan dan tanya tinggi badan."""
    lang = context.user_data.get("language", "id")
    try:
        weight = float(update.message.text.strip().replace(",", "."))
        context.user_data["weight_kg"] = weight
    except ValueError:
        await update.message.reply_text(
            t("invalid_weight", lang),
            parse_mode="Markdown",
        )
        return ASK_WEIGHT

    msg = t("ask_height", lang)
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ASK_HEIGHT


async def received_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima tinggi badan dan tanya target kalori."""
    lang = context.user_data.get("language", "id")
    try:
        height = float(update.message.text.strip().replace(",", "."))
        context.user_data["height_cm"] = height
    except ValueError:
        await update.message.reply_text(
            t("invalid_height", lang),
            parse_mode="Markdown",
        )
        return ASK_HEIGHT

    msg = t("ask_calories", lang)
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ASK_CALORIES


async def received_calories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima target kalori dan tanya target protein."""
    lang = context.user_data.get("language", "id")
    try:
        calories = int(update.message.text.strip())
        context.user_data["target_calories"] = calories
    except ValueError:
        await update.message.reply_text(
            t("invalid_calories", lang),
            parse_mode="Markdown",
        )
        return ASK_CALORIES

    weight = context.user_data.get("weight_kg", 70.0)
    min_prot = int(weight * 1.6)
    max_prot = int(weight * 2.2)

    msg = t("ask_protein", lang, min_prot=min_prot, max_prot=max_prot)
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ASK_PROTEIN


async def skip_calories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip target kalori, gunakan default 2000."""
    lang = context.user_data.get("language", "id")
    context.user_data["target_calories"] = 2000

    weight = context.user_data.get("weight_kg", 70.0)
    min_prot = int(weight * 1.6)
    max_prot = int(weight * 2.2)

    msg = t("skip_calories_done", lang, min_prot=min_prot, max_prot=max_prot)
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ASK_PROTEIN


async def received_protein(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima target protein dan simpan profil user ke database."""
    lang = context.user_data.get("language", "id")
    try:
        protein = int(update.message.text.strip())
        context.user_data["target_protein"] = protein
    except ValueError:
        await update.message.reply_text(
            t("invalid_protein", lang),
            parse_mode="Markdown",
        )
        return ASK_PROTEIN

    return await _save_user_profile(update, context)


async def skip_protein(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip target protein, gunakan default 150g."""
    context.user_data["target_protein"] = 150
    return await _save_user_profile(update, context)


async def _save_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Helper: simpan profil user ke Supabase dan kirim pesan selamat datang."""
    telegram_id = update.effective_user.id
    data = context.user_data
    lang = data.get("language", "id")

    try:
        db.create_user(
            telegram_id=telegram_id,
            name=data.get("name", update.effective_user.first_name or "User"),
            weight_kg=data.get("weight_kg", 70.0),
            height_cm=data.get("height_cm", 170.0),
            target_calories=data.get("target_calories", 2000),
            target_protein=data.get("target_protein", 150),
            language=lang,
        )

        name = data.get("name", "")
        target_cal = data.get("target_calories", 2000)
        target_prot = data.get("target_protein", 150)

        welcome_msg = t(
            "profile_saved",
            lang,
            name=name,
            target_cal=target_cal,
            target_prot=target_prot,
        )
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(
            f"⚠️ Terjadi kesalahan / An error occurred: {e}. Ketik /start untuk coba lagi."
        )
        print(f"[ERROR] Gagal menyimpan profil: {e}")

    return ConversationHandler.END


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel proses onboarding."""
    lang = context.user_data.get("language", "id")
    msg = t("onboarding_cancelled", lang)
    await update.message.reply_text(msg)
    return ConversationHandler.END


def get_onboarding_handler() -> ConversationHandler:
    """Buat ConversationHandler untuk alur onboarding bilingual."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_LANGUAGE: [
                CallbackQueryHandler(received_language_choice, pattern=r"^onboard_lang:"),
            ],
            ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_name)
            ],
            ASK_WEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_weight)
            ],
            ASK_HEIGHT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_height)
            ],
            ASK_CALORIES: [
                CommandHandler("skip", skip_calories),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_calories),
            ],
            ASK_PROTEIN: [
                CommandHandler("skip", skip_protein),
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_protein),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_onboarding)],
    )
