<template>
  <el-sub-menu
    v-if="shortcutsStore.hasShortcuts"
    index="SIDEBAR_SHORTCUTS"
    class="shortcuts-submenu"
    popper-class="sbm-popper sbm-popper--shortcuts"
  >
    <template #title>
      <SidebarCollapsedEntry
        code="SHORTCUTS"
        :label="t('sidebar.SHORTCUTS')"
        :is-collapsed="isCollapsed"
      >
        <el-icon><Star /></el-icon>
      </SidebarCollapsedEntry>
    </template>

    <li class="sbm-popup-head" role="presentation">
      <i class="sbm-popup-head__dot" />
      <span>{{ t('sidebar.SHORTCUTS') }}</span>
    </li>

    <el-menu-item
      v-for="item in shortcutsStore.pinned"
      :key="'pin-' + item.path"
      :index="item.path"
      class="shortcut-item shortcut-item--pinned"
    >
      <el-icon class="shortcut-kind-icon"><StarFilled /></el-icon>
      <template #title>
        <span class="shortcut-row">
          <span class="shortcut-label" :title="labelForItem(item)">{{ labelForItem(item) }}</span>
          <button
            type="button"
            class="shortcut-remove"
            :title="t('sidebar.REMOVE_SHORTCUT')"
            :aria-label="t('sidebar.REMOVE_SHORTCUT')"
            @click.stop="handleRemove(item)"
          >
            <el-icon><Close /></el-icon>
          </button>
        </span>
      </template>
    </el-menu-item>

    <el-menu-item
      v-for="item in shortcutsStore.frequent"
      :key="'freq-' + item.path"
      :index="item.path"
      class="shortcut-item shortcut-item--frequent"
    >
      <el-icon class="shortcut-kind-icon"><Clock /></el-icon>
      <template #title>
        <span class="shortcut-row">
          <span class="shortcut-label" :title="labelForItem(item)">{{ labelForItem(item) }}</span>
          <button
            type="button"
            class="shortcut-remove"
            :title="t('sidebar.REMOVE_SHORTCUT')"
            :aria-label="t('sidebar.REMOVE_SHORTCUT')"
            @click.stop="handleRemove(item)"
          >
            <el-icon><Close /></el-icon>
          </button>
        </span>
      </template>
    </el-menu-item>
  </el-sub-menu>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Star, StarFilled, Clock, Close } from '@element-plus/icons-vue'
import SidebarCollapsedEntry from '@/components/layout/SidebarCollapsedEntry.vue'
import { useSidebarShortcutsStore } from '@/stores/sidebarShortcuts'
import { useMenuLabel } from '@/composables/useMenuLabel'
import type { ShortcutItem } from '@/api/auth/shortcuts'
import { useUserStore } from '@/modules/auth/stores/user'

defineProps<{
  isCollapsed: boolean
}>()

const { t } = useI18n()
const shortcutsStore = useSidebarShortcutsStore()
const userStore = useUserStore()
const { labelForPath } = useMenuLabel()

const labelForItem = (item: ShortcutItem) => labelForPath(item.path, item.menu_code)

const handleRemove = async (item: ShortcutItem) => {
  try {
    await shortcutsStore.removeShortcut(item.path)
    ElMessage.success(String(t('sidebar.SHORTCUT_REMOVED', { name: labelForItem(item) })))
  } catch {
    ElMessage.error(String(t('sidebar.SHORTCUT_REMOVE_FAILED')))
  }
}

onMounted(() => {
  if (userStore.isAuthenticated && !shortcutsStore.loaded) {
    void shortcutsStore.load()
  }
})
</script>

<style scoped>
.shortcut-kind-icon {
  margin-right: 6px;
  font-size: 14px;
}

.shortcut-row {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
  min-width: 0;
}

.shortcut-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shortcut-remove {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: transparent !important;
  box-shadow: none !important;
  outline: none;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  opacity: 0;
  transition:
    opacity 0.15s ease,
    color 0.15s ease,
    background-color 0.15s ease;
}

.shortcut-remove:focus-visible {
  opacity: 1;
}

.shortcut-remove:hover {
  color: #fecaca;
  background: rgba(248, 113, 113, 0.22) !important;
}

.shortcut-remove :deep(.el-icon) {
  width: auto;
  margin: 0;
  font-size: 13px;
}
</style>
