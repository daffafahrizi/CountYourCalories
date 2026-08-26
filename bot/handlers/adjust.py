"""
bot/handlers/adjust.py

Handler untuk perintah quick adjustment (Bilingual):
- /undo — hapus entry terakhir
- /hapus <nama> — hapus entry by nama
- /settarget — ubah target kalori dan protein
- /help — panduan lengkap
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import supabase as db
from bot.locales import t


async def handle_undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /undo — menghapus entry makanan terakhir hari ini."""
    telegram_id = update.effective_user.id

    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        tg_lang = update.effective_user.language_code or "id"
        await update.message.reply_text(t("not_registered", tg_lang))
        return

    lang = user.get("language", "id")
    last = db.get_last_log(user["id"])
    if not last:
        await update.message.reply_text(t("undo_empty", lang))
        return

    db.delete_log_by_id(last["id"])

    # Tampilkan sisa setelah undo
    summary = db.get_today_summary(user["id"])
    msg = t(
        "undo_success",
        lang,
        meal_name=last["meal_name"],
        calories=last["calories"],
        total_cal=summary["total_calories"],
        target_cal=user["target_calories"],
        total_prot=summary["total_protein"],
        target_prot=user["target_protein"],
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_hapus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk /hapus <nama_makanan>.
    Contoh: /hapus nasi goreng
    """
    telegram_id = update.effective_user.id

    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        tg_lang = update.effective_user.language_code or "id"
        await update.message.reply_text(t("not_registered", tg_lang))
        return

    lang = user.get("language", "id")

    # Ambil nama makanan dari argumen command
    if not context.args:
        await update.message.reply_text(t("hapus_usage", lang), parse_mode="Markdown")
        return

    meal_name = " ".join(context.args)
    count = db.delete_logs_by_name(user["id"], meal_name)

    if count == 0:
        await update.message.reply_text(
            t("hapus_not_found", lang, meal_name=meal_name),
            parse_mode="Markdown",
        )
        return

    summary = db.get_today_summary(user["id"])
    msg = t(
        "hapus_success",
        lang,
        count=count,
        meal_name=meal_name,
        total_cal=summary["total_calories"],
        target_cal=user["target_calories"],
        total_prot=summary["total_protein"],
        target_prot=user["target_protein"],
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /help — menampilkan semua perintah yang tersedia."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)
    lang = user.get("language", "id") if user else (update.effective_user.language_code or "id")

    msg = t("help_text", lang)
    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_settarget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk /settarget — update target kalori dan protein.
    Contoh: /settarget 2000 150
    """
    telegram_id = update.effective_user.id

    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        tg_lang = update.effective_user.language_code or "id"
        await update.message.reply_text(t("not_registered", tg_lang))
        return

    lang = user.get("language", "id")

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(t("settarget_usage", lang), parse_mode="Markdown")
        return

    try:
        new_calories = int(context.args[0])
        new_protein = int(context.args[1])
    except ValueError:
        await update.message.reply_text(t("settarget_invalid", lang), parse_mode="Markdown")
        return

    db.update_user_targets(
        telegram_id=telegram_id,
        target_calories=new_calories,
        target_protein=new_protein,
    )

    msg = t(
        "settarget_success",
        lang,
        calories=new_calories,
        protein=new_protein,
    )
    await update.message.reply_text(msg, parse_mode="Markdown")
