"""
bot/db/supabase.py

Supabase client dan helper functions untuk operasi CRUD.
"""

import os
from datetime import date, datetime, timezone
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

_supabase: Optional[Client] = None


def get_client() -> Client:
    """Mengembalikan Supabase client (singleton)."""
    global _supabase
    if _supabase is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL dan SUPABASE_ANON_KEY harus diset di file .env"
            )
        _supabase = create_client(url, key)
    return _supabase


# ─── User Operations ──────────────────────────────────────────────────────────

def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    """Cari user berdasarkan telegram_id. Return None jika belum terdaftar."""
    client = get_client()
    result = (
        client.table("users")
        .select("*")
        .eq("telegram_id", telegram_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def create_user(
    telegram_id: int,
    name: str,
    weight_kg: float,
    height_cm: float,
    target_calories: int,
    target_protein: int,
    target_carbs: Optional[int] = None,
    target_fat: Optional[int] = None,
) -> dict:
    """Buat user baru di tabel users."""
    client = get_client()
    result = (
        client.table("users")
        .insert({
            "telegram_id": telegram_id,
            "name": name,
            "weight_kg": weight_kg,
            "height_cm": height_cm,
            "target_calories": target_calories,
            "target_protein": target_protein,
            "target_carbs": target_carbs,
            "target_fat": target_fat,
        })
        .execute()
    )
    return result.data[0]


def update_user_targets(
    telegram_id: int,
    target_calories: Optional[int] = None,
    target_protein: Optional[int] = None,
    target_carbs: Optional[int] = None,
    target_fat: Optional[int] = None,
) -> dict:
    """Update target gizi pengguna."""
    client = get_client()
    updates = {}
    if target_calories is not None:
        updates["target_calories"] = target_calories
    if target_protein is not None:
        updates["target_protein"] = target_protein
    if target_carbs is not None:
        updates["target_carbs"] = target_carbs
    if target_fat is not None:
        updates["target_fat"] = target_fat

    result = (
        client.table("users")
        .update(updates)
        .eq("telegram_id", telegram_id)
        .execute()
    )
    return result.data[0]


# ─── Food Log Operations ──────────────────────────────────────────────────────

def insert_food_items(user_id: str, items: list[dict]) -> list[dict]:
    """
    Menyimpan beberapa food item sekaligus ke tabel food_logs.
    Setiap item adalah dict dengan key: meal_name, calories, protein_g, carbs_g, fat_g, source.
    """
    client = get_client()
    rows = [
        {
            "user_id": user_id,
            "meal_name": item["meal_name"],
            "calories": item["calories"],
            "protein_g": item["protein_g"],
            "carbs_g": item.get("carbs_g", 0),
            "fat_g": item.get("fat_g", 0),
            "source": item.get("source", "photo"),
        }
        for item in items
    ]
    result = client.table("food_logs").insert(rows).execute()
    return result.data


def _get_today_start_utc() -> str:
    """Mengembalikan timestamp ISO UTC untuk jam 00:00:00 waktu lokal hari ini."""
    local_now = datetime.now().astimezone()
    local_midnight = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    utc_midnight = local_midnight.astimezone(timezone.utc)
    return utc_midnight.isoformat()


def get_today_logs(user_id: str) -> list[dict]:
    """Ambil semua food_logs hari ini untuk user tertentu."""
    client = get_client()
    today_start = _get_today_start_utc()
    result = (
        client.table("food_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("logged_at", today_start)
        .order("logged_at", desc=False)
        .execute()
    )
    return result.data


def get_last_log(user_id: str) -> Optional[dict]:
    """Ambil food_log terakhir yang diinput user hari ini."""
    client = get_client()
    today_start = _get_today_start_utc()
    result = (
        client.table("food_logs")
        .select("*")
        .eq("user_id", user_id)
        .gte("logged_at", today_start)
        .order("logged_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def delete_log_by_id(log_id: str) -> bool:
    """Hapus satu food_log berdasarkan id-nya."""
    client = get_client()
    result = client.table("food_logs").delete().eq("id", log_id).execute()
    return bool(result.data)


def delete_logs_by_name(user_id: str, meal_name: str) -> int:
    """
    Hapus semua food_log hari ini yang nama makanannya cocok (case-insensitive).
    Return jumlah baris yang dihapus.
    """
    client = get_client()
    today_start = _get_today_start_utc()
    result = (
        client.table("food_logs")
        .delete()
        .eq("user_id", user_id)
        .ilike("meal_name", f"%{meal_name}%")
        .gte("logged_at", today_start)
        .execute()
    )
    return len(result.data)


def update_log_entry(log_id: str, updates: dict) -> Optional[dict]:
    """
    Update nilai nutrisi pada food_log tertentu.
    updates bisa berisi: calories, protein_g, carbs_g, fat_g, meal_name
    """
    client = get_client()
    allowed_fields = {"calories", "protein_g", "carbs_g", "fat_g", "meal_name"}
    filtered = {k: v for k, v in updates.items() if k in allowed_fields}
    if not filtered:
        return None
    result = (
        client.table("food_logs")
        .update(filtered)
        .eq("id", log_id)
        .execute()
    )
    return result.data[0] if result.data else None


def get_today_summary(user_id: str) -> dict:
    """
    Hitung total kalori dan makronutrisi hari ini.
    Return dict: total_calories, total_protein, total_carbs, total_fat, entries
    """
    logs = get_today_logs(user_id)
    total_calories = sum(l.get("calories", 0) for l in logs)
    total_protein = sum(l.get("protein_g", 0) for l in logs)
    total_carbs = sum(l.get("carbs_g", 0) for l in logs)
    total_fat = sum(l.get("fat_g", 0) for l in logs)
    return {
        "total_calories": total_calories,
        "total_protein": round(total_protein, 1),
        "total_carbs": round(total_carbs, 1),
        "total_fat": round(total_fat, 1),
        "entries": logs,
    }
