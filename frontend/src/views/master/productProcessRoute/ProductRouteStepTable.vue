<template>
  <el-card shadow="always" class="route-step-card" v-loading="loading">
    <template #header>
      <div class="header-bar">
        <span>🛠️ 製品別工程ステップ</span>
        <div class="button-group">
          <el-button type="success" size="small" @click="dialogVisible = true" :disabled="loading">
            ➕ 工程追加
          </el-button>
          <el-button type="info" size="small" @click="resetData" :disabled="loading">
            🔄 リセット
          </el-button>
          <el-button
            type="primary"
            size="small"
            @click="saveSteps"
            :disabled="loading || steps.length === 0"
          >
            💾 保存
          </el-button>
        </div>
      </div>
    </template>

    <template v-if="loading && !dataLoaded">
      <div class="loading-message">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>データを読み込み中...</span>
      </div>
    </template>

    <template v-else-if="!loading && dataLoaded && steps.length === 0">
      <div class="empty-message">
        <el-icon><DocumentRemove /></el-icon>
        <p>工程ルート未設定 または ステップがありません</p>
        <el-button type="primary" @click="dialogVisible = true">工程を追加</el-button>
      </div>
    </template>

    <div v-else-if="dataLoaded && steps.length > 0" class="steps-container">
      <draggable
        v-model="steps"
        :animation="200"
        ghost-class="ghost-step"
        chosen-class="chosen-step"
        drag-class="drag-step"
        @start="onStepDragStart"
        @end="onStepDragEnd"
        item-key="step_no"
        class="draggable-steps"
        handle=".drag-handle"
      >
        <template #item="{ element: step, index: stepIndex }">
          <div class="step-card" :class="{ dragging: isDragging }">
            <el-card shadow="hover" class="process-card">
              <template #header>
                <div class="process-header">
                  <div class="drag-handle">
                    <el-icon class="drag-icon"><Rank /></el-icon>
                    <span class="drag-text">ドラッグで並び替え</span>
                  </div>
                  <div class="process-info">
                    <el-tag type="primary" size="small">順序 {{ step.step_no }}</el-tag>
                    <span class="process-code">{{ step.process_cd }}</span>
                    <span class="process-name">{{ step.process_name }}</span>
                    <el-tag v-if="step.id" type="success" size="small">保存済み</el-tag>
                    <el-tag v-else type="warning" size="small">未保存</el-tag>
                  </div>
                  <el-button type="danger" size="small" @click="removeStep(stepIndex)" :disabled="loading">
                    🗑️ 削除
                  </el-button>
                </div>
              </template>

              <div class="machines-section">
                <div class="section-title">
                  <span>
                    🔧 設備一覧
                    <el-tag v-if="step.machines && step.machines.length > 0" type="info" size="small">
                      {{ step.machines.length }}台
                    </el-tag>
                  </span>
                  <el-button type="primary" size="small" @click="addMachine(step)" :disabled="loading">
                    ➕ 設備追加
                  </el-button>
                </div>

                <div v-if="!step.machines || step.machines.length === 0" class="no-machines">
                  <el-icon><Tools /></el-icon>
                  <p>設備が設定されていません</p>
                  <el-button type="primary" size="small" @click="addMachine(step)">設備を追加</el-button>
                </div>

                <div v-else class="machines-grid">
                  <el-card
                    v-for="(machine, idx) in step.machines"
                    :key="machine._uid || machine.id || idx"
                    shadow="never"
                    class="machine-card"
                    :class="{ 'machine-saved': machine.id, 'machine-new': !machine.id }"
                  >
                    <div class="machine-form">
                      <div class="machine-status">
                        <el-tag v-if="machine.id" type="success" size="small">保存済み</el-tag>
                        <el-tag v-else type="warning" size="small">新規</el-tag>
                      </div>
                      <div class="form-row">
                        <div class="form-item">
                          <label class="form-label">設備CD</label>
                          <el-select
                            v-model="machine.machine_cd"
                            filterable
                            placeholder="設備を選択"
                            style="width: 100%"
                            @change="(cd: string) => onMachineChange(step, Number(idx), cd)"
                            :disabled="loading"
                          >
                            <el-option
                              v-for="opt in getFilteredMachines(step.process_name)"
                              :key="opt.machine_cd"
                              :label="`${opt.machine_cd} - ${opt.machine_name}`"
                              :value="opt.machine_cd"
                            />
                            <template
                              v-if="
                                getFilteredMachines(step.process_name).length === 0 && allMachines.length > 0
                              "
                            >
                              <el-option disabled label="--- 全設備 ---" :value="''" />
                              <el-option
                                v-for="opt in allMachines"
                                :key="'all-' + opt.machine_cd"
                                :label="`[全] ${opt.machine_cd} - ${opt.machine_name}`"
                                :value="opt.machine_cd"
                              />
                            </template>
                            <el-option
                              v-if="allMachines.length === 0"
                              key="no-data"
                              label="設備データがありません"
                              :value="''"
                              disabled
                            />
                          </el-select>
                        </div>
                        <div class="form-item">
                          <label class="form-label">設備名</label>
                          <el-input v-model="machine.machine_name" placeholder="設備名" readonly style="width: 100%" />
                        </div>
                      </div>
                      <div class="form-row">
                        <div class="form-item">
                          <label class="form-label">加工時間 (秒)</label>
                          <el-input-number
                            v-model="machine.process_time_sec"
                            :min="0"
                            :step="1"
                            style="width: 100%"
                            :disabled="loading"
                          />
                        </div>
                        <div class="form-item">
                          <label class="form-label">段取り時間 (分)</label>
                          <el-input-number
                            v-model="machine.setup_time"
                            :min="0"
                            :step="1"
                            style="width: 100%"
                            :disabled="loading"
                          />
                        </div>
                      </div>
                      <div class="machine-actions">
                        <el-button
                          v-if="machine.machine_cd"
                          type="success"
                          size="small"
                          @click="updateMachine(step, Number(idx))"
                          :disabled="loading"
                        >
                          {{ machine.id ? '更新' : '保存' }}
                        </el-button>
                        <el-button type="danger" size="small" @click="removeMachine(step, Number(idx))" :disabled="loading">
                          削除
                        </el-button>
                      </div>
                    </div>
                  </el-card>
                </div>
              </div>
            </el-card>
          </div>
        </template>
      </draggable>
    </div>

    <ProcessSelectDialog v-model:visible="dialogVisible" @selected="addProcess" />
  </el-card>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import request from '@/shared/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, DocumentRemove, Tools, Rank } from '@element-plus/icons-vue'
