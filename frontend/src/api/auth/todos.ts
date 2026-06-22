import request from '@/shared/api/request'

export interface UserTodoItem {
  id: number
  content: string
  is_done: number
  created_by?: string | null
  created_at: string
  completed_at: string | null
  updated_at: string
}

export interface UserTodoListResponse {
  list: UserTodoItem[]
  pending_count: number
}

export const getUserTodos = (limit = 200) => {
  return request.get<any, UserTodoListResponse>('/api/auth/todos', { params: { limit } })
}

export const createUserTodo = (content: string) => {
  return request.post<any, UserTodoItem>('/api/auth/todos', { content })
}

export const updateUserTodo = (
  id: number,
  payload: { content?: string; is_done?: number },
) => {
  return request.patch<any, UserTodoItem>(`/api/auth/todos/${id}`, payload)
}

export const deleteUserTodo = (id: number) => {
  return request.delete(`/api/auth/todos/${id}`)
}

export const clearCompletedUserTodos = () => {
  return request.delete<any, { deleted_count: number }>('/api/auth/todos/completed')
}
