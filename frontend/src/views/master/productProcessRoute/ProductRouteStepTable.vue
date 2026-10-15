<template>
  <div class="route-step-card" v-loading="loading">
    <div class="route-head">
      <div class="route-head__title">
        <span class="route-head__icon-wrap">
          <el-icon :size="17"><Setting /></el-icon>
        </span>
        <div class="route-head__titles">
          <span class="route-head__text">製品別工程ステップ</span>
          <span v-if="steps.length > 0" class="route-head__count">{{ steps.length }} 工程</span>
        </div>
      </div>
      <div class="route-head__actions">
        <el-button
          v-if="canCreate"
          class="tb-btn tb-btn-green"
          size="small"
          :disabled="loading"
          @click="openAddStepDialog"
        >
          <el-icon><Plus /></el-icon>
          <span class="tb-label">工程追加</span>
        </el-button>
        <el-button class="tb-btn tb-btn-amber" size="small" :disabled="loading" @click="resetData">
          <el-icon><RefreshRight /></el-icon>
          <span class="tb-label">リセット</span>
        </el-button>
        <el-button
          v-if="canEdit"
          class="tb-btn tb-btn-indigo"
          size="small"
          :disabled="loading || steps.length === 0"
          @click="saveSteps"
        >
          <el-icon><CircleCheck /></el-icon>
          <span class="tb-label">保存</span>
        </el-button>
      </div>
    </div>

    <div class="route-body">
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
        <el-button
          v-if="canCreate"
          class="tb-btn tb-btn-green"
          size="small"
          @click="openAddStepDialog"
        >
          <el-icon><Plus /></el-icon>
          <span class="tb-label">工程を追加</span>
        </el-button>
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
                  <el-button
                    v-if="canDelete"
                    class="act-del"
                    size="small"
                    :icon="Delete"
                    plain
                    :disabled="loading"
                    @click="removeStep(stepIndex)"
                  >
                    削除
                  </el-button>
                </div>
              </template>

              <div class="step-params">
                <div class="form-cell">
                  <label class="form-label">歩留(%)</label>
                  <el-input-number
                    v-model="step.yield_percent"
                    :min="0"
                    :max="100"
                    :precision="2"
                    :step="0.1"
                    size="small"
                    style="width: 100%"
                    controls-position="right"
                    :disabled="loading || !canEdit"
                  />
                </div>
                <div class="form-cell">
                  <label class="form-label">後工程待ち(秒)</label>
                  <el-input-number
                    v-model="step.wait_sec_after"
                    :min="0"
                    :step="1"
                    size="small"
                    style="width: 100%"
                    controls-position="right"
                    :disabled="loading || !canEdit"
                  />
                </div>
              </div>

              <div class="machines-block">
                <div class="machines-block__head">
                  <div class="machines-block__title">
                    <el-icon :size="15" class="machines-block__title-ico"><Tools /></el-icon>
                    <span>設備一覧</span>
                    <el-tag v-if="step.machines && step.machines.length > 0" type="info" size="small" effect="plain">
                      {{ step.machines.length }}台
                    </el-tag>
                  </div>
                  <el-button
                    v-if="canEdit"
                    class="tb-btn tb-btn-blue tb-btn--sm"
                    size="small"
                    :disabled="loading"
                    @click="addMachine(step)"
                  >
                    <el-icon><Plus /></el-icon>
                    <span class="tb-label">設備追加</span>
                  </el-button>
                </div>

                <div v-if="!step.machines || step.machines.length === 0" class="no-machines">
                  <el-icon :size="28"><Tools /></el-icon>
                  <p>設備が未設定です</p>
                  <el-button
                    v-if="canEdit"
                    class="tb-btn tb-btn-blue tb-btn--sm"
                    size="small"
                    @click="addMachine(step)"
                  >
                    <el-icon><Plus /></el-icon>
                    <span class="tb-label">設備を追加</span>
                  </el-button>
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
                          v-if="canEdit && machine.machine_cd"
                          class="tb-btn tb-btn-green tb-btn--sm"
                          size="small"
                          :disabled="loading"
                          @click="updateMachine(step, Number(idx))"
                        >
                          <el-icon><CircleCheck /></el-icon>
                          <span class="tb-label">{{ machine.id ? '更新' : '保存' }}</span>
                        </el-button>
                        <el-button
                          v-if="canDelete"
                          class="act-del"
                          size="small"
                          :icon="Delete"
                          plain
                          :disabled="loading"
                          @click="removeMachine(step, Number(idx))"
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
    </div>

    <!-- 工程追加後も常に見える固定フッター（スクロールで隠れない） -->
    <div v-if="canCreate && dataLoaded" class="route-footer">
      <div class="route-footer__hint">
        <span v-if="steps.length > 0">工程をさらに追加できます</span>
        <span v-else>最初の工程を追加してください</span>
      </div>
      <div class="route-footer__actions">
        <el-button
          class="tb-btn tb-btn-green"
          size="small"
          :disabled="loading"
          @click="openAddStepDialog"
        >
          <el-icon><Plus /></el-icon>
          <span class="tb-label">工程を追加</span>
        </el-button>
        <el-button
          v-if="canEdit && steps.length > 0"
          class="tb-btn tb-btn-indigo"
          size="small"
          :disabled="loading"
          @click="saveSteps"
        >
          <el-icon><CircleCheck /></el-icon>
          <span class="tb-label">保存</span>
        </el-button>
      </div>
    </div>

    <ProcessSelectDialog v-model:visible="dialogVisible" @selected="addProcess" />
  </div>
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
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'
import { getProcessDetails } from '@/api/options'

