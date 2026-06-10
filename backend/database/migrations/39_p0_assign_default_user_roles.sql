-- P0: user_roles 未割当の非 admin ユーザーに「一般ユーザー」ロールを付与
-- （ロールのメニュー権限は role_menu_permissions で別途管理）

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
INNER JOIN roles r ON r.name = '一般ユーザー' AND r.is_active = 1
WHERE COALESCE(u.role, 'user') != 'admin'
  AND NOT EXISTS (
    SELECT 1 FROM user_roles ur WHERE ur.user_id = u.id
  );
