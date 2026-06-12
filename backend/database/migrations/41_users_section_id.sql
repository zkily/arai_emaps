-- users テーブルに所属課（section）ID を追加
DELIMITER //
DROP PROCEDURE IF EXISTS add_users_section_id//
CREATE PROCEDURE add_users_section_id()
BEGIN
  IF (SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND COLUMN_NAME = 'section_id') = 0 THEN
    ALTER TABLE users ADD COLUMN section_id INT NULL COMMENT '所属課ID';
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND INDEX_NAME = 'idx_users_section') = 0 THEN
    ALTER TABLE users ADD INDEX idx_users_section (section_id);
  END IF;
  IF (SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users' AND CONSTRAINT_NAME = 'fk_users_section') = 0 THEN
    ALTER TABLE users ADD CONSTRAINT fk_users_section FOREIGN KEY (section_id) REFERENCES organizations(id) ON DELETE SET NULL;
  END IF;
END//
DELIMITER ;
CALL add_users_section_id();
DROP PROCEDURE add_users_section_id;
