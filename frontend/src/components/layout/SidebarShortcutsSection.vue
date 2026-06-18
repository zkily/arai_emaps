<template>
  <el-sub-menu v-if="shortcutsStore.hasShortcuts" index="SIDEBAR_SHORTCUTS" class="shortcuts-submenu">
    <template #title>
      <SidebarCollapsedEntry
        code="SHORTCUTS"
        :label="t('sidebar.SHORTCUTS')"
        :is-collapsed="isCollapsed"
      >
        <el-icon><Star /></el-icon>
      </SidebarCollapsedEntry>
    </template>

    <el-menu-item
      v-for="item in shortcutsStore.pinned"
      :key="'pin-' + item.path"
      :index="item.path"
      class="shortcut-item shortcut-item--pinned"
    >
      <el-icon class="shortcut-kind-icon"><StarFilled /></el-icon>
      <template #title>
        <span class="shortcut-label" :title="labelForItem(item)">{{ labelForItem(item) }}</span>
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
        <span class="shortcut-label" :title="labelForItem(item)">{{ labelForItem(item) }}</span>
      </template>
    </el-menu-item>
  </el-sub-menu>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { Star, StarFilled, Clock } from '@element-plus/icons-vue'
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

onMounted(() => {
  if (userStore.isAuthenticated && !shortcutsStore.loaded) {
    void shortcutsStore.load()
  }
})
</script>

<style scoped>
:deep(.shortcuts-submenu > .el-sub-menu__title) {
  height: 40px;
  line-height: 40px;
  margin: 4px 6px 4px 0;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9) !important;
  background: linear-gradient(90deg, rgba(251, 191, 36, 0.14) 0%, rgba(251, 191, 36, 0.05) 100%) !important;
  border-left: 3px solid rgba(251, 191, 36, 0.75);
}

:deep(.shortcut-item) {
  height: 36px !important;
  line-height: 36px !important;
  font-size: 13px !important;
  margin: 2px 6px 2px 0 !important;
  border-radius: 6px !important;
}

:deep(.shortcut-item--pinned) {
  background: rgba(251, 191, 36, 0.08) !important;
}

:deep(.shortcut-item--frequent) {
  background: rgba(96, 165, 250, 0.08) !important;
}

:deep(.shortcut-item--frequent:first-of-type) {
  margin-top: 4px !important;
}

.shortcut-kind-icon {
  margin-right: 6px;
  font-size: 14px;
  opacity: 0.85;
}

.shortcut-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
