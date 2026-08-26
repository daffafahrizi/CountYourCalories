"""
bot/agent/core.py

Setup dan inisialisasi Antigravity agent sebagai otak dari CountYourCalories bot.
"""

import asyncio
import os
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.types import Image

from bot.agent.tools import (
    log_food_items,
    get_today_nutrition_summary,
    delete_last_food_entry,
    delete_food_entry_by_name,
    edit_food_entry,
    get_user_targets,
)

# Timeout dalam detik untuk pemrosesan agent
AGENT_TIMEOUT_SECONDS = 90

SYSTEM_PROMPT = """
Kamu adalah CountYourCalories, asisten nutrisi cerdas berbasis Telegram.
Tugasmu adalah membantu pengguna mencatat dan memantau asupan kalori serta makronutrisi harian mereka.

## Kemampuanmu:
1. **Analisis foto makanan**: Ketika pengguna mengirim foto, identifikasi SEMUA komponen makanan 
   yang terlihat (misal: nasi, ayam, sayur, dll.) dan estimasikan nilai nutrisinya masing-masing.
2. **Input teks manual**: Jika pengguna mendeskripsikan makanan via teks, estimasikan nutrisinya.
3. **Simpan ke database**: Setelah menganalisis, SELALU simpan hasilnya menggunakan tool `log_food_items`.
4. **Koreksi dan penyesuaian**: Bantu pengguna menghapus atau mengedit entry yang salah.
5. **Ringkasan harian**: Tampilkan progres nutrisi hari ini vs target.

## Aturan penting:
- Selalu gunakan Bahasa Indonesia yang ramah dan natural.
- Untuk foto, identifikasi SEMUA makanan yang terlihat, bukan hanya yang dominan.
- Setelah menyimpan data, SELALU tampilkan ringkasan: apa yang baru disimpan + sisa target hari ini.
- Estimasi nutrisi berdasarkan porsi visual. Jika tidak yakin, beri range dan pilih nilai tengah.
- Jangan terlalu panjang dalam membalas — to the point tapi informatif.
- Format angka: kalori tanpa desimal, protein/karbo/lemak dengan 1 desimal.

## Format balasan setelah logging:
```
✅ Berhasil dicatat!

[Emoji makanan] [Nama Makanan] — [kalori] kkal
  Protein: [x]g | Karbo: [x]g | Lemak: [x]g

📊 Progress hari ini:
🔥 Kalori: [total]/[target] kkal ([sisa] sisa)
💪 Protein: [total]/[target]g ([sisa]g sisa)
```

## Format untuk /summary:
```
📊 Ringkasan hari ini, [nama]!

🍽️ Yang sudah dimakan:
• [Makanan 1] — [x] kkal
• [Makanan 2] — [x] kkal
...

📈 Total:
🔥 Kalori: [total]/[target] kkal
💪 Protein: [total]/[target]g
🍚 Karbo: [total]g
🥑 Lemak: [total]g

[Pesan motivasi berdasarkan progress]
```
""".strip()


def create_agent_config() -> LocalAgentConfig:
    """Membuat konfigurasi Antigravity agent dengan API key."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY tidak ditemukan! Pastikan file .env sudah dikonfigurasi."
        )
    return LocalAgentConfig(
        api_key=api_key,
        system_instructions=SYSTEM_PROMPT,
        tools=[
            log_food_items,
            get_today_nutrition_summary,
            delete_last_food_entry,
            delete_food_entry_by_name,
            edit_food_entry,
            get_user_targets,
        ],
    )


async def _collect_response(response) -> str:
    """Kumpulkan semua chunk streaming dari response agent."""
    chunks = []
    async for chunk in response:
        chunks.append(chunk)
    result = "".join(chunks).strip()
    if not result and hasattr(response, "text"):
        result = await response.text()
    return result


async def process_photo_message(
    image_path: str,
    user_context: str,
    caption: str = "",
) -> str:
    """
    Memproses foto makanan menggunakan Antigravity agent + Gemini multimodal.

    Args:
        image_path: Path lokal ke file gambar yang sudah didownload.
        user_context: String berisi konteks user (id, nama, target).
        caption: Caption foto dari Telegram (jika ada).

    Returns:
        Respons teks dari agent.

    Raises:
        asyncio.TimeoutError: Jika agent tidak merespons dalam AGENT_TIMEOUT_SECONDS.
    """
    config = create_agent_config()
    prompt_parts = [
        f"[Konteks pengguna]: {user_context}\n\n",
        "Ini adalah foto makanan yang baru saja saya makan. ",
    ]
    if caption:
        prompt_parts.append(f"Keterangan dari saya: {caption}. ")
    prompt_parts.append(
        "Tolong analisis semua makanan yang ada di foto ini, estimasikan nutrisinya, "
        "dan simpan ke database."
    )

    image = Image.from_file(image_path)
    full_prompt = ["".join(prompt_parts), image]

    async def _run():
        async with Agent(config) as agent:
            response = await agent.chat(full_prompt)
            return await _collect_response(response)

    return await asyncio.wait_for(_run(), timeout=AGENT_TIMEOUT_SECONDS)


async def process_text_message(
    user_message: str,
    user_context: str,
) -> str:
    """
    Memproses pesan teks dari user (input manual atau perintah adjustment).

    Args:
        user_message: Pesan teks dari pengguna.
        user_context: String berisi konteks user (id, nama, target).

    Returns:
        Respons teks dari agent.

    Raises:
        asyncio.TimeoutError: Jika agent tidak merespons dalam AGENT_TIMEOUT_SECONDS.
    """
    config = create_agent_config()
    full_prompt = f"[Konteks pengguna]: {user_context}\n\n{user_message}"

    async def _run():
        async with Agent(config) as agent:
            response = await agent.chat(full_prompt)
            return await _collect_response(response)

    return await asyncio.wait_for(_run(), timeout=AGENT_TIMEOUT_SECONDS)
