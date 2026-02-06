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

    <!-- 読み込み状態 -->
    <template v-if="loading">
      <div class="loading-message">
        <el-icon class="is-loading">
          <Loading />
        </el-icon>
        <span>{{ dataLoaded ? '処理中...' : 'データを読み込み中...' }}</span>
      </div>
    </template>

    <!-- 空状態 -->
    <template v-else-if="!loading && dataLoaded && steps.length === 0">
      <div class="empty-message">
        <el-icon>
          <DocumentRemove />
        </el-icon>
        <p>工程ルート未設定 または ステップがありません</p>
        <el-button type="primary" @click="dialogVisible = true">工程を追加</el-button>
      </div>
    </template>

    <!-- データ表示 -->
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
                    <el-icon class="drag-icon">
                      <Rank />
                    </el-icon>
                    <span class="drag-text">ドラッグで並び替え</span>
                  </div>
                  <div class="process-info">
                    <el-tag type="primary" size="small">順序 {{ step.step_no }}</el-tag>
                    <span class="process-code">{{ step.process_cd }}</span>
                    <span class="process-name">{{ step.process_name }}</span>
                    <el-tag v-if="step.id" type="success" size="small">保存済み</el-tag>
                    <el-tag v-else type="warning" size="small">未保存</el-tag>
                  </div>
                  <el-button
                    type="danger"
                    size="small"
                    @click="removeStep(stepIndex)"
                    :disabled="loading"
                  >
                    🗑️ 削除
                  </el-button>
                </div>
              </template>

              <div class="machines-section">
                <div class="section-title">
                  <span
                    >🔧 設備一覧
                    <el-tag
                      v-if="step.machines && step.machines.length > 0"
                      type="info"
                      size="small"
                    >
                      {{ step.machines.length }}台
                    </el-tag>
                  </span>
                  <el-button
                    type="primary"
                    size="small"
                    @click="addMachine(step)"
                    :disabled="loading"
                  >
                    ➕ 設備追加
                  </el-button>
                </div>

                <div v-if="!step.machines || step.machines.length === 0" class="no-machines">
                  <el-icon>
                    <Tools />
                  </el-icon>
                  <p>設備が設定されていません</p>
                  <el-button type="primary" size="small" @click="addMachine(step)"
                    >設備を追加</el-button
                  >
                </div>

                <div v-else class="machines-grid">
                  <el-card
                    v-for="(machine, idx) in step.machines"
                    :key="machine._uid || idx"
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
                          <label class="form-label">
                            設備CD
                            <el-tooltip
                              content="この工程の利用可能な設備をクリックして表示"
                              placement="top"
                            >
                              <span
                                class="device-count"
                                @click="showMachineStats(step.process_name)"
                              >
                                ({{ getFilteredMachines(step.process_name).length }}台設備)
                              </span>
                            </el-tooltip>
                          </label>
                          <el-select
                            v-model="machine.machine_cd"
                            filterable
                            placeholder="設備を選択"
                            style="width: 100%"
                            @change="(cd) => onMachineChange(step, idx, cd)"
                            :disabled="loading"
                          >
                            <!-- フィルタリング後の設備 -->
                            <el-option
                              v-for="opt in getFilteredMachines(step.process_name)"
                              :key="opt.machine_cd"
                              :label="`${opt.machine_cd} - ${opt.machine_name}`"
                              :value="opt.machine_cd"
                            />
                            <!-- デバッグ：全設備を表示（フィルタリング結果が空の場合） -->
                            <template
                              v-if="
                                getFilteredMachines(step.process_name).length === 0 &&
                                allMachines.length > 0
                              "
                            >
                              <el-option
                                disabled
                                :key="'separator'"
                                :label="'--- 全設備（デバッグ） ---'"
                                :value="''"
                              />
                              <el-option
                                v-for="opt in allMachines"
                                :key="'all-' + opt.machine_cd"
                                :label="`[全] ${opt.machine_cd} - ${opt.machine_name} (${opt.machine_type})`"
                                :value="opt.machine_cd"
                              />
                            </template>
                            <!-- デバッグオプション：設備データなし -->
                            <el-option
                              v-if="allMachines.length === 0"
                              :key="'no-data'"
                              :label="'設備データがありません'"
                              :value="''"
                              disabled
                            />
                          </el-select>
                        </div>
                        <div class="form-item">
                          <label class="form-label">設備名</label>
                          <el-input
                            v-model="machine.machine_name"
                            placeholder="設備名"
                            readonly
                            style="width: 100%"
                          />
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
                            placeholder="加工時間を入力"
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
                            placeholder="段取り時間を入力"
                            :disabled="loading"
                          />
                        </div>
                      </div>

                      <div class="machine-actions">
                        <el-button
                          v-if="machine.machine_cd"
                          type="success"
                          size="small"
                          @click="updateMachine(step, idx)"
                          :disabled="loading"
                        >
                          <el-icon>
                            <Check />
                          </el-icon>
                          {{ machine.id ? '更新' : '保存' }}
                        </el-button>
                        <el-button
                          type="danger"
                          size="small"
                          @click="removeMachine(step, idx)"
                          :disabled="loading"
                        >
                          <el-icon>
                            <Delete />
                          </el-icon>
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

    <!-- ✅ 工程選択ダイアログ -->
    <ProcessSelectDialog v-model:visible="dialogVisible" @selected="addProcess" />
  </el-card>
