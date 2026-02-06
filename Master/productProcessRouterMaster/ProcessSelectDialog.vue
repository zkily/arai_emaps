<template>
  <el-dialog v-model="visible" width="40%" :close-on-click-modal="false" :modal-append-to-body="false"
    class="smart-dialog">
    <!-- 🏷️ カスタムタイトル -->
    <template #header>
      <div class="smart-dialog-header">
        🛠️ <span>工程選択</span>
      </div>
    </template>

    <!-- 🔎 検索 -->
    <el-input v-model="searchKeyword" placeholder="🔎 工程CD・名称で検索" clearable size="small" class="smart-search-box" />

    <!-- 📋 テーブル -->
    <el-table :data="filteredProcesses" border height="340" size="small"
      :header-cell-style="{ fontWeight: 'bold', backgroundColor: '#e6f4ff', color: '#409EFF' }"
      style="margin-top: 12px;">
      <el-table-column prop="process_cd" label="工程CD" width="120" />
      <el-table-column prop="process_name" label="工程名" />
      <el-table-column label="操作" width="90">
        <template #default="scope">
          <el-button type="primary" size="small" @click="selectProcess(scope.row)">選択</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- ✅ フッター -->
    <template #footer>
      <div class="smart-footer">
        <el-button @click="close">閉じる</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import request from '@/utils/request'

interface Process {
  process_cd: string
  process_name: string
}

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'selected', process: Process): void
}>()

const visible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const processes = ref<Process[]>([])
const searchKeyword = ref('')

watch(() => visible.value, async (val) => {
  if (val) {
    processes.value = await request.get('/api/master/product/process/routes')
  }
})

const filteredProcesses = computed(() => {
  if (!searchKeyword.value) return processes.value
  const keyword = searchKeyword.value.toLowerCase()
  return processes.value.filter(
    (p) =>
      p.process_cd.toLowerCase().includes(keyword) ||
      (p.process_name?.toLowerCase().includes(keyword))
  )
})

const selectProcess = (process: Process) => {
  emit('selected', process)
  close()
}

const close = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.smart-dialog {
  border-radius: 12px;
}

.smart-dialog-header {
  font-size: 18px;
  font-weight: bold;
  display: flex;
  align-items: center;
}

.smart-dialog-header span {
  margin-left: 6px;
}

.smart-search-box {
  width: 100%;
  border-radius: 8px;
}

.smart-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
