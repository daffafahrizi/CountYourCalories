"""
bot/handlers/summary.py

Handler untuk command /summary dan /today — menampilkan ringkasan nutrisi hari ini.
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import supabase as db


def _progress_bar(current: int, target: int, length: int = 10) -> str:
    """Buat progress bar sederhana."""
    if target <= 0:
        return "░" * length
    filled = min(int((current / target) * length), length)
    return "█" * filled + "░" * (length - filled)


def _format_summary(user: dict, summary: dict) -> str:
    """Format ringkasan nutrisi menjadi pesan Telegram yang rapi."""
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

    # Status emoji berdasarkan progress protein
    persen_prot = (total_prot / target_prot * 100) if target_prot > 0 else 0
    if persen_prot >= 100:
        status = "🎉 Target protein tercapai! Luar biasa!"
    elif persen_prot >= 75:
        status = "💪 Hampir sampai target proteinmu, terus semangat!"
    elif persen_prot >= 50:
        status = "📈 Sudah setengah jalan, pertahankan!"
    else:
        status = "🥗 Jangan lupa tingkatkan asupan proteinmu ya!"

    # Daftar makanan yang sudah dimakan
    if entries:
        food_list = "\n".join(
            f"  • {e['meal_name']} — {e['calories']} kkal "
            f"(P:{e['protein_g']}g)"
            for e in entries
        )
    else:
        food_list = "  _Belum ada makanan yang tercatat hari ini_"

    # Format pesan akhir
    sisa_str_cal = f"+{abs(sisa_cal)} lebih" if sisa_cal < 0 else f"{sisa_cal} sisa"
    sisa_str_prot = f"+{abs(sisa_prot):.1f}g lebih" if sisa_prot < 0 else f"{sisa_prot:.1f}g sisa"

    return (
        f"📊 *Ringkasan hari ini, {name}!*\n\n"
        f"🍽️ *Makanan yang tercatat:*\n"
        f"{food_list}\n\n"
        f"📈 *Progress nutrisi:*\n"
        f"🔥 Kalori: `{bar_cal}` {total_cal}/{target_cal} kkal _{sisa_str_cal}_\n"
        f"💪 Protein: `{bar_prot}` {total_prot}g/{target_prot}g _{sisa_str_prot}_\n"
        f"🍚 Karbo: {total_carbs}g\n"
        f"🥑 Lemak: {total_fat}g\n\n"
        f"{status}"
    )


async def handle_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /summary dan /today."""
    telegram_id = update.effective_user.id

    # Verifikasi user terdaftar
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text(
            "⚠️ Kamu belum terdaftar! Ketik /start untuk setup profil dulu ya."
        )
        return

    # Ambil ringkasan hari ini
    summary = db.get_today_summary(user["id"])
    message = _format_summary(user, summary)

    await update.message.reply_text(message, parse_mode="Markdown")
