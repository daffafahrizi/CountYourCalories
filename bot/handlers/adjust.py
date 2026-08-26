"""
bot/handlers/adjust.py

Handler untuk perintah quick adjustment (Bilingual):
- /undo — hapus entry terakhir
- /hapus <nama> — hapus entry by nama
- /settarget — update target kalori dan protein (Mendukung shortcut dan Wizard Kalkulator Ilmiah)
- /help — panduan lengkap
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.db import supabase as db
from bot.handlers.start import calculate_nutrition_targets
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


# ── /settarget (Shortcut + Interactive Wizard) ───────────────────────────────

def _get_recalc_gender_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_male", lang), callback_data="recalc:gender:male"),
            InlineKeyboardButton(t("btn_female", lang), callback_data="recalc:gender:female"),
        ],
        [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
    ])


def _get_recalc_age_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_age_group_1", lang), callback_data="recalc:age:18"),
            InlineKeyboardButton(t("btn_age_group_2", lang), callback_data="recalc:age:25"),
        ],
        [
            InlineKeyboardButton(t("btn_age_group_3", lang), callback_data="recalc:age:35"),
            InlineKeyboardButton(t("btn_age_group_4", lang), callback_data="recalc:age:45"),
        ],
        [InlineKeyboardButton(t("btn_age_group_5", lang), callback_data="recalc:age:55")],
        [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
    ])


def _get_recalc_activity_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_act_sedentary", lang), callback_data="recalc:act:1.2")],
        [InlineKeyboardButton(t("btn_act_light", lang), callback_data="recalc:act:1.375")],
        [InlineKeyboardButton(t("btn_act_moderate", lang), callback_data="recalc:act:1.55")],
        [InlineKeyboardButton(t("btn_act_heavy", lang), callback_data="recalc:act:1.725")],
        [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
    ])


def _get_recalc_goal_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_goal_deficit", lang), callback_data="recalc:goal:deficit")],
        [InlineKeyboardButton(t("btn_goal_maintain", lang), callback_data="recalc:goal:maintain")],
        [InlineKeyboardButton(t("btn_goal_surplus", lang), callback_data="recalc:goal:surplus")],
        [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
    ])


def _get_recalc_confirm_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_recalc_apply", lang), callback_data="recalc:apply")],
        [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
    ])


async def handle_settarget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk /settarget:
    1. Shortcut: /settarget 2000 150 -> langsung update.
    2. Interactive Wizard: /settarget (tanpa argumen) -> buka menu kalkulator ilmiah.
    """
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if not user:
        tg_lang = update.effective_user.language_code or "id"
        await update.message.reply_text(t("not_registered", tg_lang))
        return

    lang = user.get("language", "id")

    # Mode 1: Shortcut dengan 2 argumen (/settarget <kalori> <protein>)
    if context.args and len(context.args) >= 2:
        try:
            new_calories = int(context.args[0])
            new_protein = int(context.args[1])
            if new_calories <= 500 or new_calories >= 10000 or new_protein <= 10 or new_protein >= 500:
                raise ValueError()
        except ValueError:
            await update.message.reply_text(t("settarget_invalid", lang), parse_mode="Markdown")
            return

        db.update_user_targets(
            telegram_id=telegram_id,
            target_calories=new_calories,
            target_protein=new_protein,
        )
        msg = t("settarget_success", lang, calories=new_calories, protein=new_protein)
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # Mode 2: Interactive Wizard Menu
    weight = user.get("weight_kg", 70.0)
    height = user.get("height_cm", 170.0)
    current_cal = user.get("target_calories", 2000)
    current_prot = user.get("target_protein", 150)

    menu_text = t(
        "settarget_menu",
        lang,
        weight=weight,
        height=height,
        current_cal=current_cal,
        current_prot=current_prot,
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_recalc_start", lang), callback_data="recalc:start")],
        [InlineKeyboardButton(t("btn_recalc_manual", lang), callback_data="recalc:manual")],
        [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
    ])

    await update.message.reply_text(menu_text, reply_markup=keyboard, parse_mode="Markdown")


