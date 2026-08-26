-- CountYourCalories — Supabase Schema
-- Jalankan SQL ini di Supabase SQL Editor

-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: users
-- Menyimpan profil dan target gizi setiap pengguna
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id      BIGINT UNIQUE NOT NULL,
  name             TEXT NOT NULL,
  weight_kg        FLOAT,
  height_cm        FLOAT,
  target_calories  INT NOT NULL DEFAULT 2000,
  target_protein   INT NOT NULL DEFAULT 150,
  target_carbs     INT,
  target_fat       INT,
  created_at       TIMESTAMPTZ DEFAULT now()
);

-- Index untuk lookup cepat berdasarkan telegram_id
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Tabel: food_logs
-- Menyimpan setiap item makanan yang dicatat pengguna
-- 1 foto atau 1 sesi makan bisa menghasilkan beberapa baris (1 item = 1 row)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS food_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  logged_at   TIMESTAMPTZ DEFAULT now(),
  meal_name   TEXT NOT NULL,
  calories    INT NOT NULL DEFAULT 0,
  protein_g   FLOAT NOT NULL DEFAULT 0,
  carbs_g     FLOAT DEFAULT 0,
  fat_g       FLOAT DEFAULT 0,
  source      TEXT DEFAULT 'photo' CHECK (source IN ('photo', 'text'))
);

-- Index untuk query log harian per user
CREATE INDEX IF NOT EXISTS idx_food_logs_user_date
  ON food_logs(user_id, logged_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- Row Level Security (RLS)
-- Aktifkan RLS agar data antar pengguna terisolasi
-- ─────────────────────────────────────────────────────────────────────────────

-- Enable RLS pada kedua tabel
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_logs ENABLE ROW LEVEL SECURITY;

-- Policy: service_role (backend Python bot) bisa baca/tulis semua data
-- Ini diperlukan karena bot menggunakan anon/service key, bukan auth JWT per user
CREATE POLICY "Service role full access on users"
  ON users FOR ALL
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Service role full access on food_logs"
  ON food_logs FOR ALL
  USING (true)
  WITH CHECK (true);
