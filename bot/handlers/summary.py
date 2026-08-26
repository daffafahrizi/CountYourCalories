"""
bot/handlers/summary.py

Handler untuk command /summary dan /today — menampilkan ringkasan nutrisi hari ini (Bilingual).
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import supabase as db
from bot.locales import t


def _progress_bar(current: int, target: int, length: int = 10) -> str:
    """Buat progress bar visual."""
    if target <= 0:
        return "░" * length
    filled = min(int((current / target) * length), length)
    return "█" * filled + "░" * (length - filled)


def _format_summary(user: dict, summary: dict) -> str:
    """Format ringkasan nutrisi menjadi pesan Telegram dwibahasa yang rapi."""
    lang = user.get("language", "id")
    name = user["name"]
    target_cal = user["target_calories"]
    target_prot = user["target_protein"]

    total_cal = summary["total_calories"]
    total_prot = summary["total_protein"]
    total_carbs = summary["total_carbs"]
    total_fat = summary["total_fat"]
    entries = summary["entries"]

    sisa_cal = target_cal - total_cal
    sisa_prot = target_prot - total_prot

    # Progress bars
    bar_cal = _progress_bar(total_cal, target_cal)
    bar_prot = _progress_bar(total_prot, target_prot)

    # Status pesan berdasarkan progress protein
    persen_prot = (total_prot / target_prot * 100) if target_prot > 0 else 0
    if persen_prot >= 100:
        status = t("status_protein_100", lang)
    elif persen_prot >= 75:
        status = t("status_protein_75", lang)
    elif persen_prot >= 50:
        status = t("status_protein_50", lang)
    else:
        status = t("status_protein_low", lang)

    # Format daftar makanan
    if entries:
        food_list = "\n".join(
            f"  • {e['meal_name']} — {e['calories']} kcal (P:{e['protein_g']}g)"
            for e in entries
        )
    else:
        food_list = t("summary_no_meals", lang)

    # Format teks sisa / lebih
    if sisa_cal < 0:
        sisa_str_cal = t("summary_over", lang, lebih=abs(sisa_cal))
    else:
        sisa_str_cal = t("summary_remaining", lang, sisa=sisa_cal)

    if sisa_prot < 0:
        sisa_str_prot = t("summary_over_prot", lang, lebih=f"{abs(sisa_prot):.1f}")
    else:
        sisa_str_prot = t("summary_remaining_prot", lang, sisa=f"{sisa_prot:.1f}")

    header = t("summary_title", lang, name=name)
    logged_label = t("summary_logged_meals", lang)
    progress_label = t("summary_nutrition_progress", lang)
    cal_line = t(
        "summary_cal_line",
        lang,
        bar=bar_cal,
        total=total_cal,
        target=target_cal,
        sisa=sisa_str_cal,
    )
    prot_line = t(
        "summary_prot_line",
        lang,
        bar=bar_prot,
        total=total_prot,
        target=target_prot,
        sisa=sisa_str_prot,
    )
    carbs_line = t("summary_carbs_line", lang, total=total_carbs)
    fat_line = t("summary_fat_line", lang, total=total_fat)

    return (
        f"{header}\n\n"
        f"{logged_label}\n"
        f"{food_list}\n\n"
        f"{progress_label}\n"
        f"{cal_line}\n"
        f"{prot_line}\n"
        f"{carbs_line}\n"
        f"{fat_line}\n\n"
        f"{status}"
    )


async def handle_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /summary dan /today."""
    telegram_id = update.effective_user.id

    # Verifikasi user terdaftar
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        tg_lang = update.effective_user.language_code or "id"
        await update.message.reply_text(t("not_registered", tg_lang))
        return

    summary = db.get_today_summary(user["id"])
    message = _format_summary(user, summary)

    await update.message.reply_text(message, parse_mode="Markdown")
