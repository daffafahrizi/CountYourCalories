# Product Requirements Document (PRD): CountYourCalories (Telegram)

**Project Lead:** Izi Daffa Fahrizi  
**Target Platform:** Telegram Bot  
**Status:** MVP / Draft  

---

## 1. Objective
Membangun asisten nutrisi *agentic* berbasis Telegram untuk mengotomatisasi pencatatan kalori dan makronutrisi harian dari foto makanan. Bot ini bertujuan untuk menghilangkan friksi pencatatan manual di aplikasi kebugaran konvensional, memastikan asupan protein harian selalu terpantau akurat untuk mendukung *progressive overload* dan rutinitas *strength training*. Skala proyek ini mencakup kapabilitas *multi-user* untuk melayani lebih dari satu pengguna secara bersamaan.

## 2. Tech Stack & Architecture

| Komponen | Teknologi | Peran dalam Sistem |
| :--- | :--- | :--- |
| **Frontend/Interface** | Telegram Bot API | Antarmuka obrolan, menerima input foto dan perintah teks. |
| **Agentic Framework** | Google Antigravity SDK | Orkestrator utama berbasis Python. Mengatur *state* obrolan, *tool execution*, dan validasi data. |
| **AI / Vision Engine** | Gemini Flash API | Memproses gambar (via Antigravity *multimodal input*) untuk menghasilkan estimasi nutrisi. |
| **Database & Auth** | Supabase (PostgreSQL) | Menyimpan profil pengguna, relasi *food_logs* per *user*, dan sisa target makro. Dasbor bawaan Supabase digunakan sebagai panel admin awal. |
| **Web Dashboard (Admin)**| React, Next.js, Tailwind CSS | Dasbor analitik kustom untuk memantau metrik pengguna secara keseluruhan (opsional/pengembangan lanjutan). |

---

## 3. Core Features (MVP)

*   **Multi-User & Session Management:** Menggunakan `telegram_id` sebagai pengenal unik untuk memisahkan sesi percakapan, profil target gizi, dan riwayat makanan masing-masing pengguna di dalam memori agen Antigravity.
*   **Multimodal Food Logging:** Pengguna cukup mengirim foto makanan. Bot otomatis mendeteksi porsi dan memecahnya menjadi profil nutrisi.
*   **Structured JSON Output:** Menggunakan fitur *structured outputs* di Antigravity untuk memaksa AI mengembalikan data dalam skema `Pydantic` yang ketat (Kalori, Protein, Karbohidrat, Lemak), bukan sekadar teks naratif.
*   **Daily Macro Tracking:** Menjumlahkan total asupan nutrisi hari ini per pengguna dan membandingkannya dengan target harian masing-masing.
*   **Quick Adjustments:** Kemampuan untuk memberikan perintah revisi ringkas di mana *agent* Antigravity akan otomatis mengoreksi *database* milik *user* tersebut.

---

## 4. Execution Flow

1. **Ingestion (Telegram -> User):** Pengguna mengirimkan foto piring makanan ke Telegram Bot. *Webhook* atau *polling* menangkap pesan beserta `telegram_id` pengirim.
2. **Authentication & Routing:** Bot mengecek `telegram_id` di Supabase. Jika belum terdaftar, bot memicu alur *onboarding*. Jika sudah, sesi diarahkan ke *agent* dengan konteks target kalori *user* bersangkutan.
3. **Agent Processing (Antigravity + Gemini):** Gambar diproses. *Agent* diinstruksikan untuk menganalisis gambar dan mengekstrak nilai makronutrisi.
4. **Data Validation (Pydantic Models):** Antigravity memvalidasi respons Gemini ke dalam skema Pydantic `FoodLog`. 
5. **Database Execution (Tool Calling):** *Agent* memanggil *tool call* untuk menginjeksi data JSON berserta `user_id` langsung ke dalam tabel Supabase.
6. **Feedback Output (Telegram -> User):** Bot membalas *chat* dengan rincian makanan dan sisa kuota gizi spesifik untuk pengguna tersebut.

---

## 5. Quality Assurance & Testing Strategy
*   **API & Integration Testing:** Menggunakan skrip Python + Playwright untuk menyimulasikan interaksi pengiriman foto dari berbagai `telegram_id` berbeda untuk menguji isolasi data *multi-user*.
*   **Database Monitoring:** Memastikan relasi antara tabel `users` dan `food_logs` di Supabase berfungsi baik tanpa anomali pencampuran data antar pengguna.