import ProcessSelectDialog from './ProcessSelectDialog.vue'
import draggable from 'vuedraggable'

const props = defineProps<{ productCd: string }>()

interface MachineInfo {
  id?: number
  machine_cd: string
  machine_name: string
  process_time_sec: number
  setup_time: number
  _uid?: string
}

interface ProductRouteStep {
  id?: number
  product_cd: string
  route_cd: string
  step_no: number
  process_cd: string
  process_name: string
  machines?: MachineInfo[]
}

interface Machine {
  machine_cd: string
  machine_name: string
  machine_type?: string
}

const steps = ref<ProductRouteStep[]>([])
const dialogVisible = ref(false)
const allMachines = ref<Machine[]>([])
const loading = ref(false)
const dataLoaded = ref(false)
const isDragging = ref(false)

const machineCache = new Map<string, Machine[]>()

const getFilteredMachines = (processName: string) => {
  if (!processName) return []
  if (machineCache.has(processName)) return machineCache.get(processName)!
  const filtered = allMachines.value.filter((m) => m.machine_type === processName)
  machineCache.set(processName, filtered)
  return filtered
}

const onStepDragStart = () => { isDragging.value = true }
const onStepDragEnd = () => {
  isDragging.value = false
  steps.value.forEach((step, index) => { step.step_no = index + 1 })
  ElMessage.success('ステップ順序が更新されました')
}

onMounted(async () => {
  try {
    loading.value = true
    const res = await request.get('/api/master/machines')
    const data = res?.data ?? res
    const list = data?.list ?? (Array.isArray(data) ? data : [])
    allMachines.value = list
    machineCache.clear()
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } }; message?: string }
    ElMessage.error(err?.response?.data?.message || err?.message || '設備リストの読み込みに失敗')
  } finally {
    loading.value = false
  }
})

