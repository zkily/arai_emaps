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

  <el-menu-item v-else-if="node.path" :index="node.path">
    <el-icon><component :is="node.icon || 'Menu'" /></el-icon>
    <template #title><span :title="label">{{ label }}</span></template>
  </el-menu-item>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MenuTreeNode } from '@/composables/useMenuTree'
import SidebarCollapsedEntry from '@/components/layout/SidebarCollapsedEntry.vue'

const props = withDefaults(
  defineProps<{
    node: MenuTreeNode
    isCollapsed?: boolean
    depth?: number
  }>(),
  { isCollapsed: false, depth: 0 },
)

const { t } = useI18n()

const label = computed(() => {
  const key = `menu.${props.node.code}`
  const translated = t(key)
  // 翻訳キーが無い場合は menuConfig の name にフォールバック
  return translated === key ? props.node.name : translated
})
</script>
