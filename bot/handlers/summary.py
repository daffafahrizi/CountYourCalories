"""
bot/handlers/summary.py

Handler untuk ringkasan nutrisi harian (/summary, /today) dengan navigasi tanggal interaktif,
serta laporan mingguan (/weekly, /mingguan) dengan evaluasi AI Nutrition Coach (Bilingual).
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.agent.core import process_text_message
from bot.db import supabase as db
from bot.locales import t

# Kamus nama hari dan bulan untuk formatting tanggal
DAY_NAMES = {
    "id": ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}

DAY_ABBR = {
    "id": ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}

MONTH_ABBR = {
    "id": ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def _get_day_name(target_date: date, lang: str) -> str:
    lang_key = "en" if lang.startswith("en") else "id"
    return DAY_NAMES[lang_key][target_date.weekday()]


def _get_day_abbr(target_date: date, lang: str) -> str:
    lang_key = "en" if lang.startswith("en") else "id"
    return DAY_ABBR[lang_key][target_date.weekday()]


def _get_month_abbr(month_idx: int, lang: str) -> str:
    lang_key = "en" if lang.startswith("en") else "id"
    return MONTH_ABBR[lang_key][month_idx - 1]


def _format_date_str(target_date: date, lang: str) -> str:
    day_name = _get_day_name(target_date, lang)
    month_str = _get_month_abbr(target_date.month, lang)
    return f"{day_name}, {target_date.day} {month_str} {target_date.year}"


def _progress_bar(current: int, target: int, length: int = 10) -> str:
    """Buat progress bar visual."""
    if target <= 0:
        return "░" * length
    filled = min(int((current / target) * length), length)
    return "█" * filled + "░" * (length - filled)


def _get_summary_date_keyboard(target_date: date, lang: str) -> InlineKeyboardMarkup:
    """Membuat keyboard navigasi tanggal untuk /summary."""
    today = datetime.now().astimezone().date()
    yesterday = today - timedelta(days=1)

    prev_d = target_date - timedelta(days=1)
    next_d = target_date + timedelta(days=1)

    # Label tombol kemarin/sebelumnya
    if prev_d == yesterday:
        prev_label = t("day_yesterday", lang)
    else:
        prev_label = f"{prev_d.day} {_get_month_abbr(prev_d.month, lang)}"

    btn_prev = InlineKeyboardButton(
        t("btn_prev_day", lang, date_label=prev_label),
        callback_data=f"summary_date:{prev_d.isoformat()}",
    )

    buttons_row = [btn_prev]

    # Tombol Hari Ini (jika sedang melihat hari lalu)
    if target_date != today:
        buttons_row.append(
            InlineKeyboardButton(
                t("btn_today", lang),
                callback_data=f"summary_date:{today.isoformat()}",
            )
        )

    # Tombol Besok (hanya jika target_date < today)
    if target_date < today:
        if next_d == today:
            next_label = t("day_today", lang)
        else:
            next_label = f"{next_d.day} {_get_month_abbr(next_d.month, lang)}"

        buttons_row.append(
            InlineKeyboardButton(
                t("btn_next_day", lang, date_label=next_label),
                callback_data=f"summary_date:{next_d.isoformat()}",
            )
        )

    return InlineKeyboardMarkup([
        buttons_row,
        [InlineKeyboardButton("📊 Laporan Mingguan (/weekly)" if not lang.startswith("en") else "📊 Weekly Report (/weekly)", callback_data="summary_open_weekly")],
    ])


def _format_summary(user: dict, summary: dict, target_date: Optional[date] = None) -> str:
    """Format ringkasan nutrisi menjadi pesan Telegram dwibahasa yang rapi."""
    lang = user.get("language", "id")
    name = user["name"]
    target_cal = user["target_calories"]
    target_prot = user["target_protein"]

    today = datetime.now().astimezone().date()
    is_today = (target_date is None) or (target_date == today)
    display_date = target_date or today

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

    # Status pesan berdasarkan progress protein (khusus hari ini)
    if is_today:
        persen_prot = (total_prot / target_prot * 100) if target_prot > 0 else 0
        if persen_prot >= 100:
            status = t("status_protein_100", lang)
        elif persen_prot >= 75:
            status = t("status_protein_75", lang)
        elif persen_prot >= 50:
            status = t("status_protein_50", lang)
        else:
            status = t("status_protein_low", lang)
    else:
        status = ""

    # Format daftar makanan
    if entries:
        food_list = "\n".join(
            f"  • {e['meal_name']} — {e['calories']} kcal (P:{e['protein_g']}g)"
            for e in entries
        )
    else:
        food_list = t("summary_no_meals", lang) if is_today else t("summary_no_meals_date", lang)

    # Format teks sisa / lebih
    if sisa_cal < 0:
        sisa_str_cal = t("summary_over", lang, lebih=abs(sisa_cal))
    else:
        sisa_str_cal = t("summary_remaining", lang, sisa=sisa_cal)

    if sisa_prot < 0:
        sisa_str_prot = t("summary_over_prot", lang, lebih=f"{abs(sisa_prot):.1f}")
    else:
        sisa_str_prot = t("summary_remaining_prot", lang, sisa=f"{sisa_prot:.1f}")

    if is_today:
        header = t("summary_title", lang, name=name)
    else:
        date_str = _format_date_str(display_date, lang)
        header = t("summary_date_title", lang, date_str=date_str, name=name)

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

    res = (
        f"{header}\n\n"
        f"{logged_label}\n"
        f"{food_list}\n\n"
        f"{progress_label}\n"
        f"{cal_line}\n"
        f"{prot_line}\n"
        f"{carbs_line}\n"
        f"{fat_line}"
    )
    if status:
        res += f"\n\n{status}"

    return res


async def handle_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk /summary dan /today:
    - /summary (hari ini)
    - /summary kemarin / /summary yesterday (kemarin)
    - /summary YYYY-MM-DD (tanggal tertentu)
    """
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        tg_lang = update.effective_user.language_code or "id"
        await update.message.reply_text(t("not_registered", tg_lang))
        return

    lang = user.get("language", "id")
    today = datetime.now().astimezone().date()
    target_date = today

    # Cek apakah ada argumen tanggal
    if context.args:
        arg = context.args[0].strip().lower()
        if arg in ["kemarin", "yesterday"]:
            target_date = today - timedelta(days=1)
        else:
            try:
                target_date = datetime.strptime(arg, "%Y-%m-%d").date()
                if target_date > today:
                    target_date = today
            except ValueError:
                target_date = today

    summary = db.get_date_summary(user["id"], target_date)
    message = _format_summary(user, summary, target_date)
    keyboard = _get_summary_date_keyboard(target_date, lang)

    await update.message.reply_text(message, reply_markup=keyboard, parse_mode="Markdown")


