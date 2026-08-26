"""
bot/handlers/adjust.py

Handler untuk perintah quick adjustment:
- /undo — hapus entry terakhir
- /hapus <nama> — hapus entry by nama
- /help — bantuan
"""

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import supabase as db


async def handle_undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /undo — menghapus entry makanan terakhir hari ini."""
    telegram_id = update.effective_user.id

    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text(
            "⚠️ Kamu belum terdaftar! Ketik /start untuk setup profil dulu ya."
        )
        return

    last = db.get_last_log(user["id"])
    if not last:
        await update.message.reply_text(
            "📭 Tidak ada entry makanan hari ini yang bisa dihapus."
        )
        return

    db.delete_log_by_id(last["id"])

    # Tampilkan sisa setelah undo
    summary = db.get_today_summary(user["id"])
    await update.message.reply_text(
        f"↩️ *Entry dihapus!*\n\n"
        f"❌ *{last['meal_name']}* ({last['calories']} kkal) telah dihapus.\n\n"
        f"📊 *Sisa hari ini:*\n"
        f"🔥 Kalori: {summary['total_calories']}/{user['target_calories']} kkal\n"
        f"💪 Protein: {summary['total_protein']}g/{user['target_protein']}g",
        parse_mode="Markdown",
    )


async def handle_hapus(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk /hapus <nama_makanan>.
    Contoh: /hapus nasi goreng
    """
    telegram_id = update.effective_user.id

    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text(
            "⚠️ Kamu belum terdaftar! Ketik /start untuk setup profil dulu ya."
        )
        return

    # Ambil nama makanan dari argumen command
    if not context.args:
        await update.message.reply_text(
            "ℹ️ Penggunaan: `/hapus <nama makanan>`\n"
            "Contoh: `/hapus nasi goreng`",
            parse_mode="Markdown",
        )
        return

    meal_name = " ".join(context.args)
    count = db.delete_logs_by_name(user["id"], meal_name)

    if count == 0:
        await update.message.reply_text(
            f"❓ Tidak ditemukan entry dengan nama *'{meal_name}'* hari ini.\n\n"
            f"Gunakan /summary untuk melihat daftar makanan yang sudah tercatat.",
            parse_mode="Markdown",
        )
        return

    summary = db.get_today_summary(user["id"])
    await update.message.reply_text(
        f"🗑️ *{count} entry dihapus!*\n\n"
        f"❌ Semua entry yang mengandung *'{meal_name}'* telah dihapus.\n\n"
        f"📊 *Sisa hari ini:*\n"
        f"🔥 Kalori: {summary['total_calories']}/{user['target_calories']} kkal\n"
        f"💪 Protein: {summary['total_protein']}g/{user['target_protein']}g",
        parse_mode="Markdown",
    )


async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /help — menampilkan semua perintah yang tersedia."""
    await update.message.reply_text(
        "🤖 *CountYourCalories — Panduan Penggunaan*\n\n"
        "*📸 Mencatat Makanan:*\n"
        "  • Kirim *foto makanan* → Bot otomatis analisis & catat\n"
        "  • /catat `<makanan>` → Catat manual via teks\n"
        "    Contoh: `/catat nasi goreng 1 porsi`\n\n"
        "*📊 Melihat Progress:*\n"
        "  • /summary atau /today → Ringkasan nutrisi hari ini\n\n"
        "*✏️ Mengoreksi Entry:*\n"
        "  • /undo → Hapus entry terakhir\n"
        "  • /hapus `<nama>` → Hapus entry by nama\n"
        "    Contoh: `/hapus nasi goreng`\n"
        "  • Ketik perintah natural → Contoh: _'hapus ayam bakar tadi'_\n\n"
        "*⚙️ Pengaturan:*\n"
        "  • /settarget `<kal> <prot>` → Update target\n"
        "    Contoh: `/settarget 2000 150`\n"
        "  • /start → Setup ulang profil\n"
        "  • /help → Tampilkan bantuan ini",
        parse_mode="Markdown",
    )


async def handle_settarget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handler untuk /settarget — update target kalori dan protein.
    Contoh: /settarget 2000 150
    """
    telegram_id = update.effective_user.id

    user = db.get_user_by_telegram_id(telegram_id)
    if not user:
        await update.message.reply_text(
            "⚠️ Kamu belum terdaftar! Ketik /start untuk setup profil dulu ya."
        )
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "ℹ️ Penggunaan: `/settarget <kalori> <protein>`\n"
            "Contoh: `/settarget 2000 150`",
            parse_mode="Markdown",
        )
        return

    try:
        new_calories = int(context.args[0])
        new_protein = int(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "⚠️ Masukkan angka yang valid.\nContoh: `/settarget 2000 150`",
            parse_mode="Markdown",
        )
        return

    db.update_user_targets(
        telegram_id=telegram_id,
        target_calories=new_calories,
        target_protein=new_protein,
    )

    await update.message.reply_text(
        f"✅ *Target berhasil diperbarui!*\n\n"
        f"🔥 Kalori: *{new_calories} kkal/hari*\n"
        f"💪 Protein: *{new_protein}g/hari*",
        parse_mode="Markdown",
    )
