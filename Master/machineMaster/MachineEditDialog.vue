<template>
  <el-dialog v-model="visible" :title="''" width="520px" class="machine-dialog" :close-on-click-modal="false">
    <div class="dialog-title">
      <span class="icon">🛠️</span>
      <span>設備編集</span>
    </div>
    <el-form :model="form" label-width="120px" class="form-section card-section">
      <el-form-item label="設備CD">
        <el-input v-model="form.machine_cd" />
      </el-form-item>
      <el-form-item label="設備名">
        <el-input v-model="form.machine_name" />
      </el-form-item>
      <el-form-item label="設備タイプ">
        <el-select v-model="form.machine_type" placeholder="選択してください" style="width: 100%">
          <el-option label="切断" value="切断" />
          <el-option label="面取" value="面取" />
          <el-option label="SW" value="SW" />
          <el-option label="成型" value="成型" />
          <el-option label="溶接" value="溶接" />
          <el-option label="メッキ" value="メッキ" />
          <el-option label="検査" value="検査" />
          <el-option label="溶接前検査" value="溶接前検査" />
          <el-option label="外注切断" value="外注切断" />
          <el-option label="外注成型" value="外注成型" />
          <el-option label="外注メッキ" value="外注メッキ" />
          <el-option label="外注溶接" value="外注溶接" />
          <el-option label="外注検査" value="外注検査" />
        </el-select>
      </el-form-item>
      <el-form-item label="効率（%）">
        <el-input-number v-model="form.efficiency" :min="0" :max="300" />
      </el-form-item>
      <el-form-item label="状態">
        <el-select v-model="form.status">
          <el-option label="稼働中" value="active" />
          <el-option label="修理中" value="maintenance" />
          <el-option label="停止中" value="inactive" />
        </el-select>
      </el-form-item>
      <el-form-item label="可用時間">
        <el-time-picker v-model="form.available_from" placeholder="00:00:00" style="width: 100px" />
        〜
        <el-time-picker v-model="form.available_to" placeholder="23:59:59" style="width: 100px" />
      </el-form-item>
      <el-form-item label="備考">
        <el-input type="textarea" v-model="form.note" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { createMachine, updateMachine } from '@/api/master/machineMaster'
import { Machine } from '@/types/master'


const props = defineProps<{
  modelValue: boolean
  machine: Machine | null
}>()
const emit = defineEmits(['update:modelValue', 'saved'])

const visible = ref(false)
watch(() => props.modelValue, val => (visible.value = val))
watch(() => visible.value, val => emit('update:modelValue', val))

const form = ref<Partial<Machine>>({})

watch(() => props.machine, val => {
  form.value = val ? { ...val } : {}
})

function handleSave() {
  const data = form.value
  if (data.id) {
    updateMachine(data.id, data).then(() => {
      emit('saved')
      visible.value = false
    })
  } else {
    createMachine(data).then(() => {
      emit('saved')
      visible.value = false
    })
  }
}
</script>

<style scoped>
.machine-dialog :deep(.el-dialog) {
  border-radius: 16px;
}

.dialog-title {
  font-size: 22px;
  font-weight: bold;
  color: #2c3e50;
  padding: 20px 24px 12px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(to right, #e6f7ff, #ffffff);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-title .icon {
  margin-right: 8px;
  font-size: 22px;
}

.card-section {
  background: #fafafa;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 18px;
  padding: 24px 18px 10px 18px;
}

.form-section {
  padding: 0;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 10px;
}

@media (max-width: 600px) {
  .machine-dialog :deep(.el-dialog) {
    width: 99vw !important;
    min-width: 0;
  }

  .card-section {
    padding: 6px 2px 4px 2px;
  }

  .dialog-title {
    font-size: 18px;
    padding: 14px 10px 8px 10px;
  }
}
</style>