const loadData = async () => {
  if (!props.productCd) {
    steps.value = []
    dataLoaded.value = false
    return
  }
  try {
    loading.value = true
    const productRes = await request.get(
      `/api/master/product/process/routes/${encodeURIComponent(props.productCd)}`
    )
    const product = productRes?.data ?? productRes
    const routeCd = product?.route_cd
    if (!routeCd) {
      steps.value = []
      dataLoaded.value = true
      return
    }
    const stepsRes = await request.get(
      `/api/master/product/process/routes/${encodeURIComponent(props.productCd)}/${encodeURIComponent(routeCd)}`
    )
    const productSteps = stepsRes?.data ?? stepsRes
    if (productSteps && Array.isArray(productSteps) && productSteps.length > 0) {
      steps.value = productSteps.map((step: ProductRouteStep) => ({
        ...step,
        machines: (step.machines || []).map((m: MachineInfo) => ({
          id: m.id,
          machine_cd: m.machine_cd || '',
          machine_name: m.machine_name || '',
          process_time_sec: Number(m.process_time_sec) || 0,
          setup_time: Number(m.setup_time) || 0,
          _uid: Math.random().toString(36).slice(2),
        })),
      }))
    } else {
      steps.value = []
    }
    dataLoaded.value = true
  } catch (e: unknown) {
    const err = e as { response?: { data?: { message?: string } }; message?: string }
    ElMessage.error(err?.response?.data?.message || err?.message || 'データ読み込み失敗')
    steps.value = []
    dataLoaded.value = false
  } finally {
    loading.value = false
  }
}

watch(() => props.productCd, loadData, { immediate: true })

const addProcess = async (process: { process_cd: string; process_name: string }) => {
  let routeCd = steps.value[0]?.route_cd
  if (!routeCd) {
    try {
      const productRes = await request.get(
        `/api/master/product/process/routes/${encodeURIComponent(props.productCd)}`
      )
      const product = productRes?.data ?? productRes
      routeCd = product?.route_cd
      if (!routeCd) {
        ElMessage.error('製品に工程ルートが設定されていません')
        return
      }
    } catch {
      ElMessage.error('製品ルートの取得に失敗しました')
      return
    }
  }
  const maxStepNo = steps.value.length > 0 ? Math.max(...steps.value.map((s) => s.step_no)) : 0
  steps.value.push({
    product_cd: props.productCd,
    route_cd: routeCd,
    step_no: maxStepNo + 1,
    process_cd: process.process_cd,
    process_name: process.process_name,
    machines: [],
  })
}

const addMachine = (step: ProductRouteStep) => {
  if (!step.machines) step.machines = []
  step.machines.push({
    machine_cd: '',
    machine_name: '',
    process_time_sec: 0,
    setup_time: 0,
    _uid: Math.random().toString(36).slice(2),
  })
}

const onMachineChange = (_step: ProductRouteStep, idx: number, machineCd: string) => {
  const machine = allMachines.value.find((m) => m.machine_cd === machineCd)
  const step = _step
  if (machine && step.machines?.[idx]) {
    step.machines[idx].machine_name = machine.machine_name
  }
}

const removeStep = async (index: number) => {
  if (steps.value.length <= index) return
  const removedStep = steps.value[index]
  if (removedStep.id) {
    try {
      await ElMessageBox.confirm(
        `工程ステップ "${removedStep.process_name}" を削除しますか？`,
        '削除確認',
        { confirmButtonText: '確定', cancelButtonText: 'キャンセル', type: 'warning' }
      )
    } catch {
      return
    }
  }
  steps.value.splice(index, 1)
  let nextStepNo = 1
  steps.value.forEach((step) => {
    if (!step.id) {
      while (steps.value.some((s) => s.id && s.step_no === nextStepNo)) nextStepNo++
      step.step_no = nextStepNo
      nextStepNo++
    }
  })
}

