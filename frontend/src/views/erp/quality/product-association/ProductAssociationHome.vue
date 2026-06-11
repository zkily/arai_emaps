<template>
  <div class="product-association-home">
    <el-empty description="製品関連ページは準備中です" />
  </div>
</template>

<script setup lang="ts">import { useQualityOperationPermission } from '@/composables/useQualityOperationPermission'
import { guardQualityOperation } from '@/utils/qualityOperationGuard'

const { canCreate, canEdit, canDelete, canExport, canApprove } = useQualityOperationPermission()


</script>

<style scoped>
.product-association-home {
  padding: 24px;
  background: #fff;
  border-radius: 8px;
}
</style>
