import request from '@/shared/api/request'
import type { User } from '@/modules/auth/stores/user'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: {
    id: number
    username: string
    email: string
    full_name?: string
    role: string
    permissions: string[]
    is_active?: boolean
    department_id?: number | null
    department_name?: string | null
  }
}

// ログイン
export const login = (data: LoginParams) => {
  return request.post<any, LoginResponse>('/api/auth/login', data)
}

// ログアウト
export const logout = () => {
  return request.post('/api/auth/logout')
}

// ユーザー情報取得（インターセプターで response.data を返す）
export const getUserInfo = (): Promise<User> => {
  return request.get('/api/auth/me') as Promise<User>
}

