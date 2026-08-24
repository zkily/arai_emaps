-- ユーザーログインQR用トークン（パスワードはQRに含めない）
SET NAMES utf8mb4;

DELIMITER //
DROP PROCEDURE IF EXISTS add_users_qr_login_token//
CREATE PROCEDURE add_users_qr_login_token()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'qr_login_token') = 0 THEN
    ALTER TABLE users
      ADD COLUMN qr_login_token VARCHAR(64) NULL COMMENT 'ログインQRトークン（パスワードとは別）' AFTER hashed_password;
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS
      WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'uk_users_qr_login_token') = 0 THEN
    ALTER TABLE users ADD UNIQUE INDEX uk_users_qr_login_token (qr_login_token);
  END IF;
END//
DELIMITER ;
CALL add_users_qr_login_token();
DROP PROCEDURE add_users_qr_login_token;
