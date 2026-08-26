"""
bot/agent/schemas.py

Pydantic models untuk validasi data nutrisi dan profil pengguna.
"""

from pydantic import BaseModel, Field
from typing import Optional


class FoodItem(BaseModel):
    """Representasi satu item makanan dengan nilai nutrisinya."""
    meal_name: str = Field(description="Nama makanan, contoh: 'Nasi Putih', 'Ayam Bakar'")
    calories: int = Field(description="Estimasi kalori dalam kkal")
    protein_g: float = Field(description="Estimasi protein dalam gram")
    carbs_g: float = Field(description="Estimasi karbohidrat dalam gram")
    fat_g: float = Field(description="Estimasi lemak dalam gram")
    source: str = Field(default="photo", description="Sumber data: 'photo' atau 'text'")


class FoodLog(BaseModel):
    """Hasil analisis satu sesi makan (bisa berisi lebih dari 1 item)."""
    items: list[FoodItem] = Field(description="Daftar semua makanan yang terdeteksi")
    notes: Optional[str] = Field(
        default=None,
        description="Catatan tambahan dari AI, misal ketidakpastian estimasi"
    )


class UserProfile(BaseModel):
    """Profil dan target gizi pengguna."""
    telegram_id: int
    name: str
    weight_kg: float
    height_cm: float
    target_calories: int
    target_protein: int
    target_carbs: Optional[int] = None
    target_fat: Optional[int] = None


class DailySummary(BaseModel):
    """Ringkasan nutrisi harian pengguna."""
    total_calories: int
    total_protein: float
    total_carbs: float
    total_fat: float
    target_calories: int
    target_protein: int
    entries: list[dict]