async def handle_summary_date_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handler callback saat user mengklik tombol navigasi tanggal di /summary."""
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        return

    lang = user.get("language", "id")
    data = query.data or ""

    if data == "summary_open_weekly":
        # Redirect ke handler weekly
        await handle_weekly(update, context)
        return

    if data.startswith("summary_date:"):
        date_str = data.split(":")[1]
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now().astimezone().date()

        summary = db.get_date_summary(user["id"], target_date)
        message = _format_summary(user, summary, target_date)
        keyboard = _get_summary_date_keyboard(target_date, lang)

        try:
            await query.edit_message_text(
                message, reply_markup=keyboard, parse_mode="Markdown"
            )
        except Exception:
            pass


# ── Laporan Mingguan (/weekly & /mingguan) ────────────────────────────────────

async def handle_weekly(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk /weekly dan /mingguan:
    1. Mengambil data 7 hari terakhir dari Supabase.
    2. Menghitung rata-rata kalori, protein, dan persentase kepatuhan.
    3. Menyusun grafik batang 7 hari (Senin–Minggu).
    4. Menghasilkan evaluasi personal dari AI Nutrition Coach via Gemini/fallback.
    """
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        tg_lang = update.effective_user.language_code or "id"
        if update.message:
            await update.message.reply_text(t("not_registered", tg_lang))
        return

    lang = user.get("language", "id")
    name = user["name"]
    target_cal = user.get("target_calories", 2000)
    target_prot = user.get("target_protein", 150)

    # Kirim loading message jika dipanggil via command
    loading_msg = None
    if update.message:
        loading_msg = await update.message.reply_text(
            t("weekly_loading", lang), parse_mode="Markdown"
        )
    elif update.callback_query:
        loading_msg = await update.callback_query.edit_message_text(
            t("weekly_loading", lang), parse_mode="Markdown"
        )

    # Ambil 7 hari riwayat
    history = db.get_weekly_history(user["id"], days=7)
    start_date = history[0]["date"]
    end_date = history[-1]["date"]

    start_str = f"{start_date.day} {_get_month_abbr(start_date.month, lang)}"
    end_str = f"{end_date.day} {_get_month_abbr(end_date.month, lang)} {end_date.year}"
    period_str = f"{start_str} – {end_str}"

    total_cal_all = sum(d["total_calories"] for d in history)
    total_prot_all = sum(d["total_protein"] for d in history)
    logged_days_count = sum(1 for d in history if d["total_calories"] > 0)

    # Hitung rata-rata
    divisor = logged_days_count if logged_days_count > 0 else 1
    avg_cal = round(total_cal_all / divisor)
    avg_prot = round(total_prot_all / divisor, 1)

    # Kepatuhan target (hari di mana kalori tercatat & dalam rentang wajar +/- 10% atau protein >= 80%)
    met_days = 0
    for d in history:
        cal = d["total_calories"]
        if cal > 0 and cal <= (target_cal * 1.15):
            met_days += 1

    percent_compliance = round((met_days / 7) * 100)

    # Susun grafik 7 hari
    chart_lines = []
    for d in history:
        d_date = d["date"]
        d_day = _get_day_abbr(d_date, lang)
        d_cal = d["total_calories"]
        bar = _progress_bar(d_cal, target_cal, length=8)

        if d_cal == 0:
            badge = "⚪"
        elif d_cal <= target_cal * 1.05:
            badge = "✅"
        else:
            badge = "⚠️"

        day_label = f"{d_day} ({d_date.day})"
        chart_lines.append(f"• `{day_label:<7}` `{bar}` {d_cal} kkal {badge}")

    chart_text = "\n".join(chart_lines)

    # Request masukan personal dari AI Coach
    ai_prompt_data = (
        f"Data 7 hari user {name}: Target={target_cal} kkal, Protein={target_prot}g. "
        f"Rata-rata kalori tercatat={avg_cal} kkal, Rata-rata protein={avg_prot}g. "
        f"Kepatuhan={met_days}/7 hari. "
        f"Hari-hari kalori: {[(d['date'].strftime('%a'), d['total_calories']) for d in history]}. "
        f"Berikan 1-2 kalimat feedback singkat, ramah, dan solutif sebagai AI Nutrition Coach untuk evaluasi minggu ini."
    )

    user_context = (
        f"user_id={user['id']}, "
        f"telegram_id={user['telegram_id']}, "
        f"nama={user['name']}, "
        f"target_kalori={target_cal} kkal, "
        f"target_protein={target_prot}g, "
        f"bahasa={lang}"
    )

    try:
        coach_feedback = await asyncio.wait_for(
            process_text_message(
                user_message=ai_prompt_data,
                user_context=user_context,
                language=lang,
            ),
            timeout=20.0,
        )
        coach_feedback = coach_feedback.strip()
    except Exception:
        coach_feedback = t("weekly_coach_fallback", lang)

    # Susun pesan laporan mingguan final
    title = t("weekly_title", lang, period=period_str, name=name)
    avg_title = t("weekly_averages_title", lang)
    avg_cal_line = t("weekly_avg_cal", lang, avg_cal=avg_cal, target_cal=target_cal)
    avg_prot_line = t("weekly_avg_prot", lang, avg_prot=avg_prot, target_prot=target_prot)
    comp_line = t("weekly_compliance", lang, met_days=met_days, total_days=7, percent=percent_compliance)
    chart_hdr = t("weekly_chart_header", lang)
    coach_hdr = t("weekly_ai_coach_header", lang)

    final_report = (
        f"{title}\n\n"
        f"{avg_title}\n"
        f"{avg_cal_line}\n"
        f"{avg_prot_line}\n"
        f"{comp_line}\n\n"
        f"{chart_hdr}\n"
        f"{chart_text}\n\n"
        f"{coach_hdr}\n"
        f"_{coach_feedback}_"
    )

    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📅 Kembali ke Hari Ini" if not lang.startswith("en") else "📅 Back to Today", callback_data=f"summary_date:{end_date.isoformat()}")]
    ])

    if loading_msg:
        try:
            await loading_msg.edit_text(final_report, reply_markup=back_kb, parse_mode="Markdown")
        except Exception:
            await loading_msg.edit_text(final_report, reply_markup=back_kb)
    elif update.message:
        await update.message.reply_text(final_report, reply_markup=back_kb, parse_mode="Markdown")