const { canCreate, canEdit, canDelete } = useMasterOperationPermission()

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
  yield_percent?: number
  wait_sec_after?: number
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
        yield_percent: step.yield_percent != null ? Number(step.yield_percent) : 100,
        wait_sec_after: step.wait_sec_after != null ? Number(step.wait_sec_after) : 0,
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

const openAddStepDialog = () => {
  if (!guardMasterOperation(canCreate)) return
  dialogVisible.value = true
}

const addProcess = async (process: { process_cd: string; process_name: string }) => {
  if (!guardMasterOperation(canCreate)) return
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
  let yieldPercent = 100
  try {
    const details = await getProcessDetails(process.process_cd)
    if (details.success && details.data?.default_yield != null) {
      yieldPercent = Number(details.data.default_yield) * 100
    }
  } catch {
    /* 工程マスタ未取得時は 100% */
  }
  steps.value.push({
    product_cd: props.productCd,
    route_cd: routeCd,
    step_no: maxStepNo + 1,
    process_cd: process.process_cd,
    process_name: process.process_name,
    yield_percent: yieldPercent,
    wait_sec_after: 0,
    machines: [],
  })
}

const addMachine = (step: ProductRouteStep) => {
  if (!guardMasterOperation(canEdit)) return
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
  if (!guardMasterOperation(canDelete)) return
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
  if (!guardMasterOperation(canEdit)) return
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
  if (!guardMasterOperation(canEdit)) return
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
  if (!guardMasterOperation(canDelete)) return
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
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  border-radius: 14px;
  border: 1px solid #ddd6fe;
  background: #fff;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.95) inset, 0 10px 28px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  position: relative;
}
.route-step-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  pointer-events: none;
  background: linear-gradient(90deg, #4c1d95 0%, #8b5cf6 55%, #c4b5fd 100%);
}

