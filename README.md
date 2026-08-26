# CountYourCalories 🍱

Asisten nutrisi agentic berbasis Telegram yang mencatat kalori dan makronutrisi harian otomatis dari foto makanan — powered by **Google Antigravity SDK** + **Gemini Flash**.

## Fitur

- 📸 **Foto Makanan** → Kirim foto, bot otomatis analisis semua komponen & catat nutrisinya
- ✍️ **Input Manual** → Ketik nama makanan jika tidak punya foto
- 📊 **Daily Summary** → `/summary` untuk melihat progress hari ini vs target
- ↩️ **Quick Adjustments** → `/undo`, `/hapus`, dan perintah natural bahasa Indonesia
- 👥 **Multi-User** → Setiap pengguna punya sesi & data terpisah

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Interface | Telegram Bot API (Polling) |
| Agent Framework | Google Antigravity SDK |
| AI / Vision | Gemini Flash (multimodal) |
| Database | Supabase (PostgreSQL) |
| Language | Python 3.11+ |

## Setup

### 1. Clone & Install Dependencies

```bash
# Clone repo
git clone <repo-url>
cd CountYourCalories

# Buat virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Konfigurasi Environment Variables

```bash
# Salin template
copy .env.example .env
```

Edit file `.env` dengan nilai yang benar:

```env
TELEGRAM_BOT_TOKEN=   # Dari @BotFather di Telegram
SUPABASE_URL=         # https://your-project.supabase.co
SUPABASE_ANON_KEY=    # Dari Settings > API di dashboard Supabase
GEMINI_API_KEY=       # Dari https://aistudio.google.com/app/api-keys
```

### 3. Setup Database (Supabase)

1. Buka [Supabase Dashboard](https://supabase.com)
2. Buat project baru
3. Buka **SQL Editor**
4. Paste dan jalankan isi file `supabase_schema.sql`

### 4. Jalankan Bot

```bash
python -m bot.main
```

Bot akan mulai polling dan siap digunakan! Cari bot kamu di Telegram dan kirim `/start`.

## Perintah Bot

| Perintah | Fungsi |
|---|---|
| `/start` | Registrasi & onboarding |
| `/summary` atau `/today` | Lihat ringkasan nutrisi hari ini |
| `/undo` | Hapus entry terakhir |
| `/hapus <nama>` | Hapus entry by nama, contoh: `/hapus nasi goreng` |
| `/settarget <kal> <prot>` | Update target, contoh: `/settarget 2000 150` |
| `/help` | Bantuan lengkap |
| _(kirim foto)_ | Catat otomatis dari foto |
| _(ketik makanan)_ | Catat manual via teks |

## Struktur Project

```
CountYourCalories/
├── bot/
│   ├── main.py               # Entry point
│   ├── handlers/
│   │   ├── start.py          # /start + onboarding
│   │   ├── photo.py          # Handler foto makanan
│   │   ├── text.py           # Handler input teks
│   │   ├── summary.py        # /summary, /today
│   │   └── adjust.py         # /undo, /hapus, /help
│   ├── agent/
│   │   ├── core.py           # Antigravity agent
│   │   ├── tools.py          # Tool definitions
│   │   └── schemas.py        # Pydantic models
│   └── db/
│       └── supabase.py       # Supabase CRUD helpers
├── supabase_schema.sql       # Database schema
├── .env.example              # Template env vars
├── requirements.txt          # Python dependencies
└── README.md
```