</template>

<!--
バックエンドでサポートが必要なAPIインターフェース：

1. 単一設備新規追加：POST /api/master/product/process/routes/machines
   リクエストボディ：{
     product_cd: string,
     route_cd: string,
     step_no: number,
     machine_cd: string,
     machine_name: string,
     process_time_sec: number,
     setup_time: number
   }
   戻り値：{ id: number, ...その他のフィールド }

2. 単一設備更新：PUT /api/master/product/process/routes/machines/:id
   リクエストボディ：新規追加インターフェースと同じ
   戻り値：{ success: true }

3. 単一設備削除：DELETE /api/master/product/process/routes/machines/:id
   戻り値：{ success: true }

4. 工程ステップ取得（設備含む）：GET /api/master/product/process/routes/:productCd/:routeCd
   戻り値：[{
     id: number,
     product_cd: string,
     route_cd: string,
     step_no: number,
     process_cd: string,
     process_name: string,
     machines: [{
       id: number,
       machine_cd: string,
       machine_name: string,
       process_time_sec: number,
       setup_time: number
     }]
   }]
-->

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, DocumentRemove, Tools, Check, Delete, Rank } from '@element-plus/icons-vue'
import ProcessSelectDialog from './ProcessSelectDialog.vue'
import draggable from 'vuedraggable'

const props = defineProps<{ productCd: string }>()

interface MachineInfo {
  id?: number // データベースID、更新操作に使用
  machine_cd: string
  machine_name: string
  process_time_sec: number
  setup_time: number
  _uid?: string // フロントエンド一意キー
}
interface ProductRouteStep {
  id?: number // データベースID
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
  machine_type: string
}

const steps = ref<ProductRouteStep[]>([])
const dialogVisible = ref(false)
const allMachines = ref<Machine[]>([])
const loading = ref(false)
const dataLoaded = ref(false)
const isDragging = ref(false)

// 計算プロパティ：データ変更があるかチェック
const hasChanges = computed(() => {
  return steps.value.some((step) =>
    step.machines?.some(
      (machine) => machine.machine_cd || machine.process_time_sec > 0 || machine.setup_time > 0,
    ),
  )
})

