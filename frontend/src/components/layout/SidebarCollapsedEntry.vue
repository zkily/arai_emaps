<template>
  <div class="sidebar-collapsed-entry" :class="{ 'is-collapsed': isCollapsed }">
    <slot />
    <div v-if="isCollapsed" class="sidebar-collapsed-entry__label">{{ shortLabel }}</div>
    <span v-else-if="showTitle" class="sidebar-collapsed-entry__title" :title="label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { collapsedSidebarLabel } from '@/utils/collapsedSidebarLabel'

const props = withDefaults(
  defineProps<{
    code: string
    label: string
    isCollapsed: boolean
    /** menu-item 展开时标题在 #title 插槽，默认槽仅放图标 */
    showTitle?: boolean
  }>(),
  { showTitle: true },
)

const shortLabel = computed(() => collapsedSidebarLabel(props.code, props.label))
</script>

<style scoped>
.sidebar-collapsed-entry {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  flex: 1;
  gap: 8px;
}

.sidebar-collapsed-entry.is-collapsed {
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  width: 100%;
  flex: none;
}

.sidebar-collapsed-entry__label {
  font-size: 10px;
  line-height: 12px;
  text-align: center;
  max-width: 100%;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sidebar-collapsed-entry__title {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
