/**
 * レイアウト関連 API（ログイン等）を一元管理
 * layouts/pages と対応し、ルート・API・バックエンドを同じ方法で管理
 */
export {
  login,
  logout,
  getUserInfo,
  type LoginParams,
  type LoginResponse,
} from '@/api/auth'
