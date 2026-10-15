<template>
  <div class="part-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">import { usePurchaseOperationPermission } from '@/composables/usePurchaseOperationPermission'
import { guardPurchaseOperation } from '@/utils/purchaseOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = usePurchaseOperationPermission()


</script>

<style scoped>
.part-layout {
  width: 100%;
  min-height: 100%;
}
</style>
