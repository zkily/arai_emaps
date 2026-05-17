<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  scannedCode: string
  managementCode?: string | null
}>()

const { t } = useI18n()

const popoverTrigger = ref<'hover' | 'click'>('hover')
let touchMq: MediaQueryList | null = null

function syncPopoverTrigger(): void {
  if (typeof window === 'undefined') return
  popoverTrigger.value = window.matchMedia('(hover: none) and (pointer: coarse)').matches
    ? 'click'
    : 'hover'
}

onMounted(() => {
  syncPopoverTrigger()
  if (typeof window !== 'undefined') {
    touchMq = window.matchMedia('(hover: none) and (pointer: coarse)')
    touchMq.addEventListener('change', syncPopoverTrigger)
  }
})

onUnmounted(() => {
  touchMq?.removeEventListener('change', syncPopoverTrigger)
  touchMq = null
})
</script>

<template>
  <el-popover
    :trigger="popoverTrigger"
    placement="top"
    :width="320"
    popper-class="plan-scan-registration-popper"
    :show-after="popoverTrigger === 'hover' ? 120 : 0"
  >
    <template #reference>
      <span class="scan-registered-hint" role="button" tabindex="0" @click.stop>
        {{ t('mesChamferingActual.scanRegistered') }}
      </span>
    </template>
    <div class="plan-scan-tip">
      <p class="plan-scan-tip__title">{{ t('mesChamferingActual.scanCurrentCodeLabel') }}</p>
      <p class="plan-scan-tip__code">{{ scannedCode }}</p>
      <p v-if="(managementCode ?? '').trim()" class="plan-scan-tip__sub">
        {{ t('mesChamferingActual.managementCode') }}: {{ managementCode }}
      </p>
      <p class="plan-scan-tip__note">{{ t('mesChamferingActual.scanOverwriteHint') }}</p>
    </div>
  </el-popover>
</template>

<style scoped>
.scan-registered-hint {
  display: inline-flex;
  align-items: center;
  padding: 0 6px;
  height: 22px;
  border-radius: 4px;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--el-color-success);
  background: var(--el-color-success-light-9);
  border: 1px solid var(--el-color-success-light-5);
  line-height: 1;
  flex-shrink: 0;
  cursor: help;
}

.scan-registered-hint:focus-visible {
  outline: 2px solid var(--el-color-primary);
  outline-offset: 1px;
}
</style>

<style>
.plan-scan-registration-popper .plan-scan-tip__title {
  margin: 0 0 4px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.plan-scan-registration-popper .plan-scan-tip__code {
  margin: 0 0 6px;
  font-size: 0.85rem;
  font-weight: 600;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  word-break: break-all;
  color: var(--el-text-color-primary);
  line-height: 1.35;
}

.plan-scan-registration-popper .plan-scan-tip__sub {
  margin: 0 0 6px;
  font-size: 0.78rem;
  color: var(--el-text-color-regular);
  word-break: break-all;
}

.plan-scan-registration-popper .plan-scan-tip__note {
  margin: 0;
  font-size: 0.72rem;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}
</style>
