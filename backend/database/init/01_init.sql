-- Smart-EMAP / eams_db：マイグレーション実行前の最小前提
-- 004_create_system_tables.sql が user_roles 等で users を参照するため、
-- 先に users 本体が必要です（旧版の全表ダミー初期化は廃止）。
--
-- 前提: 対象データベースは既に存在し、mysql クライアントで USE 済み、または
--       mysql -u USER -p DB_NAME < 本ファイル のように DB を指定して流すこと。
--
SET NAMES utf8mb4;
SET time_zone = '+09:00';

CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT COMMENT 'ユーザーID（主キー）',
    username VARCHAR(50) NOT NULL COMMENT 'ユーザー名（ログインID、一意制約）',
    email VARCHAR(100) NOT NULL COMMENT 'メールアドレス（一意制約）',
    hashed_password VARCHAR(255) NOT NULL COMMENT 'ハッシュ化されたパスワード',
    full_name VARCHAR(100) NULL DEFAULT NULL COMMENT '氏名（フルネーム）',
    role VARCHAR(20) NOT NULL DEFAULT 'user' COMMENT 'ユーザーロール',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT 'アカウント有効フラグ',
    last_login_token VARCHAR(500) NULL DEFAULT NULL COMMENT '単一デバイスログイン用トークン',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
    PRIMARY KEY (id) USING BTREE,
    UNIQUE INDEX idx_username (username) USING BTREE,
    UNIQUE INDEX idx_email (email) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ユーザーマスターテーブル';

-- 開発用初期管理者（既に同じ username がいればスキップ）
INSERT IGNORE INTO users (username, email, hashed_password, full_name, role) VALUES
(
    'zkily',
    'chougai@arais.co.jp',
    '$2b$12$ox/KTAkwcVvNNXnZ1aBaUOTdleC6kckSVVTllfFjlab2l0OpVBfXC',
    '管理者',
    'admin'
);
