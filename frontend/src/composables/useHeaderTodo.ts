import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/modules/auth/stores/user'
import * as todosApi from '@/api/auth/todos'
import type { UserTodoItem } from '@/api/auth/todos'

export type { UserTodoItem }

export function useHeaderTodo() {
  const { t } = useI18n()
  const userStore = useUserStore()
  const items = ref<UserTodoItem[]>([])
  const draft = ref('')
  const loading = ref(false)
  const submitting = ref(false)

  const pendingCount = computed(() => items.value.filter((item) => item.is_done !== 1).length)
  const doneCount = computed(() => items.value.filter((item) => item.is_done === 1).length)

  const sortedItems = computed(() =>
    [...items.value].sort((a, b) => {
      if (a.is_done !== b.is_done) return a.is_done - b.is_done
      return b.created_at.localeCompare(a.created_at)
    }),
  )

  async function reload() {
    if (!userStore.isAuthenticated) {
      items.value = []
      return
    }
    loading.value = true
    try {
      const data = await todosApi.getUserTodos()
      items.value = data.list ?? []
    } catch {
      ElMessage.error(t('common.headerTodoLoadFailed'))
    } finally {
      loading.value = false
    }
  }

  watch(
    () => userStore.user?.id,
    () => {
      void reload()
    },
    { immediate: true },
  )

  async function addItem(content?: string) {
    const text = (content ?? draft.value).trim()
    if (!text || submitting.value) return false
    submitting.value = true
    try {
      const created = await todosApi.createUserTodo(text)
      items.value.unshift(created)
      draft.value = ''
      return true
    } catch {
      ElMessage.error(t('common.headerTodoAddFailed'))
      return false
    } finally {
      submitting.value = false
    }
  }

  async function toggleItem(id: number) {
    const item = items.value.find((row) => row.id === id)
    if (!item) return
    const nextDone = item.is_done === 1 ? 0 : 1
    try {
      const updated = await todosApi.updateUserTodo(id, { is_done: nextDone })
      Object.assign(item, updated)
    } catch {
      ElMessage.error(t('common.headerTodoUpdateFailed'))
    }
  }

  async function updateContent(id: number, content: string) {
    const text = content.trim()
    if (!text) return false
    const item = items.value.find((row) => row.id === id)
    if (!item || item.content === text) return false
    try {
      const updated = await todosApi.updateUserTodo(id, { content: text })
      Object.assign(item, updated)
      return true
    } catch {
      ElMessage.error(t('common.headerTodoUpdateFailed'))
      return false
    }
  }

  async function removeItem(id: number) {
    try {
      await todosApi.deleteUserTodo(id)
      items.value = items.value.filter((row) => row.id !== id)
    } catch {
      ElMessage.error(t('common.headerTodoDeleteFailed'))
    }
  }

  async function clearDone() {
    if (doneCount.value === 0) return
    try {
      await todosApi.clearCompletedUserTodos()
      items.value = items.value.filter((row) => row.is_done !== 1)
    } catch {
      ElMessage.error(t('common.headerTodoClearFailed'))
    }
  }

  return {
    items,
    draft,
    loading,
    submitting,
    pendingCount,
    doneCount,
    sortedItems,
    addItem,
    toggleItem,
    updateContent,
    removeItem,
    clearDone,
    reload,
  }
}
