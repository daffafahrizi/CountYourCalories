"""
bot/handlers/start.py

Handler untuk command /start dan alur onboarding pengguna baru.
"""

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.db import supabase as db

# States untuk ConversationHandler onboarding
ASK_NAME, ASK_WEIGHT, ASK_HEIGHT, ASK_CALORIES, ASK_PROTEIN = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point /start — cek apakah user sudah terdaftar atau belum."""
    telegram_id = update.effective_user.id
    user = db.get_user_by_telegram_id(telegram_id)

    if user:
        await update.message.reply_text(
            f"👋 Halo lagi, *{user['name']}*!\n\n"
            f"Kirim foto makananmu atau ketik nama makanan untuk mulai mencatat.\n"
            f"Ketik /help untuk melihat semua perintah yang tersedia.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    # User baru — mulai onboarding
    await update.message.reply_text(
        "🎉 *Selamat datang di CountYourCalories!*\n\n"
        "Aku akan membantumu mencatat kalori dan makronutrisi harian dengan mudah — "
        "cukup kirim foto makananmu!\n\n"
        "Sebelum mulai, aku perlu tahu sedikit tentang kamu. "
        "Kamu bisa skip dengan ketik /skip kapan saja.\n\n"
        "Pertama, *siapa namamu?* 😊",
        parse_mode="Markdown",
    )
    return ASK_NAME


async def received_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima nama user dan tanya berat badan."""
    name = update.message.text.strip()
    context.user_data["name"] = name

    await update.message.reply_text(
        f"Senang bertemu denganmu, *{name}*! 💪\n\n"
        f"Berapa berat badanmu saat ini? _(dalam kg, contoh: 70)_",
        parse_mode="Markdown",
    )
    return ASK_WEIGHT


async def received_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima berat badan dan tanya tinggi badan."""
    try:
        weight = float(update.message.text.strip().replace(",", "."))
        context.user_data["weight_kg"] = weight
    except ValueError:
        await update.message.reply_text(
            "⚠️ Masukkan angka yang valid, contoh: *70* atau *70.5*",
            parse_mode="Markdown",
        )
        return ASK_WEIGHT

    await update.message.reply_text(
        f"Berapa tinggi badanmu? _(dalam cm, contoh: 175)_",
        parse_mode="Markdown",
    )
    return ASK_HEIGHT


async def received_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima tinggi badan dan tanya target kalori."""
    try:
        height = float(update.message.text.strip().replace(",", "."))
        context.user_data["height_cm"] = height
    except ValueError:
        await update.message.reply_text(
            "⚠️ Masukkan angka yang valid, contoh: *175* atau *165.5*",
            parse_mode="Markdown",
        )
        return ASK_HEIGHT

    await update.message.reply_text(
        "🎯 Berapa target *kalori harian* kamu?\n\n"
        "_(contoh: 2000 untuk cutting, 2500 untuk maintenance, 3000 untuk bulking)_\n"
        "Ketik /skip untuk pakai default: *2000 kkal*",
        parse_mode="Markdown",
    )
    return ASK_CALORIES


async def received_calories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima target kalori dan tanya target protein."""
    try:
        calories = int(update.message.text.strip())
        context.user_data["target_calories"] = calories
    except ValueError:
        await update.message.reply_text(
            "⚠️ Masukkan angka yang valid, contoh: *2000*",
            parse_mode="Markdown",
        )
        return ASK_CALORIES

    await update.message.reply_text(
        "💪 Berapa target *protein harian* kamu? _(dalam gram)_\n\n"
        "Untuk strength training, disarankan *1.6–2.2g per kg berat badan*.\n"
        f"Berdasarkan berat badanmu {context.user_data.get('weight_kg', 70)}kg, "
        f"range yang disarankan: "
        f"*{int(context.user_data.get('weight_kg', 70) * 1.6)}–"
        f"{int(context.user_data.get('weight_kg', 70) * 2.2)}g*\n\n"
        "Ketik /skip untuk pakai default: *150g*",
        parse_mode="Markdown",
    )
    return ASK_PROTEIN


async def received_protein(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Terima target protein dan simpan profil user ke database."""
    try:
        protein = int(update.message.text.strip())
        context.user_data["target_protein"] = protein
    except ValueError:
        await update.message.reply_text(
            "⚠️ Masukkan angka yang valid, contoh: *150*",
            parse_mode="Markdown",
        )
        return ASK_PROTEIN

    return await _save_user_profile(update, context)


async def skip_calories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip target kalori, gunakan default 2000."""
    context.user_data["target_calories"] = 2000
    await update.message.reply_text(
        "✅ Oke, target kalori diset ke *2000 kkal*.\n\n"
        "💪 Berapa target *protein harian* kamu? _(dalam gram)_\n"
        "Ketik /skip untuk pakai default: *150g*",
        parse_mode="Markdown",
    )
    return ASK_PROTEIN


async def skip_protein(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip target protein, gunakan default 150g."""
    context.user_data["target_protein"] = 150
    return await _save_user_profile(update, context)


async def _save_user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Helper: simpan profil user ke Supabase dan kirim pesan selamat datang."""
    telegram_id = update.effective_user.id
    data = context.user_data

    try:
        db.create_user(
            telegram_id=telegram_id,
            name=data.get("name", update.effective_user.first_name or "Pengguna"),
            weight_kg=data.get("weight_kg", 70.0),
            height_cm=data.get("height_cm", 170.0),
            target_calories=data.get("target_calories", 2000),
            target_protein=data.get("target_protein", 150),
        )

        name = data.get("name", "")
        target_cal = data.get("target_calories", 2000)
        target_prot = data.get("target_protein", 150)

        await update.message.reply_text(
            f"🎉 *Profil tersimpan! Selamat datang, {name}!*\n\n"
            f"📋 Target harianmu:\n"
            f"  🔥 Kalori: *{target_cal} kkal*\n"
            f"  💪 Protein: *{target_prot}g*\n\n"
            "Sekarang, cukup kirim *foto makananmu* dan aku akan otomatis mencatatnya!\n\n"
            "Perintah yang tersedia:\n"
            "  📸 Kirim foto → Catat dari foto\n"
            "  ✍️ Ketik nama makanan → Catat manual\n"
            "  /summary → Lihat progress hari ini\n"
            "  /undo → Hapus entry terakhir\n"
            "  /help → Bantuan lengkap",
            parse_mode="Markdown",
        )
    except Exception as e:
        await update.message.reply_text(
            "⚠️ Terjadi kesalahan saat menyimpan profil. Coba lagi dengan /start."
        )
        print(f"[ERROR] Gagal menyimpan profil: {e}")

    return ConversationHandler.END


async def cancel_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel proses onboarding."""
    await update.message.reply_text(
        "Onboarding dibatalkan. Ketik /start untuk memulai lagi."
    )
    return ConversationHandler.END


def get_onboarding_handler() -> ConversationHandler:
    """Buat ConversationHandler untuk alur onboarding."""
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
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
