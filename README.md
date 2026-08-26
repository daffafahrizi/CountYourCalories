# CountYourCalories 🍱

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white)](https://python.org)
[![Telegram Bot API](https://img.shields.io/badge/Telegram_Bot_API-21.6-2CA5E0.svg?logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![Google Antigravity](https://img.shields.io/badge/Agent_Framework-Google_Antigravity_SDK-4285F4.svg?logo=google&logoColor=white)](https://github.com/google)
[![Gemini Multimodal](https://img.shields.io/badge/AI_Model-Gemini_Flash-8E75C2.svg?logo=google-gemini&logoColor=white)](https://ai.google.dev/)
[![Supabase](https://img.shields.io/badge/Database-Supabase_PostgreSQL-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com)
[![Docker](https://img.shields.io/badge/Deployment-Docker_%26_Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![i18n](https://img.shields.io/badge/Languages-ID_%7C_EN-success.svg)](./bot/locales.py)

Asisten nutrisi cerdas berbasis Telegram yang mencatat kalori dan makronutrisi harian secara otomatis dari foto makanan — ditenagai oleh **Google Antigravity SDK** + **Gemini Flash Multimodal Vision**.

---

## ✨ Fitur Utama (Key Features)

- 📸 **Analisis Foto Makanan Otomatis:** Cukup kirimkan foto makananmu, AI akan mengidentifikasi seluruh komponen makanan, mengestimasi porsi, kalori, serta makronutrisi (protein, karbohidrat, lemak).
- 🌐 **Dukungan Dwibahasa (Bilingual i18n):** Mendukung penuh **Bahasa Indonesia** 🇮🇩 dan **English** 🇬🇧 dengan deteksi otomatis dan menu pergantian bahasa via `/lang`.
- ✍️ **Pencatatan Teks Manual:** Fitur `/catat <makanan>` untuk mencatat makanan ketika tidak memiliki foto.
- 🧮 **Kalkulator Gizi Ilmiah (Mifflin-St Jeor):** Menghitung BMR, TDEE, target kalori (Defisit/Maintenance/Surplus), dan protein optimal (1.8g/kg BB - BJSM 2018) secara otomatis saat onboarding `/start`.
- 📊 **Ringkasan Harian Visual:** Command `/summary` atau `/today` menyajikan laporan progres harian lengkap dengan indikator progress bar dan sisa kuota nutrisi.
- ↩️ **Koreksi Cepat & NLP:** Fitur `/undo`, `/hapus <nama>`, `/settarget`, serta perintah bahasa natural (misal: *"hapus ayam bakar tadi"*).
- 🐳 **Docker Ready:** Siap dijalankan di server/VPS 24/7 dengan Docker Compose & auto-restart.

---

## 🏗️ Arsitektur Sistem (High-Level Architecture)

```
+-----------------------------------------------------------------------------------+
|                                  COUNTYOURCALORIES                                |
|                                                                                   |
|  [ Telegram User ]  <--->  [ PTB Dispatcher ]  <--->  [ Antigravity Agent ]       |
|                                     |                          |                  |
|                              [ i18n Locales ]          [ Gemini Multimodal ]      |
|                                                                |                  |
|                                                       [ Python Tools ]            |
|                                                                |                  |
|                                                    [ Supabase PostgreSQL ]        |
+-----------------------------------------------------------------------------------+
```

> 📖 **Dokumentasi Teknis Menyeluruh:** Silakan baca [**docs/ARCHITECTURE.md**](./docs/ARCHITECTURE.md) untuk detail arsitektur lengkap, diagram urutan (sequence diagrams), spesifikasi tool calling, dan perancangan database ERD.

---

## 🚀 Panduan Memulai (Quick Start)

### 1. Prasyarat (Prerequisites)
- Python 3.11+ atau Docker Desktop
- Akun Telegram (untuk membuat bot via [@BotFather](https://t.me/BotFather))
- Database [Supabase](https://supabase.com) (Gratis)
- API Key [Google AI Studio](https://aistudio.google.com/app/api-keys) (Gemini)

---

### 2. Clone Repository & Konfigurasi Environment

```bash
# Clone repo
git clone https://github.com/daffafahrizi/CountYourCalories.git
cd CountYourCalories

# Salin template konfigurasi .env
cp .env.example .env
```

Buka dan lengkapi file `.env`:
```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here

# Gemini / Google AI Studio
GEMINI_API_KEY=your_gemini_api_key_here
```

---

### 3. Setup Database Supabase

1. Buka dashboard project kamu di [Supabase](https://supabase.com).
2. Masuk ke menu **SQL Editor**.
3. Salin dan jalankan seluruh isi file [`supabase_schema.sql`](./supabase_schema.sql).

---

### 4. Menjalankan Bot

Pilih salah satu metode berikut:

#### Opsi A: Menggunakan Docker Compose (Direkomendasikan untuk Server/VPS)
```bash
# Jalankan bot di latar belakang
docker compose up -d --build

# Melihat log bot secara realtime
docker compose logs -f
```

#### Opsi B: Menjalankan Langsung via Python Virtual Environment (Lokal)
```bash
# Buat dan aktifkan virtual environment
python -m venv venv
venv\Scripts\activate      # Di Windows
# source venv/bin/activate # Di macOS/Linux

# Install dependensi
pip install -r requirements.txt

# Jalankan bot
python -m bot.main
```

---

## 📱 Daftar Perintah Bot (Commands)

| Perintah | Fungsi | Contoh Penggunaan |
|---|---|---|
| `/start` | Memulai bot, memilih bahasa, & setup target gizi | `/start` |
| `/lang` | Mengganti bahasa antarmuka (ID / EN) | `/lang` atau `/lang en` |
| `/summary` | Menampilkan ringkasan kalori & makro hari ini | `/summary` atau `/today` |
| `/catat` | Mencatat makanan manual via teks | `/catat 1 porsi nasi padang ayam rendang` |
| `/undo` | Menghapus makanan terakhir yang dicatat hari ini | `/undo` |
| `/hapus` | Menghapus makanan berdasarkan kata kunci nama | `/hapus nasi goreng` |
| `/settarget` | Mengubah target (Shortcut angka atau Wizard kalkulator ilmiah) | `/settarget` atau `/settarget 2200 160` |
| `/help` | Menampilkan panduan bantuan lengkap | `/help` |
| *(Kirim Foto)* | Bot otomatis menganalisis dan mencatat foto | *(Kirim foto makanan langsung)* |

---

## 📁 Struktur Direktori Project

```
CountYourCalories/
├── bot/
│   ├── main.py               # Entry point bot & registrasi dispatcher
│   ├── locales.py            # Kamus terpusat i18n (Bahasa Indonesia & English)
│   ├── handlers/
│   │   ├── start.py          # Alur onboarding & pemilihan bahasa
│   │   ├── language.py       # Handler switcher /lang & callback query
│   │   ├── photo.py          # Handler analisis foto makanan (Vision)
│   │   ├── text.py           # Handler input manual /catat & NLP adjustment
│   │   ├── summary.py        # Handler laporan /summary & /today
│   │   └── adjust.py         # Handler /undo, /hapus, /settarget, /help
│   ├── agent/
│   │   ├── core.py           # Inisialisasi Antigravity Agent & Gemini Multimodal
│   │   ├── tools.py          # Definisi Function Calling tools untuk Agent
│   │   └── schemas.py        # Pydantic validation schemas
│   └── db/
│       └── supabase.py       # Supabase CRUD & helper functions
├── docs/
│   └── ARCHITECTURE.md       # Dokumentasi teknis & arsitektur mendalam
├── Dockerfile                # Image blueprint (Python 3.11-slim)
├── docker-compose.yml        # Multi-container orchestrator config
├── .dockerignore             # Docker build filter
├── supabase_schema.sql       # Skema DDL & policy PostgreSQL
├── requirements.txt          # Daftar dependensi Python
├── .env.example              # Template environment variables
└── README.md                 # Dokumentasi utama project
```

---

## 🗺️ Roadmap & Rencana Masa Depan (Future Plans)

- [x] **Core AI Vision Logging**: Analisis foto makanan otomatis via Gemini Flash.
- [x] **Bilingual Support (i18n)**: Dukungan penuh Bahasa Indonesia 🇮🇩 & English 🇬🇧.
- [x] **Scientific Nutrition Auto-Calculator**: Otomatis hitung BMR, TDEE, & target gizi via formula Mifflin-St Jeor & BJSM 2018.
- [x] **Multi-Provider Fallback Switcher**: Otomatis switch ke OpenRouter / OpenAI jika primary provider mengalami 503/429.
- [x] **Dockerization**: Image `python:3.11-slim` dan orkestrasi `docker-compose.yml`.
- [ ] **🥗 RAG Food Nutrition Reference Database (Supabase)**:
  - Integrasi tabel referensi nutrisi resmi per 100g (Kemenkes RI TKPI & USDA FoodData).
  - Tool `search_food_reference` agar AI memverifikasi angka gizi ke database lab resmi sebelum mengestimasi.
- [ ] **🥫 Barcode Scanner Integration**:
  - Scan barcode kemasan makanan/minuman via kamera untuk mengambil nutrisi instan dari *Open Food Facts*.
- [ ] **📈 Weekly & Monthly Nutrition Analytics**:
  - Visualisasi grafik progres mingguan/bulanan dan export laporan nutrisi.
- [ ] **💧 Water Intake Tracker**:
  - Pencatatan asupan air harian (`/water` atau `/minum`).
- [ ] **⏰ Smart Meal Reminders**:
  - Notifikasi pengingat makan terjadwal (Sarapan, Makan Siang, Makan Malam).

---

## 📄 Lisensi
Project ini dibuat untuk tujuan edukasi dan penggunaan personal. Bebas dikembangkan lebih lanjut.