onMounted(async () => {
  // 全設備リストを取得
  try {
    loading.value = true
    const res = await request.get('/api/master/machines')
    // 複数の可能なデータ構造を試行
    let machinesData = []

    if (res.data && res.data.list) {
      // 標準フォーマット: { success: true, data: { list: [...], total: n } }
      machinesData = res.data.list
    } else if (res.data && Array.isArray(res.data)) {
      // 直接配列フォーマット: { success: true, data: [...] }
      machinesData = res.data
    } else if (Array.isArray(res)) {
      // 直接配列を返す
      machinesData = res
    } else if (res.list) {
      // その他の可能なフォーマット
      machinesData = res.list
    } else {
      machinesData = res || []
    }

    allMachines.value = machinesData

    // 工程タイプ別に設備数を統計
    if (allMachines.value.length > 0) {
      const machineStats = allMachines.value.reduce(
        (acc, machine) => {
          const type = machine.machine_type || '未分類'
          acc[type] = (acc[type] || 0) + 1
          return acc
        },
        {} as Record<string, number>,
      )

      console.log('設備リスト読み込み成功:', allMachines.value.length, '台')
      console.log('工程別統計:')
      Object.entries(machineStats)
        .sort(([, a], [, b]) => b - a) // 数量降順で並び替え
        .forEach(([type, count]) => {
          console.log(`  ${type}: ${count}台`)
        })
    } else {
      console.log('設備リスト読み込み成功: 0台')
    }

    // 設備フィルタリングキャッシュをクリア
    clearMachineCache()

    // 設備データがない場合、ヒントを表示
    if (allMachines.value.length === 0) {
      console.warn('⚠️ machinesテーブルに設備データがありません。先に設備データを追加してください')
      ElMessage.warning('設備テーブルにデータがありません。先に設備管理で設備を追加してください')
    }
  } catch (e: any) {
    console.error('設備リストの取得に失敗:', e)
    console.error('エラー詳細:', e.response)
    const errorMsg = e.response?.data?.message || e.message || '設備リストの読み込みに失敗'
    ElMessage.error(errorMsg)
  } finally {
    loading.value = false
  }
})

// 設備フィルタリングキャッシュ
const machineCache = new Map<string, Machine[]>()

// 工程名に基づいて対応する設備をフィルタリング（キャッシュ最適化付き）
const getFilteredMachines = (processName: string) => {
  if (!processName) {
    return []
  }

  // キャッシュをチェック
  if (machineCache.has(processName)) {
    return machineCache.get(processName)!
  }

  // 設備をフィルタリングして結果をキャッシュ
  const filtered = allMachines.value.filter((machine) => machine.machine_type === processName)
  machineCache.set(processName, filtered)

  console.log(`工程 "${processName}" に対応する設備:`, filtered.length, '台')

  // マッチする設備が見つからない場合、デバッグ情報を出力
  if (filtered.length === 0 && allMachines.value.length > 0) {
    console.log('マッチする設備が見つかりません。全設備タイプ:')
    const types = [...new Set(allMachines.value.map((m) => m.machine_type))]
    console.log('利用可能設備タイプ:', types)
  }

  return filtered
}

// 設備キャッシュをクリア（設備リスト更新時に呼び出し）
const clearMachineCache = () => {
  machineCache.clear()
}

// ドラッグ開始処理
const onStepDragStart = () => {
  isDragging.value = true
  console.log('ステップのドラッグを開始')
}

// ドラッグ終了処理
const onStepDragEnd = () => {
  isDragging.value = false
  // ステップ番号を再割り当て
  steps.value.forEach((step, index) => {
    step.step_no = index + 1
  })
  console.log(
    'ステップ順序が更新されました:',
    steps.value.map((s) => `${s.step_no}: ${s.process_name}`),
  )
  ElMessage.success('ステップ順序が更新されました')
}