const saveSteps = async () => {
  if (!dataLoaded.value) {
    ElMessage.warning('データの読み込みが完了していません')
    return
  }
  const invalidSteps = steps.value.filter((s) => !s.process_cd || !s.process_name)
  if (invalidSteps.length > 0) {
    ElMessage.error('無効な工程ステップが存在します')
    return
  }
  try {
    loading.value = true
    const cleanedSteps = steps.value.map((step) => ({
      ...step,
      machines: (step.machines || []).filter((m) => m.machine_cd),
    }))
    await request.post('/api/master/product/process/routes/bulk', cleanedSteps)
    ElMessage.success('保存成功！')
    await loadData()
  } catch {
    ElMessage.error('保存に失敗しました')
  } finally {
    loading.value = false
  }
}

const resetData = async () => {
  try {
    await ElMessageBox.confirm('リセットしますか？', 'リセット確認', {
      confirmButtonText: '確定',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
  } catch {
    return
  }
  await loadData()
  ElMessage.success('データがリセットされました')
}

const updateMachine = async (step: ProductRouteStep, machineIndex: number) => {
  const machine = step.machines?.[machineIndex]
  if (!machine || !machine.machine_cd) {
    ElMessage.warning('先に設備を選択してください')
    return
  }
  try {
    loading.value = true
    const payload = {
      product_cd: step.product_cd,
      route_cd: step.route_cd,
      step_no: step.step_no,
      machine_cd: machine.machine_cd,
      machine_name: machine.machine_name,
      process_time_sec: machine.process_time_sec,
      setup_time: machine.setup_time,
    }
    if (machine.id) {
      await request.put(`/api/master/product/process/routes/machines/${machine.id}`, payload)
      ElMessage.success('設備更新成功')
    } else {
      const result = await request.post('/api/master/product/process/routes/machines', payload)
      machine.id = (result as { data?: { id?: number }; id?: number })?.data?.id ?? (result as { id?: number })?.id
      ElMessage.success('設備追加成功')
    }
  } catch {
    ElMessage.error('設備操作に失敗しました')
  } finally {
    loading.value = false
  }
}

const removeMachine = async (step: ProductRouteStep, machineIndex: number) => {
  const machine = step.machines?.[machineIndex]
  if (!machine) return
  try {
    await ElMessageBox.confirm(
      `設備 "${machine.machine_name || machine.machine_cd}" を削除しますか？`,
      '削除確認',
      { confirmButtonText: '確定', cancelButtonText: 'キャンセル', type: 'warning' }
    )
  } catch {
    return
  }
  try {
    loading.value = true
    if (machine.id) {
      await request.delete(`/api/master/product/process/routes/machines/${machine.id}`)
    }
    step.machines?.splice(machineIndex, 1)
    ElMessage.success('設備削除成功')
  } catch {
    ElMessage.error('設備削除に失敗しました')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.route-step-card {
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.button-group > .el-button + .el-button {
  margin-left: 8px;
}

.loading-message,
.empty-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
  color: #606266;
  gap: 10px;
}

.empty-message p {
  margin: 0;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.process-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.process-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.process-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.process-code {
  font-weight: bold;
  color: #409eff;
}

.machines-section {
  margin-top: 12px;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 600;
  font-size: 14px;
}

.no-machines {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 4px;
  gap: 8px;
}

.machines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 10px;
}

.machine-card {
  border-radius: 6px;
}

.machine-card.machine-saved {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.machine-card.machine-new {
  border-color: #e6a23c;
  background-color: #fdf6ec;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
}

.form-label {
  font-size: 12px;
  margin-bottom: 4px;
}

.machine-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 6px;
}

.drag-handle {
  display: flex;
  align-items: center;
  gap: 3px;
  color: #909399;
  font-size: 11px;
  cursor: grab;
  user-select: none;
  padding: 3px 6px;
  border-radius: 3px;
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
}

.ghost-step {
  opacity: 0.5;
  background: #f0f9ff;
  border: 2px dashed #409eff;
  border-radius: 8px;
}

.chosen-step {
  background: #ecf5ff;
  border: 2px solid #409eff;
  border-radius: 8px;
}
</style>
