"""
bot/handlers/start.py

Handler untuk command /start dan alur onboarding bilingual (Bahasa Indonesia & English).
Dilengkapi Kalkulator Gizi Otomatis berbasis standar medis (Mifflin-St Jeor & BJSM 2018).
"""

from typing import Any
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
(
    ASK_LANGUAGE,
    ASK_NAME,
    ASK_WEIGHT,
    ASK_HEIGHT,
    ASK_TARGET_MODE,
    ASK_GENDER,
    ASK_AGE,
    ASK_ACTIVITY,
    ASK_GOAL,
    CONFIRM_CALC,
    ASK_CALORIES,
    ASK_PROTEIN,
) = range(12)


def calculate_nutrition_targets(
    gender: str,
    weight_kg: float,
    height_cm: float,
    age: int,
    activity_multiplier: float,
    goal: str,
) -> dict[str, int]:
    """
    Menghitung BMR, TDEE, Target Kalori, dan Target Protein berbasis sains gizi:
    - BMR: Mifflin-St Jeor Equation (AJCN, 1990)
    - TDEE: WHO/FAO Physical Activity Level Multiplier (2004)
    - Protein: British Journal of Sports Medicine Meta-Analysis (2018) @ 1.8g/kg BB
    - Goal: Defisit 400 kkal (Fat loss) / Maintenance (TDEE) / Surplus 300 kkal (Hypertrophy)
    """
    if gender.lower().startswith("f") or gender.lower() == "female":
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5

    bmr_val = max(500, int(round(bmr)))
    tdee_val = int(round(bmr_val * activity_multiplier))

    if goal == "deficit":
        target_calories = max(1200, tdee_val - 400)
    elif goal == "surplus":
        target_calories = tdee_val + 300
    else:
        target_calories = tdee_val

    target_protein = max(50, int(round(weight_kg * 1.8)))

    return {
        "bmr": bmr_val,
        "tdee": tdee_val,
        "target_calories": target_calories,
        "target_protein": target_protein,
    }


def _get_onboarding_lang_keyboard() -> InlineKeyboardMarkup:
    """Tombol pemilihan bahasa khusus onboarding."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇮🇩 Bahasa Indonesia", callback_data="onboard_lang:id"),
            InlineKeyboardButton("🇬🇧 English", callback_data="onboard_lang:en"),
        ]
    ])


def _get_target_mode_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Tombol memilih antara kalkulator otomatis atau input manual."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_auto_calc", lang), callback_data="onboard_mode:auto")],
        [InlineKeyboardButton(t("btn_manual_input", lang), callback_data="onboard_mode:manual")],
    ])


def _get_gender_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Tombol memilih gender biologis untuk rumus BMR."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(t("btn_male", lang), callback_data="onboard_gender:male"),
            InlineKeyboardButton(t("btn_female", lang), callback_data="onboard_gender:female"),
        ]
    ])


def _get_activity_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Tombol memilih level aktivitas fisik WHO."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_act_sedentary", lang), callback_data="onboard_act:1.2")],
        [InlineKeyboardButton(t("btn_act_light", lang), callback_data="onboard_act:1.375")],
        [InlineKeyboardButton(t("btn_act_moderate", lang), callback_data="onboard_act:1.55")],
        [InlineKeyboardButton(t("btn_act_heavy", lang), callback_data="onboard_act:1.725")],
    ])


def _get_goal_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Tombol memilih tujuan fitness harian."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_goal_deficit", lang), callback_data="onboard_goal:deficit")],
        [InlineKeyboardButton(t("btn_goal_maintain", lang), callback_data="onboard_goal:maintain")],
        [InlineKeyboardButton(t("btn_goal_surplus", lang), callback_data="onboard_goal:surplus")],
    ])


def _get_confirm_calc_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Tombol konfirmasi hasil kalkulasi gizi otomatis."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_confirm_calc", lang), callback_data="onboard_confirm:yes")],
        [InlineKeyboardButton(t("btn_edit_manual", lang), callback_data="onboard_confirm:manual")],
    ])


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
        if weight <= 20 or weight >= 300:
            raise ValueError()
        context.user_data["weight_kg"] = weight
    except ValueError:
        await update.message.reply_text(t("invalid_weight", lang), parse_mode="Markdown")
        return ASK_WEIGHT

    msg = t("ask_height", lang)
    await update.message.reply_text(msg, parse_mode="Markdown")
    return ASK_HEIGHT


async def received_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima tinggi badan dan tampilkan pilihan mode penentuan target (Otomatis / Manual)."""
    lang = context.user_data.get("language", "id")
    try:
        height = float(update.message.text.strip().replace(",", "."))
        if height <= 50 or height >= 260:
            raise ValueError()
        context.user_data["height_cm"] = height
    except ValueError:
        await update.message.reply_text(t("invalid_height", lang), parse_mode="Markdown")
        return ASK_HEIGHT

    # Tanyakan apakah ingin hitung otomatis atau input manual
    msg = t("choose_target_mode", lang)
    await update.message.reply_text(
        msg,
        reply_markup=_get_target_mode_keyboard(lang),
        parse_mode="Markdown",
    )
    return ASK_TARGET_MODE


