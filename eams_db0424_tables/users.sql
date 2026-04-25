SET NAMES utf8mb4;

CREATE TABLE `users`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT 'ユーザーID（主キー）',
  `username` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ユーザー名（ログインID、一意制約）',
  `email` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'メールアドレス（一意制約）',
  `hashed_password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'ハッシュ化されたパスワード',
  `full_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '氏名（フルネーム）',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'user' COMMENT 'ユーザーロール（user:一般ユーザー、admin:管理者）',
  `is_active` tinyint(1) NULL DEFAULT 1 COMMENT 'アカウント有効フラグ（TRUE:有効、FALSE:無効）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '作成日時',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日時',
  `last_login_token` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '最後にログインしたデバイスのトークン（単一デバイスログイン用）',
  `department_id` int NULL DEFAULT NULL COMMENT '所属部門ID',
  `two_factor_enabled` tinyint(1) NULL DEFAULT 0 COMMENT '二要素認証有効フラグ',
  `last_login_at` timestamp NULL DEFAULT NULL COMMENT '最終ログイン日時',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT 'active' COMMENT 'ステータス（active/locked/inactive）',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE,
  INDEX `idx_username`(`username` ASC) USING BTREE COMMENT 'ユーザー名インデックス',
  INDEX `idx_email`(`email` ASC) USING BTREE COMMENT 'メールアドレスインデックス',
  INDEX `idx_users_department`(`department_id` ASC) USING BTREE,
  INDEX `idx_users_status`(`status` ASC) USING BTREE,
  CONSTRAINT `fk_users_department` FOREIGN KEY (`department_id`) REFERENCES `organizations` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 24 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'ユーザーマスターテーブル' ROW_FORMAT = Dynamic;
