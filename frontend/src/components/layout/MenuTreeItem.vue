<!--
  menuConfig 由来のメニューツリーを再帰描画する。
  子を持つノードは el-sub-menu、リーフ（path あり）は el-menu-item。
  ラベルは i18n の menu.<CODE> を使用。アイコンは main.ts でグローバル登録済みの
  Element Plus アイコン名を component :is で解決する。
-->
<template>
  <el-sub-menu v-if="node.children && node.children.length" :index="node.code">
    <template #title>
      <SidebarCollapsedEntry
        v-if="depth === 0"
        :code="node.code"
        :label="label"
        :is-collapsed="isCollapsed"
      >
        <el-icon><component :is="node.icon || 'Menu'" /></el-icon>
      </SidebarCollapsedEntry>
      <template v-else>
        <el-icon><component :is="node.icon || 'Menu'" /></el-icon>
        <span :title="label">{{ label }}</span>
      </template>
    </template>
    <MenuTreeItem
      v-for="child in node.children"
      :key="child.code"
      :node="child"
      :depth="depth + 1"
      :is-collapsed="isCollapsed"
    />
  </el-sub-menu>

  <el-menu-item v-else-if="node.path" :index="node.path" class="menu-tree-leaf">
    <el-icon><component :is="node.icon || 'Menu'" /></el-icon>
    <template #title>
      <span class="menu-tree-leaf__row">
        <span class="menu-tree-leaf__label" :title="label">{{ label }}</span>
        <button
          type="button"
          class="menu-tree-leaf__pin"
          :class="{ 'is-pinned': isPinned }"
          :title="isPinned ? t('sidebar.UNPIN') : t('sidebar.PIN')"
          @click.stop="handleTogglePin"
        >
          <el-icon><component :is="isPinned ? 'StarFilled' : 'Star'" /></el-icon>
        </button>
      </span>
    </template>
  </el-menu-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MenuTreeNode } from '@/composables/useMenuTree'
import SidebarCollapsedEntry from '@/components/layout/SidebarCollapsedEntry.vue'
import { useSidebarShortcutsStore } from '@/stores/sidebarShortcuts'

const props = withDefaults(
  defineProps<{
    node: MenuTreeNode
    isCollapsed?: boolean
    depth?: number
  }>(),
  { isCollapsed: false, depth: 0 },
)

const { t } = useI18n()
const shortcutsStore = useSidebarShortcutsStore()

const label = computed(() => {
  const key = `menu.${props.node.code}`
  const translated = t(key)
  // 翻訳キーが無い場合は menuConfig の name にフォールバック
  return translated === key ? props.node.name : translated
})

const isPinned = computed(() => {
  if (!props.node.path) return false
  return shortcutsStore.isPinned(props.node.path)
})

const handleTogglePin = () => {
  if (!props.node.path) return
  void shortcutsStore.togglePin(props.node.path)
}
</script>

<style scoped>
.menu-tree-leaf__row {
  display: flex;
  align-items: center;
  min-width: 0;
  width: 100%;
  gap: 4px;
}

.menu-tree-leaf__label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-tree-leaf__pin {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease, background 0.15s ease;
}

:deep(.menu-tree-leaf:hover) .menu-tree-leaf__pin,
.menu-tree-leaf__pin.is-pinned {
  opacity: 1;
}

.menu-tree-leaf__pin:hover {
  color: #fbbf24;
  background: rgba(251, 191, 36, 0.15);
}

.menu-tree-leaf__pin.is-pinned {
  color: #fbbf24;
}
</style>
