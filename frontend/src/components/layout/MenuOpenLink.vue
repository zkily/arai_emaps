<!--
  メニュー葉項目の実リンク。通常クリックは親の el-menu select に任せ、
  ドラッグ / Ctrl+クリック / 中クリックはブラウザの新規タブで開く。
-->
<template>
  <a
    class="menu-open-link"
    :href="href"
    draggable="true"
    @mousedown="onMouseDown"
    @click="onMenuLinkClick"
    @auxclick="onAuxClick"
    @dragstart="onDragStart"
  >
    <slot />
  </a>
</template>

<script setup lang="ts">
import { useMenuHref, onMenuLinkClick, onMenuLinkDragStart } from '@/composables/useMenuHref'
import { markMenuTabHandoff } from '@/modules/auth/sessionSync'

const props = defineProps<{
  path: string
}>()

const { href } = useMenuHref(() => props.path)

const onDragStart = (event: DragEvent) => {
  onMenuLinkDragStart(event, href.value)
}

const onMouseDown = (event: MouseEvent) => {
  if (event.button === 1 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
    markMenuTabHandoff()
  }
}

const onAuxClick = (event: MouseEvent) => {
  if (event.button !== 1) return
  markMenuTabHandoff()
  event.stopPropagation()
}
</script>
