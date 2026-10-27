-- Migration 002: xóa mềm linh kiện và tồn kho theo trung tâm (QT-13: không xóa vật lý).
-- Giao dịch cũ vẫn tham chiếu được dòng part/part_stock đã ngừng dùng.
-- Dùng IF NOT EXISTS để chạy lại lần hai không lỗi.

ALTER TABLE part       ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE part_stock ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;
