import request from '@/shared/api/request'

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

// ユーザー情報取得
export const getUserInfo = () => {
  return request.get('/api/auth/me')
}