// 設備統計情報を表示
const showMachineStats = (processName?: string) => {
  if (allMachines.value.length === 0) {
    ElMessage.info('設備データがありません')
    return
  }

  if (processName) {
    // 特定工程の設備情報を表示
    const filteredMachines = getFilteredMachines(processName)
    if (filteredMachines.length === 0) {
      ElMessage.info(`工程 "${processName}" に利用可能な設備がありません`)
      return
    }

    const machineList = filteredMachines
      .map((machine) => `${machine.machine_cd} - ${machine.machine_name}`)
      .join('\n')

    ElMessageBox.alert(
      `工程 "${processName}" の利用可能設備：\n\n${machineList}\n\n合計 ${filteredMachines.length} 台`,
      '工程設備一覧',
      {
        confirmButtonText: '確定',
        type: 'info',
      },
    )
  } else {
    // 全設備の統計情報を表示
    const machineStats = allMachines.value.reduce(
      (acc, machine) => {
        const type = machine.machine_type || '未分類'
        acc[type] = (acc[type] || 0) + 1
        return acc
      },
      {} as Record<string, number>,
    )

    const statsText = Object.entries(machineStats)
      .sort(([, a], [, b]) => b - a)
      .map(([type, count]) => `${type}: ${count}台`)
      .join('\n')

    ElMessageBox.alert(
      `設備統計情報：\n\n${statsText}\n\n合計: ${allMachines.value.length}台`,
      '設備統計',
      {
        confirmButtonText: '確定',
        type: 'info',
      },
    )
  }
}

const loadData = async () => {
  if (!props.productCd) {
    steps.value = []
    dataLoaded.value = false
    return
  }

  try {
    loading.value = true
    console.log('製品データの読み込み開始:', props.productCd)

    // 1. 製品のルート情報を取得
    const productResponse = await request.get(
      `/api/master/product/process/routes/${props.productCd}`,
    )
    console.log('製品ルート情報:', productResponse)

    // APIレスポンスデータ構造処理を修正
    const product = productResponse.data || productResponse
    const routeCd = product?.route_cd

    console.log('解析後の製品情報:', product)
    console.log('抽出されたルートコード:', routeCd)

    if (!routeCd) {
      console.log('製品に工程ルートが設定されていません')
      steps.value = []
      dataLoaded.value = true
      return
    }

    // 2. 製品工程ステップデータを取得（設備情報含む）
    console.log('工程ステップデータの読み込み:', props.productCd, routeCd)
    const productStepsResponse = await request.get(
      `/api/master/product/process/routes/${props.productCd}/${routeCd}`,
    )
    console.log('取得された工程ステップデータ:', productStepsResponse)

    // APIレスポンスデータ構造処理を修正 - バックエンドは { success: true, data: steps } を返す
    const productSteps = productStepsResponse.data || productStepsResponse

    console.log('解析後の工程ステップデータ:', productSteps)
    console.log('配列かどうか:', Array.isArray(productSteps))
    console.log('配列の長さ:', productSteps?.length)

    if (productSteps && Array.isArray(productSteps) && productSteps.length > 0) {
      // 保存済みデータがある場合、設備データの完全読み込みを確保
      steps.value = productSteps.map((step: ProductRouteStep) => {
        const processedStep: ProductRouteStep = {
          ...step,
          machines: [],
        }

        // 設備データを処理し、各設備に完全な情報があることを確保
        if (step.machines && Array.isArray(step.machines)) {
          processedStep.machines = step.machines.map((m: MachineInfo) => ({
            id: m.id, // データベースIDを保持
            machine_cd: m.machine_cd || '',
            machine_name: m.machine_name || '',
            process_time_sec: Number(m.process_time_sec) || 0,
            setup_time: Number(m.setup_time) || 0,
            _uid: Math.random().toString(36).slice(2),
          }))
        }

        return processedStep
      })
      console.log('保存済み工程ステップの読み込み:', steps.value.length, 'ステップ')

      // 各ステップの設備情報を出力
      steps.value.forEach((step, index) => {
        console.log(
          `ステップ ${index + 1} (${step.process_name}):`,
          step.machines?.length || 0,
          '設備',
        )
        step.machines?.forEach((machine, machineIndex) => {
          console.log(`  設備 ${machineIndex + 1}:`, {
            id: machine.id,
            machine_cd: machine.machine_cd,
            machine_name: machine.machine_name,
            process_time_sec: machine.process_time_sec,
            setup_time: machine.setup_time,
          })
        })
      })
    } else {
      // 保存済みデータがない場合、工程ステップを自動作成しない
      // ユーザーが手動で工程を追加する必要がある
      console.log('保存済みデータがありません、ユーザーが手動で工程を追加するのを待機中')
      steps.value = []
    }

    dataLoaded.value = true
  } catch (e: any) {
    console.error('データ読み込み失敗:', e)
    const errorMsg = e.response?.data?.message || e.message || 'データ読み込み失敗'
    ElMessage.error(`データ読み込み失敗: ${errorMsg}`)
    steps.value = []
    dataLoaded.value = false
  } finally {
    loading.value = false
  }
}