.route-head {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 10px 12px;
  background: linear-gradient(110deg, #f5f3ff 0%, #ffffff 60%);
  border-bottom: 1px solid #ede9fe;
  z-index: 2;
}

.route-head__title {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.route-head__titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.route-head__icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #ede9fe 0%, #ddd6fe 100%);
  border: 1px solid #c4b5fd;
  color: #6d28d9;
  flex-shrink: 0;
}

.route-head__text {
  font-size: 0.88rem;
  font-weight: 800;
  color: #4c1d95;
}

.route-head__count {
  font-size: 11px;
  font-weight: 700;
  color: #7c3aed;
  font-variant-numeric: tabular-nums;
}

.route-head__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.route-body {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 12px;
}

.route-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid #ede9fe;
  background: linear-gradient(180deg, #faf5ff 0%, #ffffff 100%);
  box-shadow: 0 -6px 16px -12px rgba(76, 29, 149, 0.35);
  z-index: 3;
}

.route-footer__hint {
  font-size: 12px;
  font-weight: 600;
  color: #7c3aed;
}

.route-footer__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tb-btn {
  --k-rgb: 109 40 217;
  --k-fg: #5b21b6;
  --k-bd: #c4b5fd;
  --k-tint: #ede9fe;
  --k-tint-h: #ddd6fe;
  --k-ico: #8b5cf6;
  height: 30px !important;
  padding: 0 12px 0 10px !important;
  border-radius: 999px !important;
  font-weight: 700 !important;
  margin: 0 !important;
  color: var(--k-fg) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 40%, var(--k-tint) 100%) !important;
  border: 1px solid var(--k-bd) !important;
  box-shadow:
    inset 0 1px 0 #fff,
    inset 0 -2px 0 rgb(var(--k-rgb) / 0.12),
    0 2px 6px -1px rgba(76, 29, 149, 0.2) !important;
}
.tb-btn :deep(.el-icon) {
  color: var(--k-ico);
}
.tb-btn:hover:not(:disabled) {
  color: rgb(var(--k-rgb)) !important;
  background: linear-gradient(135deg, #ffffff 0%, #ffffff 30%, var(--k-tint-h) 100%) !important;
  transform: translateY(-1px);
}
.tb-btn--sm {
  height: 26px !important;
  font-size: 12px !important;
}
.tb-btn-green {
  --k-rgb: 5 150 105;
  --k-fg: #047857;
  --k-bd: #6ee7b7;
  --k-tint: #d1fae5;
  --k-tint-h: #a7f3d0;
  --k-ico: #10b981;
}
.tb-btn-amber {
  --k-rgb: 217 119 6;
  --k-fg: #92400e;
  --k-bd: #fcd34d;
  --k-tint: #fef3c7;
  --k-tint-h: #fde68a;
  --k-ico: #d97706;
}
.tb-btn-indigo {
  --k-rgb: 99 102 241;
  --k-fg: #4338ca;
  --k-bd: #a5b4fc;
  --k-tint: #e0e7ff;
  --k-tint-h: #c7d2fe;
  --k-ico: #6366f1;
}
.tb-btn-blue {
  --k-rgb: 37 99 235;
  --k-fg: #1d4ed8;
  --k-bd: #93c5fd;
  --k-tint: #dbeafe;
  --k-tint-h: #bfdbfe;
  --k-ico: #3b82f6;
}
.act-del {
  border-radius: 999px !important;
  font-weight: 700 !important;
  color: #e11d48 !important;
  border-color: #fecdd3 !important;
  background: #fff1f2 !important;
}
.act-del:hover:not(:disabled) {
  color: #fff !important;
  background: linear-gradient(135deg, #f43f5e, #e11d48) !important;
  border-color: transparent !important;
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
  border-radius: 12px !important;
  border: 1px solid #ddd6fe !important;
  overflow: hidden;
}

.process-card :deep(.el-card__header) {
  padding: 6px 8px !important;
  background: linear-gradient(180deg, #faf5ff 0%, #f5f3ff 100%);
  border-bottom: 1px solid #ede9fe !important;
}

.process-card :deep(.el-card__body) {
  padding: 8px !important;
}

.step-params {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.process-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.process-head > .act-del {
  margin-left: auto;
  flex-shrink: 0;
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
  color: #6d28d9;
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
  color: #7c3aed;
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
  background: #f5f3ff;
  border: 2px dashed #8b5cf6;
  border-radius: 8px;
}

.chosen-step {
  background: #f5f3ff;
  border: 1px solid #a78bfa;
  border-radius: 8px;
}

@media (max-width: 640px) {
  .route-head__actions,
  .route-footer__actions {
    width: 100%;
  }
  .route-footer__actions .tb-btn {
    flex: 1 1 auto;
    justify-content: center;
  }
}

@media (max-width: 520px) {
  .form-grid {
    grid-template-columns: 1fr;
  }

  .process-head__info {
    width: 100%;
  }
  .process-head > .act-del {
    margin-left: 0;
  }
}
</style>