async def handle_recalc_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Menangani alur interaktif kalkulator gizi saat user klik tombol di /settarget.
    """
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        return

    lang = user.get("language", "id")
    data = query.data or ""

    if data == "recalc:cancel":
        await query.edit_message_text(t("recalc_cancelled", lang))
        return

    if data == "recalc:menu":
        # Kembali ke menu utama /settarget
        weight = user.get("weight_kg", 70.0)
        height = user.get("height_cm", 170.0)
        current_cal = user.get("target_calories", 2000)
        current_prot = user.get("target_protein", 150)

        menu_text = t(
            "settarget_menu",
            lang,
            weight=weight,
            height=height,
            current_cal=current_cal,
            current_prot=current_prot,
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t("btn_recalc_start", lang), callback_data="recalc:start")],
            [InlineKeyboardButton(t("btn_recalc_manual", lang), callback_data="recalc:manual")],
            [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
        ])
        await query.edit_message_text(menu_text, reply_markup=keyboard, parse_mode="Markdown")
        return

    if data == "recalc:manual":
        # Tampilkan panduan cara input manual
        guide_text = t("recalc_manual_guide", lang)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t("btn_back", lang), callback_data="recalc:menu")],
            [InlineKeyboardButton(t("btn_recalc_cancel", lang), callback_data="recalc:cancel")],
        ])
        await query.edit_message_text(guide_text, reply_markup=keyboard, parse_mode="Markdown")
        return

    if data == "recalc:start":
        # Langkah 1: Tanya Gender
        await query.edit_message_text(
            t("ask_gender", lang),
            reply_markup=_get_recalc_gender_kb(lang),
            parse_mode="Markdown",
        )
        return

    if data.startswith("recalc:gender:"):
        gender = data.split(":")[2]
        context.user_data["recalc_gender"] = gender

        # Langkah 2: Tanya Usia (dengan tombol kelompok usia cepat)
        await query.edit_message_text(
            t("recalc_age_prompt", lang),
            reply_markup=_get_recalc_age_kb(lang),
            parse_mode="Markdown",
        )
        return

    if data.startswith("recalc:age:"):
        age = int(data.split(":")[2])
        context.user_data["recalc_age"] = age

        # Langkah 3: Tanya Tingkat Aktivitas
        await query.edit_message_text(
            t("ask_activity", lang),
            reply_markup=_get_recalc_activity_kb(lang),
            parse_mode="Markdown",
        )
        return

    if data.startswith("recalc:act:"):
        multiplier = float(data.split(":")[2])
        context.user_data["recalc_act"] = multiplier

        # Langkah 4: Tanya Tujuan Fitness
        await query.edit_message_text(
            t("ask_goal", lang),
            reply_markup=_get_recalc_goal_kb(lang),
            parse_mode="Markdown",
        )
        return

    if data.startswith("recalc:goal:"):
        goal = data.split(":")[2]
        context.user_data["recalc_goal"] = goal

        weight = float(user.get("weight_kg", 70.0))
        height = float(user.get("height_cm", 170.0))
        gender = context.user_data.get("recalc_gender", "male")
        age = context.user_data.get("recalc_age", 25)
        act = context.user_data.get("recalc_act", 1.375)

        # Hitung dengan rumus Mifflin-St Jeor & BJSM 2018
        res = calculate_nutrition_targets(
            gender=gender,
            weight_kg=weight,
            height_cm=height,
            age=age,
            activity_multiplier=act,
            goal=goal,
        )

        context.user_data["recalc_new_cal"] = res["target_calories"]
        context.user_data["recalc_new_prot"] = res["target_protein"]

        goal_desc = t(f"goal_desc_{goal}", lang)

        summary_msg = t(
            "calc_result",
            lang,
            bmr=res["bmr"],
            tdee=res["tdee"],
            target_cal=res["target_calories"],
            target_prot=res["target_protein"],
            goal_desc=goal_desc,
        )

        await query.edit_message_text(
            summary_msg,
            reply_markup=_get_recalc_confirm_kb(lang),
            parse_mode="Markdown",
        )
        return

    if data == "recalc:apply":
        new_cal = context.user_data.get("recalc_new_cal", 2000)
        new_prot = context.user_data.get("recalc_new_prot", 150)

        db.update_user_targets(
            telegram_id=telegram_id,
            target_calories=new_cal,
            target_protein=new_prot,
        )

        msg = t("settarget_success", lang, calories=new_cal, protein=new_prot)
        await query.edit_message_text(msg, parse_mode="Markdown")
        return
