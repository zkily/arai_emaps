<template>
  <el-dialog v-model="dialogVisible" title="📥 日订单一括取込" width="800px">
    <div class="order-batch-import">
      <el-upload class="upload-area" action="" :http-request="handleUpload" :show-file-list="false" drag>
        <i class="el-icon-upload" />
        <div class="el-upload__text">クリックまたはドラッグしてファイルをアップロード</div>
        <div class="el-upload__tip">Excel (.xlsx) に対応</div>
      </el-upload>

      <el-divider />

      <div v-if="importData.length > 0">
        <h3>📋 プレビュー</h3>
        <el-table :data="importData" border stripe>
          <el-table-column prop="destination_cd" label="納入先CD" />
          <el-table-column prop="order_date" label="注文日" />
          <el-table-column prop="product_cd" label="製品CD" />
          <el-table-column prop="product_name" label="製品名" />
          <el-table-column prop="order_quantity" label="数量" />
          <el-table-column prop="unit" label="単位" />
        </el-table>

        <el-button type="primary" class="confirm-btn" @click="confirmImport">
          ✅ 取込実行
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'

const props = defineProps<{ visible: boolean; destination_cd: string }>()
const emit = defineEmits(['update:visible', 'imported'])

const dialogVisible = ref(props.visible)
watch(() => props.visible, (val) => dialogVisible.value = val)
watch(dialogVisible, (val) => emit('update:visible', val))

interface ImportDataItem {
  destination_cd: string
  order_date: string
  product_cd: string
  product_name: string
  order_quantity: number
  unit: string
}

const importData = ref<ImportDataItem[]>([])

const handleUpload = async (options: { file: File }) => {
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    formData.append('destination_cd', props.destination_cd)   // ✅ 纳入先CD带过去

    const res = await request.post('/api/order/import-batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    importData.value = res
    ElMessage.success('ファイル解析成功')
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : 'アップロード失敗'
    ElMessage.error(errorMessage)
  }
}

const confirmImport = async () => {
  try {
    await request.post('/api/order/import-batch/confirm', { data: importData.value })
    ElMessage.success('取込完了')
    importData.value = []
    emit('imported')
    dialogVisible.value = false
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : '取込失敗'
    ElMessage.error(errorMessage)
  }
}
</script>

<style scoped>
.order-batch-import {
  padding: 10px;
}

.upload-area {
  margin-bottom: 20px;
}

.confirm-btn {
  margin-top: 15px;
}
</style>
