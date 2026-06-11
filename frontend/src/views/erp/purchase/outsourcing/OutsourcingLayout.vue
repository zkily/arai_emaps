<template>
  <div class="outsourcing-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


// 外注管理のレイアウト：子ルートを router-view に表示。
</script>

<style scoped>
.outsourcing-layout {
  min-height: 100%;
  width: 100%;
}
</style>
