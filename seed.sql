-- seed.sql
-- 清除現有資料 (如果需要重置，請取消註解以下行)
-- TRUNCATE TABLE bookings_booking, bookings_timeoff, bookings_coursetype, bookings_instructor, auth_user CASCADE;

-- 插入測試使用者 (密碼皆為: vibe123)
-- 使用 Django 預設的 pbkdf2_sha256 雜湊演算法生成的 'vibe123' 密碼
INSERT INTO auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
VALUES
(101, 'pbkdf2_sha256$870000$l06NUdDKQcQFiQV0d95Azc$bz9yK0oCbty0nCJ0tzJdgv7l1h6+8NJmuZLHF1pFoJg=', NULL, false, 'student01', 'Test', 'Student', 'student01@example.com', false, true, NOW()),
(102, 'pbkdf2_sha256$870000$l06NUdDKQcQFiQV0d95Azc$bz9yK0oCbty0nCJ0tzJdgv7l1h6+8NJmuZLHF1pFoJg=', NULL, false, 'instructor01', 'Test', 'Instructor', 'instructor01@example.com', true, true, NOW()),
(103, 'pbkdf2_sha256$870000$l06NUdDKQcQFiQV0d95Azc$bz9yK0oCbty0nCJ0tzJdgv7l1h6+8NJmuZLHF1pFoJg=', NULL, true, 'admin', 'Super', 'Admin', 'admin@example.com', true, true, NOW())
ON CONFLICT (id) DO NOTHING;

-- 更新 auth_user 的 sequence
SELECT setval('auth_user_id_seq', (SELECT MAX(id) FROM auth_user));

-- 插入課程類型 (CourseType)
INSERT INTO bookings_coursetype (id, created_at, updated_at, name, duration_minutes, description, active)
VALUES
(1, NOW(), NOW(), '體驗課程 (30分鐘)', 30, '基礎體驗課程，適合第一次來的學員。', true),
(2, NOW(), NOW(), '進階指導 (30分鐘)', 30, '針對特定技巧進行的一對一調整與指導。', true)
ON CONFLICT (id) DO NOTHING;

-- 更新 bookings_coursetype 的 sequence
SELECT setval('bookings_coursetype_id_seq', (SELECT MAX(id) FROM bookings_coursetype));

-- 插入教練資料 (Instructor)
-- user_id = 102 (對應 instructor01)
INSERT INTO bookings_instructor (id, created_at, updated_at, display_name, active, user_id)
VALUES
(1, NOW(), NOW(), 'Coach John', true, 102)
ON CONFLICT (id) DO NOTHING;

-- 更新 bookings_instructor 的 sequence
SELECT setval('bookings_instructor_id_seq', (SELECT MAX(id) FROM bookings_instructor));

-- 插入一些測試的預約紀錄 (Booking)
-- 預約 1: 今天 10:00 - 10:30 (假設資料)
INSERT INTO bookings_booking (id, created_at, updated_at, start_datetime, end_datetime, status, course_type_id, instructor_id, student_id)
VALUES
(1, NOW(), NOW(), CURRENT_DATE + TIME '10:00:00', CURRENT_DATE + TIME '10:30:00', 'BOOKED', 1, 1, 101),
(2, NOW(), NOW(), CURRENT_DATE + TIME '14:30:00', CURRENT_DATE + TIME '15:00:00', 'BOOKED', 2, 1, 101)
ON CONFLICT (id) DO NOTHING;

-- 更新 bookings_booking 的 sequence
SELECT setval('bookings_booking_id_seq', (SELECT MAX(id) FROM bookings_booking));

-- 插入教練的休假時段 (TimeOff)
-- 假設 Coach John 今天 12:00 - 13:00 休息
INSERT INTO bookings_timeoff (id, created_at, updated_at, start_datetime, end_datetime, reason, instructor_id)
VALUES
(1, NOW(), NOW(), CURRENT_DATE + TIME '12:00:00', CURRENT_DATE + TIME '13:00:00', 'Lunch Break (午休)', 1)
ON CONFLICT (id) DO NOTHING;

-- 更新 bookings_timeoff 的 sequence
SELECT setval('bookings_timeoff_id_seq', (SELECT MAX(id) FROM bookings_timeoff));