INSERT INTO `users` VALUES (2, 'zkily', 'chogai136228508@gmail.com', '$2b$12$VAgW7lhf.v3sF.VtGxq6e.M3lZ1LMqVJf/mzq8n1.9PY7WPLY5boC', 'zk', 'admin', 1, '2026-01-07 11:36:08', '2026-04-24 07:52:01', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ6a2lseSIsImV4cCI6MTc3NzAyNzkyMX0.a1YinEP7BQ-Hpbv_2IcLE14FiqvgLyhZvUV6GMzRo_g', 1, 0, '2026-04-24 07:52:02', 'active');
INSERT INTO `users` VALUES (3, '1001', 'chougai@arais.co.jp', '$2b$12$cnyg7YpUt0oKUZ9pM8fBXO0Btvz7Y/G.amv37709EYER7MMlRcl1W', '趙 凱', 'admin', 1, '2026-02-05 19:26:01', '2026-04-24 09:50:59', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDAxIiwiZXhwIjoxNzc3MDM1MDU5fQ.5QI_B9rGjWoMOIaHWv5zHHbzkpiK0qJOHSIBauFQwH0', 21, 0, '2026-04-24 09:51:00', 'active');
INSERT INTO `users` VALUES (4, '1002', 'fukushima@arais.co.jp', '$2b$12$dtcKfYIU4AJO83hdlkowC.paEKEVntguCzJbEjPPFQwlW6.uStDpy', '福島', 'worker', 1, '2026-02-06 10:45:07', '2026-02-06 11:08:37', NULL, 21, 0, NULL, 'active');
INSERT INTO `users` VALUES (5, '1005', 'komori@arais.co.jp', '$2b$12$l2dY0z79LklyWVm3gdHY/u7FJ8RiUcPutM9l3Uz6yVFh/sj5GS7w.', '小森', 'manager', 1, '2026-02-06 10:46:04', '2026-04-24 16:07:52', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDA1IiwiZXhwIjoxNzc3MDU3NjcyfQ.C9V61i_n-Te0k1CdjR7bsKKz9HHKF92Nej75tox_KQs', 21, 0, '2026-04-24 16:07:52', 'active');
INSERT INTO `users` VALUES (6, '1025', 'shinoda@arais.co.jp', '$2b$12$xsavgjxqxbTgTB5KJmU1GeOkDI2NmzyLkH2A/SCFOQbKEPq.aDlRe', '篠田', 'manager', 1, '2026-02-06 10:46:52', '2026-04-24 14:15:41', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDI1IiwiZXhwIjoxNzc3MDUwOTQxfQ.YBlBNwjVtKrMhbEjpOAJsvaNwB-mXo9vEXT-MKDMEok', 21, 0, '2026-04-24 14:15:41', 'active');
INSERT INTO `users` VALUES (7, '1015', 'takemura@arais.co.jp', '$2b$12$R7XFBejCVKvmlc6NTGcwIu19.FT0FOrEs4JEKD7b1BstJKYY9A2FC', '竹村', 'user', 1, '2026-02-06 10:49:24', '2026-04-24 08:38:11', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDE1IiwiZXhwIjoxNzc3MDMwNjkxfQ.IQQjPJDqNRbpV5-mr5HtRj0LE_bX_m3Zhl7ZmMdI0oI', 21, 0, '2026-04-24 08:38:11', 'active');
INSERT INTO `users` VALUES (8, '1007', 'aki-son@arais.co.jp', '$2b$12$55G8SqfSESFSALyjdGoh9ew1/LDWHi2fS.1orfUOPSs9HOZrtXaym', '孫', 'user', 1, '2026-02-06 10:50:12', '2026-04-24 09:40:57', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDA3IiwiZXhwIjoxNzc3MDM0NDU3fQ.GlB1kkE-N-bWllMmtV3634DnwsXh07sAmyln_GchtsQ', 21, 0, '2026-04-24 09:40:58', 'active');
INSERT INTO `users` VALUES (9, '1050', 'toujou@arais.co.jp', '$2b$12$Sf01kfS4IqEtFP4UNs.3muFph8LfC/3OELVCTcXB4VhpJgqVVx512', '東條', 'user', 1, '2026-02-19 08:20:04', '2026-04-24 16:55:53', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDUwIiwiZXhwIjoxNzc3MDYwNTUzfQ.5PSNcjRNU8YK0iiVUDhDbvGcoCe9RcpQS3NiJ3m8B-w', 21, 0, '2026-04-24 16:55:54', 'active');
INSERT INTO `users` VALUES (10, 'uchiyama239', 'uchiyama@arais.co.jp', '$2b$12$XQjWlS9kzcTloLT0oNssh.nUjtfhI9WMDiuSi1ZAMq5cqSEYbXFU2', '内山', 'manager', 1, '2026-03-12 10:30:21', '2026-04-24 08:24:31', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1Y2hpeWFtYTIzOSIsImV4cCI6MTc3NzAyOTg3MX0.87f470-UjlPyvgzZQV-jo5uYvwOSHRHrQiv4ImWvD7Y', 24, 0, '2026-04-24 08:24:31', 'active');
INSERT INTO `users` VALUES (11, '2001', 'takeda@arais.co.jp', '$2b$12$xMj.TIH/mrRqRTVfC9g0VuPTT1talvGrBtAhYfW.ePo/eKap.XcVm', '竹田', 'worker', 1, '2026-03-31 17:30:50', '2026-03-31 17:30:50', NULL, 19, 0, NULL, 'active');
INSERT INTO `users` VALUES (12, '2002', 'idou@arais.co.jp', '$2b$12$LYLxNOT6LI6AetPYFcfrEefILenPuHQcBMQ3rOS80pdcjkcX61VX.', '伊藤', 'worker', 1, '2026-03-31 17:31:30', '2026-03-31 17:31:30', NULL, 19, 0, NULL, 'active');
INSERT INTO `users` VALUES (13, '2003', 'noji@arais.co.jp', '$2b$12$K46089ugOPvqNjzK4InZAeby9DXUBWhgUSYHnp1BFgqSCgxfDfRJO', '野地', 'worker', 1, '2026-03-31 17:32:14', '2026-03-31 17:32:14', NULL, 19, 0, NULL, 'active');
INSERT INTO `users` VALUES (14, '7001', 'kin@arais.co.jp', '$2b$12$iwq1mCRpQdN/rQ.QN0z4k.a1P09QsAp4dsPFTQGYAT4q3IX8Fvd0W', '金', 'manager', 1, '2026-04-01 11:19:39', '2026-04-24 13:05:31', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3MDAxIiwiZXhwIjoxNzc3MDQ2NzMxfQ.cLquatci01ds4CJjKwg7Ty0HZ19J68w_1C4Iy6VqE2k', 24, 0, '2026-04-24 13:05:31', 'active');
INSERT INTO `users` VALUES (15, 'hayakawa', 'hayakawa@arais.co.jp', '$2b$12$rM2A0eqDNBE/jzV7jN9K7.f.ljvqdguPGRSb92JUBlisHKnlblUQS', '早川', 'manager', 1, '2026-04-02 16:43:49', '2026-04-22 10:36:16', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoYXlha2F3YSIsImV4cCI6MTc3Njg2NDk3Nn0.nCmjycjixUUpoHLvMKBpsIeqtjLYAk5WqDehYYPUYtA', 19, 0, '2026-04-22 10:36:17', 'active');
INSERT INTO `users` VALUES (16, '10071', 'son1@arais.co.jp', '$2b$12$GEBX65GReM8ciYtc0PbsI.CK0LdsV718C3B8Kf6M4yDD46DQ7Ebxu', '孫', 'user', 1, '2026-04-02 17:06:20', '2026-04-21 16:44:08', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMDA3MSIsImV4cCI6MTc3NjgwMDY0OH0.2ivjQgHPvOLqBhDzW4Pjs-CcxF_CsWbUO-Ky4D3W3q4', 21, 0, '2026-04-21 16:44:08', 'active');
INSERT INTO `users` VALUES (17, 'hirasaki', 'hirasaki@arais.co.jp', '$2b$12$EpgFF0rxzd3X28Bw8HWCp.N7hSGqyOYN5alcQVYCt.4y52CDYDD7e', '平崎', 'manager', 1, '2026-04-02 18:06:55', '2026-04-24 13:29:04', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoaXJhc2FraSIsImV4cCI6MTc3NzA0ODE0NH0.XtA7yIBIP1xGWzh8IiYYulHBjhN3kFZb6BANdzFPVwk', 19, 0, '2026-04-24 13:29:05', 'active');
INSERT INTO `users` VALUES (18, 'watanabe@arais.co.jp', 'watanabe@arais.co.jp', '$2b$12$NbcsiutjfuBGrAiSkZDBr.JnEVYKgeSBwHUKqRmVP03Um5Se9evUS', '渡辺', 'manager', 1, '2026-04-02 18:08:26', '2026-04-16 17:55:35', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ3YXRhbmFiZUBhcmFpcy5jby5qcCIsImV4cCI6MTc3NjM3MjkzNX0.pKqrFtrI3gwFHxXETPsNG8guhZzzPeIuQ-4fPyjHOr4', 19, 0, '2026-04-16 17:55:36', 'active');
INSERT INTO `users` VALUES (19, 'gotou', 'gotou@arais.co.jp', '$2b$12$4TyatP6lAiBUy6n2On0X..s/fjrWvtJpwaAoV3a4ZtAPnWCwCcI9G', '後藤', 'manager', 1, '2026-04-02 18:09:18', '2026-04-21 14:40:31', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJnb3RvdSIsImV4cCI6MTc3Njc5MzIzMX0.5pwmq0NICe2toqkR7qP5V1qu7V71EMOHDPXA8gqjsVE', 19, 0, '2026-04-21 14:40:31', 'active');
INSERT INTO `users` VALUES (20, 'kobayashi@arais.co.jp', 'kobayashi@arais.co.jp', '$2b$12$MTCY7kzFQseTIYZCFL1rYOMyfVHjudXq7o9baW4k10snJCWgGv5hy', '小林', 'manager', 1, '2026-04-02 18:09:57', '2026-04-22 16:15:37', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJrb2JheWFzaGlAYXJhaXMuY28uanAiLCJleHAiOjE3NzY4ODUzMzd9.z9vov_r5TPq_DZ5fEc9RVwwKbYRWx-ZPxFq8wY_ef44', 19, 0, '2026-04-22 16:15:37', 'active');
INSERT INTO `users` VALUES (21, 'kandou@arais.co.jp', 'kandou@arais.co.jp', '$2b$12$emphm4937kej4POoYnc1xuR6BswbmQ5h.8waDZyvz57DCwMPD6Mpi', '考藤', 'user', 1, '2026-04-02 18:11:36', '2026-04-02 18:11:36', NULL, 24, 0, NULL, 'active');
INSERT INTO `users` VALUES (22, 'takatori@arais.co.jp', 'takatori@arais.co.jp', '$2b$12$FA6wEfNu.BUdpZQJAtZVkO3ED5tQO1VkqQP.SilWEPNsMj3dt6Oyi', '高鳥', 'user', 1, '2026-04-02 18:12:52', '2026-04-02 18:12:52', NULL, 19, 0, NULL, 'active');
INSERT INTO `users` VALUES (23, 'kuriyama', 'kuriyama@arais.co.jp', '$2b$12$zRxW4ulQUc8qbtKLvWxkfuDkQ8UoCzA.kGFTGPbWKq5wlWzFa/ira', '栗山', 'user', 1, '2026-04-23 09:10:10', '2026-04-24 16:50:16', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJrdXJpeWFtYSIsImV4cCI6MTc3NzA2MDIxNn0.RaNJtcMDuWXUAFLfp0aB14RwVPAAt1X0sm6-4tyTC1U', 27, 0, '2026-04-24 16:50:16', 'active');
