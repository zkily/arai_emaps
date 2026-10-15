<template>
  <el-dialog
    v-model="visible"
    width="520px"
    align-center
    :show-close="false"
    :close-on-click-modal="false"
    class="process-select-dialog pb-std"
    destroy-on-close
  >
    <template #header>
      <div class="dlg-header">
        <div class="dlg-header-icon">
          <el-icon :size="20"><Tools /></el-icon>
        </div>
        <div class="dlg-header-text">
          <h3 class="dlg-title">工程選択</h3>
          <p class="dlg-subtitle">追加する工程を一覧から選択してください</p>
        </div>
      </div>
    </template>

    <el-input
      v-model="searchKeyword"
      placeholder="工程CD・名称で検索"
      clearable
      size="small"
      class="smart-search-box"
      :prefix-icon="Search"
    />
    <el-table
      :data="filteredProcesses"
      border
      stripe
      height="340"
      size="small"
      class="modern-table"
      style="margin-top: 10px"
    >
      <el-table-column prop="process_cd" label="工程CD" width="120">
        <template #default="{ row }">
          <span class="code-chip">{{ row.process_cd }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="process_name" label="工程名" show-overflow-tooltip />
      <el-table-column label="操作" width="96" align="center">
        <template #default="scope">
          <el-button class="pick-btn" size="small" @click="selectProcess(scope.row)">選択</el-button>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <div class="smart-footer">
        <el-button class="dlg-btn dlg-btn--cancel" @click="close">閉じる</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Tools, Search } from '@element-plus/icons-vue'
import request from '@/shared/api/request'

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
  set: (val) => emit('update:visible', val),
})

const processes = ref<Process[]>([])
const searchKeyword = ref('')

watch(
  () => visible.value,
  async (val) => {
    if (val) {
      const res = await request.get('/api/master/product/process/routes')
      processes.value = Array.isArray(res) ? res : res?.data ?? []
      searchKeyword.value = ''
    }
  },
)

const filteredProcesses = computed(() => {
  if (!searchKeyword.value) return processes.value
  const keyword = searchKeyword.value.toLowerCase()
  return processes.value.filter(
    (p) =>
      p.process_cd.toLowerCase().includes(keyword) ||
      p.process_name?.toLowerCase().includes(keyword),
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
.dlg-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 18px;
  background: linear-gradient(125deg, #4c1d95 0%, #6d28d9 45%, #8b5cf6 100%);
}
.dlg-header-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.28), rgba(255, 255, 255, 0.1));
}
.dlg-title {
  margin: 0;
  font-size: 15px;
  font-weight: 800;
  color: #fff;
}
.dlg-subtitle {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.86);
}

.smart-search-box :deep(.el-input__wrapper) {
  border-radius: 9px;
  background: #fff;
  box-shadow: 0 0 0 1px #e2e8f0 inset;
}
.smart-search-box :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px #8b5cf6 inset,
    0 0 0 3px rgba(139, 92, 246, 0.15);
}

.modern-table :deep(.el-table__header th) {
  background: linear-gradient(180deg, #faf5ff 0%, #f5f3ff 100%) !important;
  color: #5b21b6 !important;
  font-weight: 700;
}

.code-chip {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 6px;
  font-weight: 700;
  font-size: 12px;
  color: #6d28d9;
  background: #f5f3ff;
  box-shadow: inset 0 0 0 1px #ddd6fe;
}

.pick-btn {
  border-radius: 999px !important;
  font-weight: 700 !important;
  color: #5b21b6 !important;
  background: #ede9fe !important;
  border: 1px solid #c4b5fd !important;
}
.pick-btn:hover {
  color: #fff !important;
  background: linear-gradient(135deg, #8b5cf6, #6d28d9) !important;
  border-color: transparent !important;
}

.smart-footer {
  display: flex;
  justify-content: flex-end;
  padding: 10px 14px;
  background: #fff;
  border-top: 1px solid #ede9fe;
}
.dlg-btn {
  border-radius: 999px;
  font-weight: 700;
  font-size: 12px;
  padding: 7px 16px;
  height: auto;
}
.dlg-btn--cancel {
  background: #fff;
  border: 1px solid #e2e8f0;
  color: #64748b;
}
</style>

<style>
/* append-to-body のダイアログ枠（scoped 外） */
.process-select-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.22);
}
.process-select-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
}
.process-select-dialog .el-dialog__body {
  padding: 12px 14px;
  background: linear-gradient(180deg, #faf5ff 0%, #f8fafc 100%);
}
.process-select-dialog .el-dialog__footer {
  padding: 0;
}
</style>