watch(() => props.productCd, loadData, { immediate: true })

const addProcess = async (process: { process_cd: string; process_name: string }) => {
  // まだルート情報がない場合、先に取得
  let routeCd = steps.value[0]?.route_cd
  if (!routeCd) {
    try {
      const productResponse = await request.get(
        `/api/master/product/process/routes/${props.productCd}`,
      )
      const product = productResponse.data || productResponse
      routeCd = product?.route_cd
      if (!routeCd) {
        ElMessage.error('製品に工程ルートが設定されていません、工程ステップを追加できません')
        return
      }
    } catch (e: any) {
      console.error('製品ルート取得失敗:', e)
      ElMessage.error('製品ルートの取得に失敗しました')
      return
    }
  }

  const maxStepNo = steps.value.length > 0 ? Math.max(...steps.value.map((s) => s.step_no)) : 0
  const newStep: ProductRouteStep = {
    product_cd: props.productCd,
    route_cd: routeCd,
    step_no: maxStepNo + 1,
    process_cd: process.process_cd,
    process_name: process.process_name,
    machines: [],
  }
  steps.value.push(newStep)
  console.log('新工程を追加:', newStep)
}

const addMachine = (step: ProductRouteStep) => {
  if (!step.machines) step.machines = []
  const newMachine: MachineInfo = {
    machine_cd: '',
    machine_name: '',
    process_time_sec: 0,
    setup_time: 0,
    _uid: Math.random().toString(36).slice(2),
  }
  step.machines.push(newMachine)
  console.log('工程に新設備を追加:', step.process_name)
}

const onMachineChange = (step: ProductRouteStep, idx: number, machineCd: string) => {
  const machine = allMachines.value.find((m) => m.machine_cd === machineCd)
  if (machine && step.machines && step.machines[idx]) {
    step.machines[idx].machine_name = machine.machine_name
    console.log('設備選択変更:', machineCd, '->', machine.machine_name)
  }
}

const removeStep = async (index: number) => {
  if (steps.value.length <= index) return

  const removedStep = steps.value[index]

  // 保存済みステップの場合、削除確認が必要
  if (removedStep.id) {
    try {
      const confirmed = await ElMessageBox.confirm(
        `工程ステップ "${removedStep.process_name}" を削除しますか？この操作は取り消せません。`,
        '削除確認',
        {
          confirmButtonText: '確定',
          cancelButtonText: 'キャンセル',
          type: 'warning',
        },
      )
      if (!confirmed) return
    } catch {
      return // ユーザーがキャンセル
    }
  }

  // ステップを削除
  steps.value.splice(index, 1)

  // 未保存のステップのみステップ番号を再ソート
  // 保存済みステップは元のステップ番号を保持し、データ不整合を避ける
  let nextStepNo = 1
  steps.value.forEach((step) => {
    if (!step.id) {
      // 未保存のステップ、ステップ番号を再割り当て
      while (steps.value.some((s) => s.id && s.step_no === nextStepNo)) {
        nextStepNo++
      }
      step.step_no = nextStepNo
      nextStepNo++
    }
  })

  console.log('工程ステップを削除:', removedStep.process_name)
}

