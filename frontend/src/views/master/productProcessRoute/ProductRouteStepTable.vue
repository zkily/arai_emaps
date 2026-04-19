<template>
  <el-card shadow="never" class="route-step-card" v-loading="loading">
    <template #header>
      <div class="route-head">
        <div class="route-head__title">
          <span class="route-head__icon-wrap">
            <el-icon :size="17"><Setting /></el-icon>
          </span>
          <span class="route-head__text">製品別工程ステップ</span>
        </div>
        <div class="route-head__actions">
          <el-button type="success" size="small" :icon="Plus" :disabled="loading" @click="dialogVisible = true">
            工程追加
          </el-button>
          <el-button type="info" size="small" :icon="RefreshRight" plain :disabled="loading" @click="resetData">
            リセット
          </el-button>
          <el-button
            type="primary"
            size="small"
            :icon="CircleCheck"
            :disabled="loading || steps.length === 0"
            @click="saveSteps"
          >
            保存
          </el-button>
        </div>
      </div>
    </template>

    <template v-if="loading && !dataLoaded">
      <div class="state-msg state-msg--load">
        <el-icon class="is-loading state-msg__ico"><Loading /></el-icon>
        <span>読み込み中…</span>
      </div>
    </template>

    <template v-else-if="!loading && dataLoaded && steps.length === 0">
      <div class="state-msg state-msg--empty">
        <el-icon :size="36" class="state-msg__ico"><DocumentRemove /></el-icon>
        <p class="state-msg__p">工程ルート未設定、またはステップがありません</p>
        <el-button type="primary" size="small" :icon="Plus" @click="dialogVisible = true">工程を追加</el-button>
      </div>
    </template>

    <div v-else-if="dataLoaded && steps.length > 0" class="steps-wrap">
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
          <div class="step-outer" :class="{ 'step-outer--drag': isDragging }">
            <el-card shadow="never" class="process-card">
              <template #header>
                <div class="process-head">
                  <div class="drag-handle" title="ドラッグで並び替え">
                    <el-icon class="drag-handle__ico"><Rank /></el-icon>
                  </div>
                  <div class="process-head__info">
                    <el-tag type="primary" size="small" effect="plain" class="process-head__no"
                      >順序 {{ step.step_no }}</el-tag
                    >
                    <span class="process-head__cd">{{ step.process_cd }}</span>
                    <span class="process-head__name">{{ step.process_name }}</span>
                    <el-tag v-if="step.id" type="success" size="small" effect="plain">保存済み</el-tag>
                    <el-tag v-else type="warning" size="small" effect="plain">未保存</el-tag>
                  </div>
                  <el-button type="danger" size="small" :icon="Delete" plain @click="removeStep(stepIndex)" :disabled="loading">
                    削除
                  </el-button>
                </div>
              </template>

              <div class="machines-block">
                <div class="machines-block__head">
                  <div class="machines-block__title">
                    <el-icon :size="15" class="machines-block__title-ico"><Tools /></el-icon>
                    <span>設備一覧</span>
                    <el-tag v-if="step.machines && step.machines.length > 0" type="info" size="small" effect="plain">
                      {{ step.machines.length }}台
                    </el-tag>
                  </div>
                  <el-button type="primary" size="small" :icon="Plus" link @click="addMachine(step)" :disabled="loading">
                    設備追加
                  </el-button>
                </div>

                <div v-if="!step.machines || step.machines.length === 0" class="no-machines">
                  <el-icon :size="28"><Tools /></el-icon>
                  <p>設備が未設定です</p>
                  <el-button type="primary" size="small" :icon="Plus" @click="addMachine(step)">設備を追加</el-button>
                </div>

                <div v-else class="machines-grid">
                  <el-card
                    v-for="(machine, idx) in step.machines"
                    :key="machine._uid || machine.id || idx"
                    shadow="never"
                    class="machine-card"
                    :class="{ 'machine-card--saved': machine.id, 'machine-card--new': !machine.id }"
                  >
                    <div class="machine-form">
                      <div class="machine-form__tags">
                        <el-tag v-if="machine.id" type="success" size="small" effect="plain">保存済み</el-tag>
                        <el-tag v-else type="warning" size="small" effect="plain">新規</el-tag>
                      </div>
                      <div class="form-grid">
                        <div class="form-cell">
                          <label class="form-label">設備CD</label>
                          <el-select
                            v-model="machine.machine_cd"
                            filterable
                            placeholder="選択"
                            size="small"
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
                        <div class="form-cell">
                          <label class="form-label">設備名</label>
                          <el-input v-model="machine.machine_name" placeholder="—" readonly size="small" />
                        </div>
                        <div class="form-cell">
                          <label class="form-label">加工時間 (秒)</label>
                          <el-input-number
                            v-model="machine.process_time_sec"
                            :min="0"
                            :step="1"
                            size="small"
                            style="width: 100%"
                            controls-position="right"
                            :disabled="loading"
                          />
                        </div>
                        <div class="form-cell">
                          <label class="form-label">段取り時間 (分)</label>
                          <el-input-number
                            v-model="machine.setup_time"
                            :min="0"
                            :step="1"
                            size="small"
                            style="width: 100%"
                            controls-position="right"
                            :disabled="loading"
                          />
                        </div>
                      </div>
                      <div class="machine-form__actions">
                        <el-button
                          v-if="machine.machine_cd"
                          type="success"
                          size="small"
                          :icon="CircleCheck"
                          @click="updateMachine(step, Number(idx))"
                          :disabled="loading"
                        >
                          {{ machine.id ? '更新' : '保存' }}
                        </el-button>
                        <el-button
                          type="danger"
                          size="small"
                          :icon="Delete"
                          plain
                          @click="removeMachine(step, Number(idx))"
                          :disabled="loading"
                        >
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
import {
  Loading,
  DocumentRemove,
  Tools,
  Rank,
  Setting,
  Plus,
  RefreshRight,
  CircleCheck,
  Delete,
} from '@element-plus/icons-vue'
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

