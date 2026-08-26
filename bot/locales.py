"""
bot/locales.py

Kamus teks dan sistem internasionalisasi (i18n) untuk CountYourCalories Bot.
Mendukung Bahasa Indonesia ('id') dan English ('en').
"""

from typing import Any

MESSAGES: dict[str, dict[str, str]] = {
    "id": {
        # ── Onboarding /start ──
        "welcome_existing": (
            "👋 Halo lagi, *{name}*!\n\n"
            "Kirim foto makananmu atau ketik nama makanan untuk mulai mencatat.\n"
            "Ketik /help untuk melihat panduan lengkap atau /lang untuk ganti bahasa."
        ),
        "choose_language": "🌐 *Silakan pilih bahasa / Please select your language:*",
        "lang_selected": "✅ Bahasa diatur ke *Bahasa Indonesia* 🇮🇩",
        "welcome_intro": (
            "🎉 *Selamat datang di CountYourCalories!*\n\n"
            "Aku akan membantumu mencatat kalori dan makronutrisi harian dengan mudah — "
            "cukup kirim foto makananmu!\n\n"
            "Sebelum mulai, aku perlu tahu sedikit tentang kamu. "
            "Kamu bisa skip target dengan ketik /skip kapan saja.\n\n"
            "Pertama, *siapa namamu?* 😊"
        ),
        "ask_weight": (
            "Senang bertemu denganmu, *{name}*! 💪\n\n"
            "Berapa berat badanmu saat ini? _(dalam kg, contoh: 70 atau 65.5)_"
        ),
        "invalid_weight": "⚠️ Masukkan angka yang valid, contoh: *70* atau *65.5*",
        "ask_height": "Berapa tinggi badanmu? _(dalam cm, contoh: 175)_",
        "invalid_height": "⚠️ Masukkan angka yang valid, contoh: *175* atau *168*",
        "ask_calories": (
            "🎯 Berapa target *kalori harian* kamu?\n\n"
            "_(contoh: 2000 untuk cutting, 2500 untuk maintenance, 3000 untuk bulking)_\n"
            "Ketik /skip untuk pakai default: *2000 kkal*"
        ),
        "invalid_calories": "⚠️ Masukkan angka yang valid, contoh: *2000*",
        "ask_protein": (
            "💪 Berapa target *protein harian* kamu? _(dalam gram)_\n\n"
            "Saran untukmu: *{min_prot}–{max_prot}g* (1.6–2.2g per kg BB).\n\n"
            "Ketik /skip untuk pakai default: *150g*"
        ),
        "invalid_protein": "⚠️ Masukkan angka yang valid, contoh: *150*",
        "skip_calories_done": (
            "✅ Oke, target kalori diset ke *2000 kkal*.\n\n"
            "💪 Berapa target *protein harian* kamu? _(dalam gram)_\n"
            "Ketik /skip untuk pakai default: *150g*"
        ),
        "profile_saved": (
            "🎉 *Profil tersimpan! Selamat datang, {name}!*\n\n"
            "📋 Target harianmu:\n"
            "  🔥 Kalori: *{target_cal} kkal*\n"
            "  💪 Protein: *{target_prot}g*\n\n"
            "Sekarang, cukup kirim *foto makananmu* dan aku akan otomatis mencatatnya!\n\n"
            "Perintah yang tersedia:\n"
            "  📸 Kirim foto → Catat dari foto\n"
            "  ✍️ /catat `<makanan>` → Catat manual via teks\n"
            "  /summary → Lihat progress hari ini\n"
            "  /undo → Hapus entry terakhir\n"
            "  /lang → Ganti bahasa (Language)\n"
            "  /help → Panduan lengkap"
        ),
        "onboarding_cancelled": "Onboarding dibatalkan. Ketik /start untuk memulai lagi.",
        "not_registered": "⚠️ Kamu belum terdaftar! Ketik /start untuk setup profil dulu ya.",

        # ── Language Switcher /lang ──
        "lang_switch_prompt": "🌐 *Pilih bahasa antarmuka bot:*",
        "lang_switched_success": "✅ Bahasa berhasil diubah ke *Bahasa Indonesia* 🇮🇩",

        # ── Summary /summary ──
        "summary_title": "📊 *Ringkasan hari ini, {name}!*",
        "summary_logged_meals": "🍽️ *Makanan yang tercatat:*",
        "summary_no_meals": "  _Belum ada makanan yang tercatat hari ini_",
        "summary_nutrition_progress": "📈 *Progress nutrisi:*",
        "summary_cal_line": "🔥 Kalori: `{bar}` {total}/{target} kkal _{sisa}_",
        "summary_prot_line": "💪 Protein: `{bar}` {total}g/{target}g _{sisa}_",
        "summary_carbs_line": "🍚 Karbo: {total}g",
        "summary_fat_line": "🥑 Lemak: {total}g",
        "summary_remaining": "{sisa} kkal sisa",
        "summary_remaining_prot": "{sisa}g sisa",
        "summary_over": "+{lebih} kkal lebih",
        "summary_over_prot": "+{lebih}g lebih",
        "status_protein_100": "🎉 Target protein tercapai! Luar biasa!",
        "status_protein_75": "💪 Hampir sampai target proteinmu, terus semangat!",
        "status_protein_50": "📈 Sudah setengah jalan, pertahankan!",
        "status_protein_low": "🥗 Jangan lupa tingkatkan asupan proteinmu ya!",

        # ── Adjustments (/undo, /hapus, /settarget, /help) ──
        "undo_empty": "📭 Tidak ada entry makanan hari ini yang bisa dihapus.",
        "undo_success": (
            "↩️ *Entry dihapus!*\n\n"
            "❌ *{meal_name}* ({calories} kkal) telah dihapus.\n\n"
            "📊 *Sisa hari ini:*\n"
            "🔥 Kalori: {total_cal}/{target_cal} kkal\n"
            "💪 Protein: {total_prot}g/{target_prot}g"
        ),
        "hapus_usage": (
            "ℹ️ Penggunaan: `/hapus <nama makanan>`\n"
            "Contoh: `/hapus nasi goreng`"
        ),
        "hapus_not_found": (
            "❓ Tidak ditemukan entry dengan nama *'{meal_name}'* hari ini.\n\n"
            "Gunakan /summary untuk melihat daftar makanan yang sudah tercatat."
        ),
        "hapus_success": (
            "🗑️ *{count} entry dihapus!*\n\n"
            "❌ Semua entry yang mengandung *'{meal_name}'* telah dihapus.\n\n"
            "📊 *Sisa hari ini:*\n"
            "🔥 Kalori: {total_cal}/{target_cal} kkal\n"
            "💪 Protein: {total_prot}g/{target_prot}g"
        ),
        "settarget_usage": (
            "ℹ️ Penggunaan: `/settarget <kalori> <protein>`\n"
            "Contoh: `/settarget 2000 150`"
        ),
        "settarget_invalid": "⚠️ Masukkan angka yang valid.\nContoh: `/settarget 2000 150`",
        "settarget_success": (
            "✅ *Target berhasil diperbarui!*\n\n"
            "🔥 Kalori: *{calories} kkal/hari*\n"
            "💪 Protein: *{protein}g/hari*"
        ),
        "help_text": (
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
            "*⚙️ Pengaturan & Bahasa:*\n"
            "  • /lang → Ubah bahasa (Bahasa Indonesia / English)\n"
            "  • /settarget `<kal> <prot>` → Update target harian\n"
            "  • /start → Setup ulang profil\n"
            "  • /help → Tampilkan bantuan ini"
        ),

        # ── Photo & Text Handlers ──
        "photo_analyzing": "🔍 Menganalisis foto makananmu... Tunggu sebentar ya!",
        "photo_timeout": "⏱️ Maaf, proses analisis foto memakan waktu terlalu lama. Coba kirim ulang ya!",
        "photo_error": "❌ Maaf, terjadi kesalahan saat memproses fotomu: {error}",
        "catat_usage": (
            "ℹ️ *Cara pakai /catat:*\n"
            "`/catat <nama makanan>`\n\n"
            "*Contoh:*\n"
            "• `/catat nasi goreng 1 porsi`\n"
            "• `/catat ayam bakar + nasi putih`\n"
            "• `/catat 2 butir telur rebus`\n\n"
            "_Atau kirim foto makanan langsung untuk log otomatis!_ 📸"
        ),
        "catat_processing": "✍️ Mencatat *{food_text}*... Tunggu sebentar!",
        "catat_timeout": "⏱️ Maaf, prosesnya terlalu lama. Coba lagi ya!",
        "catat_error": "❌ Terjadi kesalahan: {error}",
        "text_hint_catat": (
            "💡 Untuk mencatat makanan secara manual, gunakan:\n"
            f"`/catat {{text}}`\n\n"
            "Atau kirim *foto makanan* langsung untuk log otomatis! 📸"
        ),
        "text_processing": "⚙️ Memproses permintaanmu...",
    },

    "en": {
        # ── Onboarding /start ──
        "welcome_existing": (
            "👋 Welcome back, *{name}*!\n\n"
            "Send a photo of your meal or type food descriptions to start tracking.\n"
            "Type /help for full guide or /lang to switch language."
        ),
        "choose_language": "🌐 *Please select your language / Silakan pilih bahasa:*",
        "lang_selected": "✅ Language set to *English* 🇬🇧",
        "welcome_intro": (
            "🎉 *Welcome to CountYourCalories!*\n\n"
            "I'll help you effortlessly track your daily calories and macronutrients — "
            "just snap and send a photo of your food!\n\n"
            "Before we get started, let me learn a little about you. "
            "You can skip targets by typing /skip at any time.\n\n"
            "First, *what is your name?* 😊"
        ),
        "ask_weight": (
            "Nice to meet you, *{name}*! 💪\n\n"
            "What is your current body weight? _(in kg, e.g. 70 or 65.5)_"
        ),
        "invalid_weight": "⚠️ Please enter a valid number, e.g. *70* or *65.5*",
        "ask_height": "What is your height? _(in cm, e.g. 175)_",
        "invalid_height": "⚠️ Please enter a valid number, e.g. *175* or *168*",
        "ask_calories": (
            "🎯 What is your *daily calorie target*?\n\n"
            "_(e.g. 2000 for cutting, 2500 for maintenance, 3000 for bulking)_\n"
            "Type /skip to use default: *2000 kcal*"
        ),
        "invalid_calories": "⚠️ Please enter a valid number, e.g. *2000*",
        "ask_protein": (
            "💪 What is your *daily protein target*? _(in grams)_\n\n"
            "Recommended for you: *{min_prot}–{max_prot}g* (1.6–2.2g per kg body weight).\n\n"
            "Type /skip to use default: *150g*"
        ),
        "invalid_protein": "⚠️ Please enter a valid number, e.g. *150*",
        "skip_calories_done": (
            "✅ Daily calorie target set to *2000 kcal*.\n\n"
            "💪 What is your *daily protein target*? _(in grams)_\n"
            "Type /skip to use default: *150g*"
        ),
        "profile_saved": (
            "🎉 *Profile saved! Welcome, {name}!*\n\n"
            "📋 Your daily targets:\n"
            "  🔥 Calories: *{target_cal} kcal*\n"
            "  💪 Protein: *{target_prot}g*\n\n"
            "Now, simply send a *food photo* and I'll automatically analyze and log it!\n\n"
            "Available commands:\n"
            "  📸 Send photo → Log from photo\n"
            "  ✍️ /catat `<food>` → Log manually via text\n"
            "  /summary → View today's progress\n"
            "  /undo → Delete last logged item\n"
            "  /lang → Change language\n"
            "  /help → View help guide"
        ),
        "onboarding_cancelled": "Onboarding cancelled. Type /start to begin again.",
        "not_registered": "⚠️ You're not registered yet! Type /start to set up your profile.",

        # ── Language Switcher /lang ──
        "lang_switch_prompt": "🌐 *Choose your preferred interface language:*",
        "lang_switched_success": "✅ Language changed to *English* 🇬🇧",

        # ── Summary /summary ──
        "summary_title": "📊 *Today's summary, {name}!*",
        "summary_logged_meals": "🍽️ *Logged meals today:*",
        "summary_no_meals": "  _No meals logged yet today_",
        "summary_nutrition_progress": "📈 *Nutrition progress:*",
        "summary_cal_line": "🔥 Calories: `{bar}` {total}/{target} kcal _{sisa}_",
        "summary_prot_line": "💪 Protein: `{bar}` {total}g/{target}g _{sisa}_",
        "summary_carbs_line": "🍚 Carbs: {total}g",
        "summary_fat_line": "🥑 Fat: {total}g",
        "summary_remaining": "{sisa} kcal left",
        "summary_remaining_prot": "{sisa}g left",
        "summary_over": "+{lebih} kcal over",
        "summary_over_prot": "+{lebih}g over",
        "status_protein_100": "🎉 Daily protein target reached! Amazing work!",
        "status_protein_75": "💪 Almost at your protein target, keep it up!",
        "status_protein_50": "📈 Halfway there, stay consistent!",
        "status_protein_low": "🥗 Don't forget to get your protein in today!",

        # ── Adjustments (/undo, /hapus, /settarget, /help) ──
        "undo_empty": "📭 No meals logged today to undo.",
        "undo_success": (
            "↩️ *Entry removed!*\n\n"
            "❌ *{meal_name}* ({calories} kcal) has been deleted.\n\n"
            "📊 *Remaining today:*\n"
            "🔥 Calories: {total_cal}/{target_cal} kcal\n"
            "💪 Protein: {total_prot}g/{target_prot}g"
        ),
        "hapus_usage": (
            "ℹ️ Usage: `/hapus <food name>`\n"
            "Example: `/hapus chicken rice`"
        ),
        "hapus_not_found": (
            "❓ No logged items matching *'{meal_name}'* found today.\n\n"
            "Use /summary to inspect all meals logged today."
        ),
        "hapus_success": (
            "🗑️ *{count} entry(s) deleted!*\n\n"
            "❌ All entries containing *'{meal_name}'* were deleted.\n\n"
            "📊 *Remaining today:*\n"
            "🔥 Calories: {total_cal}/{target_cal} kcal\n"
            "💪 Protein: {total_prot}g/{target_prot}g"
        ),
        "settarget_usage": (
            "ℹ️ Usage: `/settarget <calories> <protein>`\n"
            "Example: `/settarget 2000 150`"
        ),
        "settarget_invalid": "⚠️ Please enter valid numbers.\nExample: `/settarget 2000 150`",
        "settarget_success": (
            "✅ *Target updated successfully!*\n\n"
            "🔥 Calories: *{calories} kcal/day*\n"
            "💪 Protein: *{protein}g/day*"
        ),
        "help_text": (
            "🤖 *CountYourCalories — User Guide*\n\n"
            "*📸 Logging Food:*\n"
            "  • Send a *food photo* → Bot analyzes and logs automatically\n"
            "  • /catat `<food>` → Log manually via text\n"
            "    Example: `/catat grilled chicken with rice`\n\n"
            "*📊 Checking Progress:*\n"
            "  • /summary or /today → View today's nutrition summary\n\n"
            "*✏️ Adjusting Entries:*\n"
            "  • /undo → Delete the last logged entry\n"
            "  • /hapus `<name>` → Delete entry by name\n"
            "    Example: `/hapus chicken rice`\n"
            "  • Natural language commands → E.g.: _'delete the fried chicken'_\n\n"
            "*⚙️ Settings & Language:*\n"
            "  • /lang → Switch language (English / Bahasa Indonesia)\n"
            "  • /settarget `<cal> <prot>` → Update daily targets\n"
            "  • /start → Restart profile onboarding\n"
            "  • /help → Show this help guide"
        ),

        # ── Photo & Text Handlers ──
        "photo_analyzing": "🔍 Analyzing your food photo... Please wait a moment!",
        "photo_timeout": "⏱️ Sorry, photo analysis timed out. Please try sending it again!",
        "photo_error": "❌ An error occurred while processing your photo: {error}",
        "catat_usage": (
            "ℹ️ *How to use /catat:*\n"
            "`/catat <food description>`\n\n"
            "*Examples:*\n"
            "• `/catat 1 portion of chicken rice`\n"
            "• `/catat 2 boiled eggs + toast`\n"
            "• `/catat protein shake 1 scoop`\n\n"
            "_Or simply send a photo for automatic recognition!_ 📸"
        ),
        "catat_processing": "✍️ Logging *{food_text}*... Please wait!",
        "catat_timeout": "⏱️ Sorry, request timed out. Please try again!",
        "catat_error": "❌ An error occurred: {error}",
        "text_hint_catat": (
            "💡 To log meals manually via text, use:\n"
            f"`/catat {{text}}`\n\n"
            "Or send a *food photo* directly for instant logging! 📸"
        ),
        "text_processing": "⚙️ Processing your request...",
    }
}


def t(key: str, lang: str = "id", **kwargs: Any) -> str:
    """
    Mengambil string terjemahan berdasarkan key dan bahasa ('id' atau 'en').
    Dilengkapi fallback otomatis ke 'id' atau key jika teks tidak ditemukan.
    """
    lang_code = "en" if str(lang).lower().startswith("en") else "id"
    dictionary = MESSAGES.get(lang_code, MESSAGES["id"])
    text_template = dictionary.get(key)

    if text_template is None:
        # Fallback ke bahasa Indonesia
        text_template = MESSAGES["id"].get(key, f"[{key}]")

    if kwargs:
        try:
            return text_template.format(**kwargs)
        except Exception:
            return text_template

    return text_template
