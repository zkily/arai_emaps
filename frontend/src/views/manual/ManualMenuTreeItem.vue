<!--
  ManualHome 左サイドバー：マニュアルをツリーで常時表示する（既定は全展開、フォルダはクリックで開閉）。
  フォルダ＝分類 / menuConfig の親メニュー、リーフ＝マニュアル。配色は親要素の --sc / --sc-rgb を使う。
-->
<template>
  <div
    v-if="node.manual"
    class="mmt-leaf"
    :class="{ 'is-active': node.manual.slug === activeSlug }"
    :title="node.manual.pageTitle"
    @click="emit('select', node.manual.slug)"
  >
    <span class="mmt-leaf__label">{{ node.manual.pageTitle }}</span>
    <span v-if="node.manual.pdfFile" class="mmt-leaf__pdf">PDF</span>
  </div>

  <div v-else class="mmt-folder-wrap">
    <div
      class="mmt-folder"
      :class="[`mmt-folder--depth-${Math.min(depth, 1)}`, { 'is-opened': isOpen }]"
      role="button"
      tabindex="0"
      :aria-expanded="isOpen"
      @click="emit('toggle', node.key)"
      @keydown.enter.prevent="emit('toggle', node.key)"
    >
      <span class="mmt-folder__label" :title="node.name">{{ node.name }}</span>
      <el-icon class="mmt-folder__arrow"><ArrowRight /></el-icon>
    </div>
    <el-collapse-transition>
      <div v-show="isOpen" class="mmt-children" :class="{ 'mmt-children--nested': depth > 0 }">
        <ManualMenuTreeItem
          v-for="child in node.children"
          :key="child.key"
          :node="child"
          :depth="depth + 1"
          :active-slug="activeSlug"
          :collapsed-keys="collapsedKeys"
          @select="emit('select', $event)"
          @toggle="emit('toggle', $event)"
        />
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'
import type { OperationManualTreeNode } from '@/config/operationManuals'

defineOptions({ name: 'ManualMenuTreeItem' })

const props = withDefaults(
  defineProps<{
    node: OperationManualTreeNode
    activeSlug: string
    /** 閉じているフォルダのキー（既定は空＝全展開） */
    collapsedKeys: string[]
    depth?: number
  }>(),
  { depth: 0 },
)

const emit = defineEmits<{
  (e: 'select', slug: string): void
  (e: 'toggle', key: string): void
}>()

const isOpen = computed(() => !props.collapsedKeys.includes(props.node.key))
</script>

<style scoped>
/* ---------- フォルダ ---------- */
.mmt-folder {
  position: relative;
  display: flex;
  align-items: center;
  margin: 2px 0;
  padding: 0 26px 0 10px;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
  outline: none;
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

/* 分類（ルート） */
.mmt-folder--depth-0 {
  height: 34px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.03em;
  color: rgb(var(--sc-rgb));
  background: linear-gradient(90deg, rgba(var(--sc-rgb), 0.16) 0%, rgba(255, 255, 255, 0.55) 100%);
  box-shadow: inset 0 0 0 1px rgba(var(--sc-rgb), 0.14);
}

.mmt-folder--depth-0::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 3px;
  height: 18px;
  border-radius: 0 3px 3px 0;
  background: var(--sc);
  transform: translateY(-50%);
}

/* 親メニュー */
.mmt-folder--depth-1 {
  height: 30px;
  font-size: 12.5px;
  font-weight: 700;
  color: #334155;
}

.mmt-folder--depth-1:hover,
.mmt-folder--depth-1:focus-visible {
  color: #0f172a;
  background: rgba(var(--sc-rgb), 0.1);
}

.mmt-folder--depth-0:hover,
.mmt-folder--depth-0:focus-visible {
  background: linear-gradient(90deg, rgba(var(--sc-rgb), 0.24) 0%, rgba(255, 255, 255, 0.7) 100%);
}

.mmt-folder__label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mmt-folder__arrow {
  position: absolute;
  right: 9px;
  top: 50%;
  margin-top: -6px;
  font-size: 12px;
  color: #94a3b8;
  transition:
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1),
    color 0.15s ease;
}

.mmt-folder:hover .mmt-folder__arrow,
.mmt-folder.is-opened .mmt-folder__arrow {
  color: var(--sc);
}

.mmt-folder.is-opened .mmt-folder__arrow {
  transform: rotate(90deg);
}

/* ---------- 子階層 ---------- */
.mmt-children {
  padding: 2px 0 4px;
}

.mmt-children--nested {
  margin-left: 10px;
  padding-left: 6px;
  border-left: 1px dashed rgba(var(--sc-rgb), 0.35);
}

/* ---------- リーフ（マニュアル） ---------- */
.mmt-leaf {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 30px;
  margin: 1px 0;
  padding: 5px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12.5px;
  line-height: 1.4;
  color: #475569;
  transition:
    background-color 0.15s ease,
    color 0.15s ease;
}

.mmt-leaf:hover {
  color: #0f172a;
  background: rgba(255, 255, 255, 0.75);
  box-shadow: inset 0 0 0 1px rgba(var(--sc-rgb), 0.2);
}

.mmt-leaf.is-active {
  color: #fff;
  font-weight: 700;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0) 60%),
    rgb(var(--sc-rgb));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.25),
    inset 0 -2px 0 rgba(0, 0, 0, 0.12),
    0 4px 10px -4px rgba(var(--sc-rgb), 0.6);
}

.mmt-leaf__label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mmt-leaf__pdf {
  flex-shrink: 0;
  padding: 0 6px;
  border-radius: 999px;
  font-size: 9.5px;
  font-weight: 800;
  line-height: 16px;
  letter-spacing: 0.04em;
  color: #92400e;
  background: #fde68a;
}
</style>