const onStepDragStart = () => {
  isDragging.value = true
}
const onStepDragEnd = () => {
  isDragging.value = false
  steps.value.forEach((step, index) => {
    step.step_no = index + 1
  })
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
      `/api/master/product/process/routes/${encodeURIComponent(props.productCd)}`,
    )
    const product = productRes?.data ?? productRes
    const routeCd = product?.route_cd
    if (!routeCd) {
      steps.value = []
      dataLoaded.value = true
      return
    }
    const stepsRes = await request.get(
      `/api/master/product/process/routes/${encodeURIComponent(props.productCd)}/${encodeURIComponent(routeCd)}`,
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
        `/api/master/product/process/routes/${encodeURIComponent(props.productCd)}`,
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
        { confirmButtonText: '確定', cancelButtonText: 'キャンセル', type: 'warning' },
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
      machine.id =
        (result as { data?: { id?: number }; id?: number })?.data?.id ?? (result as { id?: number })?.id
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
      { confirmButtonText: '確定', cancelButtonText: 'キャンセル', type: 'warning' },
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
  border-radius: 10px;
  border: 1px solid rgba(226, 232, 240, 0.95);
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.04),
    0 8px 20px -8px rgba(15, 23, 42, 0.1);
}

.route-step-card :deep(.el-card__header) {
  padding: 0;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #fafbfc 0%, #f1f5f9 100%);
}

.route-step-card :deep(.el-card__body) {
  padding: 10px 10px 12px;
}

.route-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 10px;
}

.route-head__title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.route-head__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  border: 1px solid rgba(99, 102, 241, 0.22);
  color: #4f46e5;
  flex-shrink: 0;
}

.route-head__text {
  font-size: 0.88rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.route-head__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.route-head__actions :deep(.el-button) {
  margin: 0;
}

.state-msg {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 12px;
  color: #64748b;
  gap: 8px;
  font-size: 13px;
}

.state-msg--empty .state-msg__ico {
  color: #94a3b8;
}

.state-msg__p {
  margin: 0;
  font-size: 13px;
}

.steps-wrap {
  margin: 0;
}

.draggable-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-outer {
  border-radius: 8px;
}

.process-card {
  border-radius: 8px !important;
  border: 1px solid #e2e8f0 !important;
  overflow: hidden;
}

.process-card :deep(.el-card__header) {
  padding: 6px 8px !important;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0 !important;
}

.process-card :deep(.el-card__body) {
  padding: 8px !important;
}

.process-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.drag-handle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  cursor: grab;
  color: #64748b;
  border-radius: 6px;
  background: #fff;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle__ico {
  font-size: 16px;
}

.process-head__info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.process-head__no {
  flex-shrink: 0;
}

.process-head__cd {
  font-weight: 700;
  font-size: 12px;
  color: #2563eb;
  font-family: ui-monospace, Menlo, Monaco, Consolas, monospace;
}

.process-head__name {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
}

.machines-block {
  margin-top: 0;
}

.machines-block__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.machines-block__title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
}

.machines-block__title-ico {
  color: #6366f1;
}

.no-machines {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px dashed #cbd5e1;
  gap: 6px;
  color: #64748b;
  font-size: 12px;
}

.no-machines p {
  margin: 0;
}

.machines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 8px;
}

.machine-card {
  border-radius: 8px !important;
}

.machine-card :deep(.el-card__body) {
  padding: 8px !important;
}

.machine-card--saved {
  border-color: rgba(34, 197, 94, 0.45) !important;
  background: linear-gradient(180deg, #f0fdf4 0%, #fff 48%) !important;
}

.machine-card--new {
  border-color: rgba(245, 158, 11, 0.5) !important;
  background: linear-gradient(180deg, #fffbeb 0%, #fff 50%) !important;
}

.machine-form__tags {
  margin-bottom: 6px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 8px;
}

.form-cell {
  min-width: 0;
}

.form-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 2px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.machine-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 8px;
  padding-top: 6px;
  border-top: 1px solid #f1f5f9;
}

.ghost-step {
  opacity: 0.55;
  background: #eef2ff;
  border: 2px dashed #6366f1;
  border-radius: 8px;
}

.chosen-step {
  background: #eef2ff;
  border: 1px solid #818cf8;
  border-radius: 8px;
}

@media (max-width: 520px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .process-head__info {
    width: 100%;
  }
}
</style>