const saveSteps = async () => {
  if (!dataLoaded.value) {
    ElMessage.warning('データの読み込みが完了していません、しばらくお待ちください')
    return
  }

  // データ検証
  const invalidSteps = steps.value.filter((step) => !step.process_cd || !step.process_name)
  if (invalidSteps.length > 0) {
    ElMessage.error('無効な工程ステップが存在します、データを確認してください')
    return
  }

  // 設備データを検証
  for (const step of steps.value) {
    if (step.machines) {
      // 設備検証ロジックを修正：machine_nameは自動入力されるため、検証不要
      const invalidMachines = step.machines.filter(
        (m) => m.machine_cd && (m.process_time_sec < 0 || m.setup_time < 0),
      )
      if (invalidMachines.length > 0) {
        ElMessage.error(`工程 "${step.process_name}" に無効な設備設定が存在します`)
        return
      }
    }
  }

  try {
    loading.value = true
    console.log('データ保存開始:', steps.value)

    // 空の設備レコードをクリーンアップ
    const cleanedSteps = steps.value.map((step) => ({
      ...step,
      machines: (step.machines || []).filter((m) => m.machine_cd), // 設備CDがあるレコードのみ保存
    }))

    await request.post('/api/master/product/process/routes/bulk', cleanedSteps)
    ElMessage.success('保存成功！')

    // 最新のIDなどの情報を取得するためデータを再読み込み
    await loadData()
  } catch (e: unknown) {
    console.error('保存失敗:', e)
    ElMessage.error('保存に失敗しました、再試行してください')
  } finally {
    loading.value = false
  }
}

// データをリセット
const resetData = async () => {
  if (hasChanges.value) {
    const confirmed = await ElMessageBox.confirm(
      '未保存の変更があります、リセットしますか？',
      'リセット確認',
      {
        confirmButtonText: '確定',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    ).catch(() => false)

    if (!confirmed) return
  }

  await loadData()
  ElMessage.success('データがリセットされました')
}

// 単一設備更新機能
const updateMachine = async (step: ProductRouteStep, machineIndex: number) => {
  const machine = step.machines?.[machineIndex]
  if (!machine || !machine.machine_cd) {
    ElMessage.warning('先に設備を選択してください')
    return
  }

  try {
    loading.value = true
    console.log('単一設備を更新:', machine)

    const updateData = {
      product_cd: step.product_cd,
      route_cd: step.route_cd,
      step_no: step.step_no,
      machine_cd: machine.machine_cd,
      machine_name: machine.machine_name,
      process_time_sec: machine.process_time_sec,
      setup_time: machine.setup_time,
    }

    if (machine.id) {
      // 既存設備を更新
      await request.put(`/api/master/product/process/routes/machines/${machine.id}`, updateData)
      ElMessage.success('設備更新成功')
    } else {
      // 新規設備を追加
      const result = await request.post('/api/master/product/process/routes/machines', updateData)
      // 設備ID取得を修正
      machine.id = result.data?.id
      ElMessage.success('設備追加成功')
    }

    console.log('設備操作成功:', machine)
  } catch (e: unknown) {
    console.error('設備操作失敗:', e)
    ElMessage.error('設備操作に失敗しました')
  } finally {
    loading.value = false
  }
}

// 単一設備削除機能
const deleteMachine = async (step: ProductRouteStep, machineIndex: number) => {
  const machine = step.machines?.[machineIndex]
  if (!machine) return

  try {
    const confirmed = await ElMessageBox.confirm(
      `設備 "${machine.machine_name || machine.machine_cd}" を削除しますか？`,
      '削除確認',
      {
        confirmButtonText: '確定',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      },
    )

    if (!confirmed) return

    loading.value = true

    if (machine.id) {
      // データベースから設備を削除
      await request.delete(`/api/master/product/process/routes/machines/${machine.id}`)
      console.log('データベースから設備を削除:', machine.id)
    }

    // フロントエンド配列から削除
    step.machines?.splice(machineIndex, 1)
    ElMessage.success('設備削除成功')
    console.log('設備削除成功:', machine.machine_cd)
  } catch (e: unknown) {
    if (e !== false) {
      // ユーザーキャンセルではない
      console.error('設備削除失敗:', e)
      ElMessage.error('設備削除に失敗しました')
    }
  } finally {
    loading.value = false
  }
}

const removeMachine = (step: ProductRouteStep, idx: number) => {
  // 削除機能を呼び出し
  deleteMachine(step, idx)
}
</script>

<style scoped>
.route-step-card {
  padding: 8px;
}

.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.button-group > .el-button + .el-button {
  margin-left: 8px;
}

.loading-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
  color: #606266;
  gap: 10px;
}

