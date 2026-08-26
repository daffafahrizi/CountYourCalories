"""
bot/agent/tools.py

Tool definitions untuk Antigravity agent.
Setiap function ini bisa dipanggil oleh agent saat memproses pesan user.
"""

from bot.db import supabase as db


def log_food_items(user_id: str, items: list[dict]) -> str:
    """
    Menyimpan satu atau beberapa item makanan ke database untuk pengguna tertentu.

    Args:
        user_id: UUID pengguna di database Supabase.
        items: Daftar item makanan. Setiap item adalah dict dengan field:
               meal_name (str), calories (int), protein_g (float),
               carbs_g (float), fat_g (float), source (str: 'photo' atau 'text').

    Returns:
        Pesan konfirmasi bahwa data telah tersimpan.
    """
    saved = db.insert_food_items(user_id, items)
    names = ", ".join(item["meal_name"] for item in items)
    return f"Berhasil menyimpan {len(saved)} item: {names}."


def get_today_nutrition_summary(user_id: str) -> dict:
    """
    Mengambil total nutrisi yang sudah dikonsumsi pengguna hari ini.

    Args:
        user_id: UUID pengguna di database Supabase.

    Returns:
        Dict berisi total_calories, total_protein, total_carbs, total_fat,
        dan daftar semua entries hari ini.
    """
    return db.get_today_summary(user_id)


def delete_last_food_entry(user_id: str) -> str:
    """
    Menghapus entry makanan terakhir yang diinput pengguna hari ini (fitur undo).

    Args:
        user_id: UUID pengguna di database Supabase.

    Returns:
        Pesan konfirmasi atau pesan error jika tidak ada entry.
    """
    last = db.get_last_log(user_id)
    if not last:
        return "Tidak ada entry makanan hari ini yang bisa dihapus."
    db.delete_log_by_id(last["id"])
    return f"Entry '{last['meal_name']}' ({last['calories']} kkal) berhasil dihapus."


def delete_food_entry_by_name(user_id: str, meal_name: str) -> str:
    """
    Menghapus semua entry makanan hari ini yang namanya cocok dengan kata kunci.

    Args:
        user_id: UUID pengguna di database Supabase.
        meal_name: Nama makanan yang ingin dihapus (pencarian case-insensitive dan partial match).

    Returns:
        Pesan konfirmasi berapa entry yang dihapus.
    """
    count = db.delete_logs_by_name(user_id, meal_name)
    if count == 0:
        return f"Tidak ditemukan entry dengan nama '{meal_name}' hari ini."
    return f"Berhasil menghapus {count} entry yang mengandung '{meal_name}'."


def edit_food_entry(user_id: str, meal_name: str, new_values: dict) -> str:
    """
    Mengedit nilai nutrisi dari entry makanan tertentu hari ini.
    Mencari entry berdasarkan nama, lalu mengupdate nilai yang diberikan.

    Args:
        user_id: UUID pengguna di database Supabase.
        meal_name: Nama makanan yang ingin diedit.
        new_values: Dict berisi field yang ingin diubah. Field yang valid:
                    calories (int), protein_g (float), carbs_g (float),
                    fat_g (float), meal_name (str untuk rename).

    Returns:
        Pesan konfirmasi perubahan yang dilakukan.
    """
    logs = db.get_today_logs(user_id)
    # Cari entry dengan nama yang cocok
    matched = [
        l for l in logs
        if meal_name.lower() in l["meal_name"].lower()
    ]
    if not matched:
        return f"Tidak ditemukan entry '{meal_name}' hari ini."

    # Edit entry pertama yang cocok
    target = matched[0]
    updated = db.update_log_entry(target["id"], new_values)
    if not updated:
        return "Gagal mengupdate entry. Coba lagi."

    changes = ", ".join(f"{k}={v}" for k, v in new_values.items())
    return f"Entry '{target['meal_name']}' berhasil diupdate: {changes}."


def get_user_targets(user_id: str = "", telegram_id: int = 0) -> dict:
    """
    Mengambil target kalori dan protein harian pengguna.

    Args:
        user_id: UUID pengguna di database Supabase.
        telegram_id: Telegram ID pengguna (untuk lookup).

    Returns:
        Dict berisi target_calories dan target_protein pengguna.
    """
    user = None
    if telegram_id:
        user = db.get_user_by_telegram_id(telegram_id)
    if not user and user_id:
        user = db.get_user_by_id(user_id)
    if not user:
        return {"target_calories": 2000, "target_protein": 150}
    return {
        "target_calories": user.get("target_calories", 2000),
        "target_protein": user.get("target_protein", 150),
        "target_carbs": user.get("target_carbs"),
        "target_fat": user.get("target_fat"),
    }
