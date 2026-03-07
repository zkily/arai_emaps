-- 分散ロック（他端末との同時一括更新防止）
CREATE TABLE IF NOT EXISTS `distributed_locks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `lock_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `lock_value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `expires_at` timestamp NOT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `lock_key` (`lock_key` ASC) USING BTREE,
  INDEX `idx_lock_key` (`lock_key` ASC) USING BTREE,
  INDEX `idx_expires_at` (`expires_at` ASC) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=Dynamic;