.loading-message .el-icon {
  font-size: 24px;
}

.empty-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 30px 0;
  color: #909399;
  gap: 10px;
}

.empty-message .el-icon {
  font-size: 36px;
  color: #c0c4cc;
}

.empty-message p {
  margin: 0;
  font-size: 16px;
}

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-card {
  width: 100%;
}

.process-card {
  border: 1px solid #e4e7ed;
  border-radius: 6px;
}

.process-card :deep(.el-card__header) {
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.process-card :deep(.el-card__body) {
  padding: 12px 16px;
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

.process-name {
  font-size: 16px;
  color: #303133;
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
  color: #606266;
  font-size: 14px;
}

.no-machines {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px 16px;
  color: #909399;
  background-color: #f5f7fa;
  border-radius: 4px;
  gap: 8px;
}

.no-machines .el-icon {
  font-size: 24px;
  color: #c0c4cc;
}

.no-machines p {
  margin: 0;
  font-size: 14px;
}

.machines-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: 10px;
}

.machine-card {
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background-color: #fafafa;
  transition: all 0.3s ease;
}

.machine-card.machine-saved {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.machine-card.machine-new {
  border-color: #e6a23c;
  background-color: #fdf6ec;
}

.machine-form {
  padding: 10px;
}

.machine-status {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
}

.form-item {
  display: flex;
  flex-direction: column;
}

.form-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 4px;
  font-weight: 500;
}

.machine-actions {
  display: flex;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 6px;
}

.machine-actions .el-button {
  min-width: 70px;
}

.device-count {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
  font-weight: 500;
}

.device-count:hover {
  color: #66b1ff;
}

/* ドラッグ関連スタイル */
.draggable-steps {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  background-color: #f5f7fa;
  border: 1px dashed #dcdfe6;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.drag-handle:hover {
  color: #409eff;
  background-color: #ecf5ff;
  border-color: #b3d8ff;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-icon {
  font-size: 12px;
}

.drag-text {
  font-size: 10px;
}

.step-card {
  transition: all 0.3s ease;
}

.step-card.dragging {
  opacity: 0.8;
  transform: rotate(2deg);
}

/* ドラッグ状態スタイル */
.ghost-step {
  opacity: 0.5;
  background-color: #f0f9ff;
  border: 2px dashed #409eff;
  border-radius: 8px;
}

.chosen-step {
  background-color: #ecf5ff;
  border: 2px solid #409eff;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.drag-step {
  transform: rotate(5deg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* レスポンシブデザイン */
@media (max-width: 768px) {
  .route-step-card {
    padding: 6px;
  }

  .draggable-steps {
    gap: 10px;
  }

  .process-card :deep(.el-card__header) {
    padding: 10px 12px;
  }

  .process-card :deep(.el-card__body) {
    padding: 10px 12px;
  }

  .machines-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .form-row {
    grid-template-columns: 1fr;
    gap: 8px;
    margin-bottom: 8px;
  }

  .process-header {
    flex-direction: column;
    gap: 6px;
    align-items: flex-start;
  }

  .drag-handle {
    padding: 2px 4px;
    font-size: 10px;
  }

  .machine-form {
    padding: 8px;
  }

  .machine-actions {
    gap: 4px;
    margin-top: 4px;
  }
}
</style>