async def received_target_mode_choice(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Menerima pilihan mode: Auto Calculate vs Manual Input."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    lang = context.user_data.get("language", "id")
    mode = data.split(":")[1] if data.startswith("onboard_mode:") else "auto"

    if mode == "auto":
        # Masuk ke alur kalkulator ilmiah: Tanya gender
        prompt = t("ask_gender", lang)
        await query.edit_message_text(
            prompt,
            reply_markup=_get_gender_keyboard(lang),
            parse_mode="Markdown",
        )
        return ASK_GENDER
    else:
        # Masuk ke alur manual: Tanya kalori langsung
        msg = t("ask_calories", lang)
        await query.edit_message_text(msg, parse_mode="Markdown")
        return ASK_CALORIES


async def received_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima gender dan tanya usia."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    gender = data.split(":")[1] if data.startswith("onboard_gender:") else "male"
    context.user_data["gender"] = gender
    lang = context.user_data.get("language", "id")

    msg = t("ask_age", lang)
    await query.edit_message_text(msg, parse_mode="Markdown")
    return ASK_AGE


async def received_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima usia dan tanya tingkat aktivitas fisik."""
    lang = context.user_data.get("language", "id")
    try:
        age = int(update.message.text.strip())
        if age < 10 or age > 110:
            raise ValueError()
        context.user_data["age"] = age
    except ValueError:
        await update.message.reply_text(t("invalid_age", lang), parse_mode="Markdown")
        return ASK_AGE

    msg = t("ask_activity", lang)
    await update.message.reply_text(
        msg,
        reply_markup=_get_activity_keyboard(lang),
        parse_mode="Markdown",
    )
    return ASK_ACTIVITY


async def received_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima tingkat aktivitas dan tanya tujuan fitness."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    multiplier_str = data.split(":")[1] if data.startswith("onboard_act:") else "1.375"
    context.user_data["activity_multiplier"] = float(multiplier_str)
    lang = context.user_data.get("language", "id")

    msg = t("ask_goal", lang)
    await query.edit_message_text(
        msg,
        reply_markup=_get_goal_keyboard(lang),
        parse_mode="Markdown",
    )
    return ASK_GOAL


async def received_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hitung target nutrisi secara ilmiah dan tampilkan preview ke pengguna."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    goal = data.split(":")[1] if data.startswith("onboard_goal:") else "deficit"
    context.user_data["goal"] = goal
    lang = context.user_data.get("language", "id")

    # Eksekusi rumus ilmiah Mifflin-St Jeor & BJSM 2018
    calc = calculate_nutrition_targets(
        gender=context.user_data.get("gender", "male"),
        weight_kg=context.user_data.get("weight_kg", 70.0),
        height_cm=context.user_data.get("height_cm", 170.0),
        age=context.user_data.get("age", 25),
        activity_multiplier=context.user_data.get("activity_multiplier", 1.375),
        goal=goal,
    )

    context.user_data["target_calories"] = calc["target_calories"]
    context.user_data["target_protein"] = calc["target_protein"]

    # Ambil deskripsi tujuan
    goal_desc_key = f"goal_desc_{goal}"
    goal_desc = t(goal_desc_key, lang)

    summary_text = t(
        "calc_result",
        lang,
        bmr=calc["bmr"],
        tdee=calc["tdee"],
        target_cal=calc["target_calories"],
        target_prot=calc["target_protein"],
        goal_desc=goal_desc,
    )

    await query.edit_message_text(
        summary_text,
        reply_markup=_get_confirm_calc_keyboard(lang),
        parse_mode="Markdown",
    )
    return CONFIRM_CALC


async def received_confirm_calc(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Menerima konfirmasi hasil kalkulator: Simpan vs Ubah Manual."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    lang = context.user_data.get("language", "id")
    action = data.split(":")[1] if data.startswith("onboard_confirm:") else "yes"

    if action == "yes":
        return await _save_user_profile(update, context)
    else:
        msg = t("ask_calories", lang)
        await query.edit_message_text(msg, parse_mode="Markdown")
        return ASK_CALORIES


# ── Alur Manual / Fallback ───────────────────────────────────────────────────

async def received_calories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima target kalori manual dan tanya target protein."""
    lang = context.user_data.get("language", "id")
    try:
        calories = int(update.message.text.strip())
        if calories <= 500 or calories >= 10000:
            raise ValueError()
        context.user_data["target_calories"] = calories
    except ValueError:
        await update.message.reply_text(t("invalid_calories", lang), parse_mode="Markdown")
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
    """Terima target protein manual dan simpan profil user ke database."""
    lang = context.user_data.get("language", "id")
    try:
        protein = int(update.message.text.strip())
        if protein <= 10 or protein >= 500:
            raise ValueError()
        context.user_data["target_protein"] = protein
    except ValueError:
        await update.message.reply_text(t("invalid_protein", lang), parse_mode="Markdown")
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

    name = data.get("name", update.effective_user.first_name or "User")
    target_cal = data.get("target_calories", 2000)
    target_prot = data.get("target_protein", 150)

    try:
        db.create_user(
            telegram_id=telegram_id,
            name=name,
            weight_kg=data.get("weight_kg", 70.0),
            height_cm=data.get("height_cm", 170.0),
            target_calories=target_cal,
            target_protein=target_prot,
            language=lang,
        )

        welcome_msg = t(
            "profile_saved",
            lang,
            name=name,
            target_cal=target_cal,
            target_prot=target_prot,
        )
        
        # Cek apakah dipanggil dari callback_query atau message biasa
        if update.callback_query:
            await update.callback_query.edit_message_text(welcome_msg, parse_mode="Markdown")
        else:
            await update.message.reply_text(welcome_msg, parse_mode="Markdown")

    except Exception as e:
        err_msg = f"⚠️ Terjadi kesalahan / An error occurred: {e}. Ketik /start untuk coba lagi."
        if update.callback_query:
            await update.callback_query.edit_message_text(err_msg)
        else:
            await update.message.reply_text(err_msg)

    return ConversationHandler.END


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel proses onboarding."""
    lang = context.user_data.get("language", "id")
    msg = t("onboarding_cancelled", lang)
    await update.message.reply_text(msg)
    return ConversationHandler.END


def get_onboarding_handler() -> ConversationHandler:
    """Buat ConversationHandler untuk alur onboarding bilingual dengan Auto Calculator."""
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
            ASK_TARGET_MODE: [
                CallbackQueryHandler(received_target_mode_choice, pattern=r"^onboard_mode:"),
            ],
            ASK_GENDER: [
                CallbackQueryHandler(received_gender, pattern=r"^onboard_gender:"),
            ],
            ASK_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_age)
            ],
            ASK_ACTIVITY: [
                CallbackQueryHandler(received_activity, pattern=r"^onboard_act:"),
            ],
            ASK_GOAL: [
                CallbackQueryHandler(received_goal, pattern=r"^onboard_goal:"),
            ],
            CONFIRM_CALC: [
                CallbackQueryHandler(received_confirm_calc, pattern=r"^onboard_confirm:"),
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
        per_message=False,
    )
