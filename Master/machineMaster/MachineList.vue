<template>
  <div class="machine-master-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="main-title">
            <el-icon class="title-icon">
              <Tools />
            </el-icon>
            設備マスタ管理
          </h1>
          <p class="subtitle">設備情報の登録・編集・管理を行います</p>
        </div>
        <div class="header-stats">
          <div class="stat-card">
            <div class="stat-number">{{ machines?.length || 0 }}</div>
            <div class="stat-label">総設備数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ activeMachinesCount }}</div>
            <div class="stat-label">稼働中</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">{{ averageEfficiency }}%</div>
            <div class="stat-label">平均効率</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 功能操作区域 -->
    <div class="action-section">
      <!-- 筛选标题 -->
      <div class="filter-header">
        <div class="filter-title">
          <el-icon class="filter-icon">
            <Filter />
          </el-icon>
          <span>検索・絞り込み</span>
        </div>
        <div class="filter-actions">
          <el-button text @click="clearFilters" :icon="Refresh" class="clear-btn">
            クリア
          </el-button>
          <el-button
            type="warning"
            @click="openMachineTypeSelector"
            :icon="Printer"
            :disabled="filteredMachines.length === 0"
            class="qr-print-btn"
          >
            QRコード印刷
          </el-button>
          <el-button
            type="success"
            @click="exportToCSV"
            :icon="Download"
            :disabled="filteredMachines.length === 0"
            class="export-csv-btn"
          >
            CSV出力
          </el-button>
          <el-button type="primary" @click="openDialog()" :icon="Plus" class="add-machine-btn">
            設備追加
          </el-button>
        </div>
      </div>

      <!-- 筛选内容 -->
      <div class="filters-grid">
        <!-- 搜索框 -->
        <div class="filter-item search-item">
          <label class="filter-label">
            <el-icon>
              <Search />
            </el-icon>
            キーワード検索
          </label>
          <el-input
            v-model="filters.searchText"
            placeholder="設備CD・設備名で検索"
            clearable
            @input="handleFilter"
            class="filter-input"
          >
            <template #suffix>
              <el-icon v-if="filters.searchText" class="search-active">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>

        <!-- 设备类型筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <Management />
            </el-icon>
            設備タイプ
          </label>
          <el-select
            v-model="filters.machineType"
            placeholder="全てのタイプ"
            multiple
            collapse-tags
            collapse-tags-tooltip
            clearable
            @change="handleFilter"
            class="filter-input"
          >
            <el-option label="切断" value="切断">
              <div class="type-option">
                <el-tag type="primary" size="small">切断</el-tag>
                <span class="type-desc">カッティング</span>
              </div>
            </el-option>
            <el-option label="面取" value="面取">
              <div class="type-option">
                <el-tag type="success" size="small">面取</el-tag>
                <span class="type-desc">エッジング</span>
              </div>
            </el-option>
            <el-option label="SW" value="SW">
              <div class="type-option">
                <el-tag type="warning" size="small">SW</el-tag>
                <span class="type-desc">スイッチング</span>
              </div>
            </el-option>
            <el-option label="成型" value="成型">
              <div class="type-option">
                <el-tag type="info" size="small">成型</el-tag>
                <span class="type-desc">モールディング</span>
              </div>
            </el-option>
            <el-option label="溶接" value="溶接">
              <div class="type-option">
                <el-tag type="danger" size="small">溶接</el-tag>
                <span class="type-desc">ウェルディング</span>
              </div>
            </el-option>
            <el-option label="メッキ" value="メッキ">
              <div class="type-option">
                <el-tag color="#8e44ad" size="small">メッキ</el-tag>
                <span class="type-desc">プレーティング</span>
              </div>
            </el-option>
            <el-option label="検査" value="検査">
              <div class="type-option">
                <el-tag color="#2c3e50" size="small">検査</el-tag>
                <span class="type-desc">インスペクション</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 状态筛选 -->
        <div class="filter-item">
          <label class="filter-label">
            <el-icon>
              <CircleCheck />
            </el-icon>
            稼働状態
          </label>
          <el-select
            v-model="filters.status"
            placeholder="全ての状態"
            clearable
            @change="handleFilter"
            class="filter-input"
          >
            <el-option label="稼働中" value="active">
              <div class="status-option">
                <el-tag type="success" size="small">稼働中</el-tag>
                <span class="status-desc">正常稼働</span>
              </div>
            </el-option>
            <el-option label="修理中" value="maintenance">
              <div class="status-option">
                <el-tag type="warning" size="small">修理中</el-tag>
                <span class="status-desc">メンテナンス</span>
              </div>
            </el-option>
            <el-option label="停止中" value="inactive">
              <div class="status-option">
                <el-tag type="info" size="small">停止中</el-tag>
                <span class="status-desc">停止状態</span>
              </div>
            </el-option>
          </el-select>
        </div>

        <!-- 效率范围筛选 -->
        <div class="filter-item efficiency-range">
          <label class="filter-label">
            <el-icon>
              <DataAnalysis />
            </el-icon>
            効率範囲
          </label>
          <div class="efficiency-inputs">
            <el-input-number
              v-model="filters.minEfficiency"
              placeholder="最小"
              :min="0"
              :max="300"
              @change="handleFilter"
              size="small"
              controls-position="right"
            />
            <span class="range-separator">〜</span>
            <el-input-number
              v-model="filters.maxEfficiency"
              placeholder="最大"
              :min="0"
              :max="300"
              @change="handleFilter"
              size="small"
              controls-position="right"
            />
          </div>
        </div>
      </div>

      <!-- 筛选结果摘要 -->
      <div class="filter-summary" v-if="hasActiveFilters">
        <div class="summary-text">
          <el-icon class="summary-icon">
            <InfoFilled />
          </el-icon>
          <span>{{ filteredMachines.length }}件 / {{ machines?.length || 0 }}件中を表示</span>
        </div>
        <div class="active-filters">
          <el-tag
            v-if="filters.searchText"
            closable
            @close="
              () => {
                filters.searchText = ''
                handleFilter()
              }
            "
            type="primary"
            size="small"
          >
            検索: {{ filters.searchText }}
          </el-tag>
          <el-tag
            v-if="filters.machineType && filters.machineType.length > 0"
            closable
            @close="
              () => {
                filters.machineType = []
                handleFilter()
              }
            "
            type="warning"
            size="small"
          >
            タイプ: {{ filters.machineType.join(', ') }}
          </el-tag>
          <el-tag
            v-if="filters.status"
            closable
            @close="
              () => {
                filters.status = ''
                handleFilter()
              }
            "
            type="info"
            size="small"
          >
            状態: {{ getStatusText(filters.status) }}
          </el-tag>
          <el-tag
            v-if="filters.minEfficiency !== undefined || filters.maxEfficiency !== undefined"
            closable
            @close="clearEfficiencyRange"
            type="success"
            size="small"
          >
            効率: {{ filters.minEfficiency || 0 }}% 〜 {{ filters.maxEfficiency || 300 }}%
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 设备卡片视图（移动端） -->
    <div class="mobile-view" v-if="isMobile">
      <div class="machines-grid">
        <div
          v-for="machine in filteredMachines"
          :key="machine.id"
          class="machine-card"
          @click="openDialog(machine)"
        >
          <div class="machine-avatar">
            <el-icon>
              <Tools />
            </el-icon>
          </div>
          <div class="machine-info">
            <h3 class="machine-name">{{ machine.machine_name }}</h3>
            <p class="machine-code">{{ machine.machine_cd }}</p>
            <p class="machine-type">
              <el-icon>
                <Management />
              </el-icon>
              {{ machine.machine_type }}
            </p>
            <p class="machine-time" v-if="machine.available_from && machine.available_to">
              <el-icon>
                <Clock />
              </el-icon>
              {{ machine.available_from }} 〜 {{ machine.available_to }}
            </p>
            <div class="machine-meta">
              <el-tag :type="getStatusTagType(machine.status || '')" size="small">
                {{ getStatusText(machine.status || '') }}
              </el-tag>
              <el-tag color="#8e44ad" size="small" v-if="machine.efficiency">
                効率: {{ machine.efficiency }}%
              </el-tag>
            </div>
          </div>
          <div class="machine-actions">
            <el-dropdown @command="handleCommand">
              <el-button circle size="small" :icon="MoreFilled" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="`edit-${machine.id}`" :icon="Edit"
                    >編集</el-dropdown-item
                  >
                  <el-dropdown-item :command="`delete-${machine.id}`" :icon="Delete" divided
                    >削除</el-dropdown-item
                  >
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </div>

    <!-- 表格视图（桌面端） -->
    <div class="desktop-view" v-else>
      <el-card class="table-card">
        <el-table
          :data="filteredMachines"
          stripe
          highlight-current-row
          v-loading="loading"
          class="modern-table"
        >
          <el-table-column prop="machine_cd" label="設備CD" width="120" align="center">
            <template #default="{ row }">
              <div class="machine-code-cell">
                <el-icon class="code-icon">
                  <Tickets />
                </el-icon>
                <span>{{ row.machine_cd }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="machine_name" label="設備名" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              <div class="machine-name-cell">
                <el-icon class="name-icon">
                  <Tools />
                </el-icon>
                <span>{{ row.machine_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="machine_type" label="タイプ" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getMachineTypeTagType(row.machine_type)" size="small">
                {{ row.machine_type }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状態" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status || '')" size="small">
                {{ getStatusText(row.status || '') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="稼働時間" width="200" align="center">
            <template #default="{ row }">
              <div v-if="row.available_from && row.available_to" class="time-cell">
                <el-icon class="time-icon">
                  <Clock />
                </el-icon>
                <span>{{ row.available_from }} 〜 {{ row.available_to }}</span>
              </div>
              <span v-else class="no-data">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="efficiency" label="効率" width="100" align="center">
            <template #default="{ row }">
              <div v-if="row.efficiency !== undefined" class="efficiency-cell">
                <el-progress
                  :percentage="Math.min(row.efficiency, 100)"
                  :color="getEfficiencyColor(row.efficiency)"
                  :stroke-width="8"
                  :show-text="false"
                />
                <span class="efficiency-text">{{ row.efficiency }}%</span>
              </div>
              <span v-else class="no-data">—</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" fixed="right" width="140" align="center">
            <template #default="{ row }">
              <div class="action-buttons-table">
                <el-button size="small" type="primary" link @click="openDialog(row)" :icon="Edit">
                  編集
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  link
                  @click="handleDelete(row.id)"
                  :icon="Delete"
                >
                  削除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 结果统计 -->
    <div class="result-section">
      <div class="result-info">
        表示件数: {{ filteredMachines.length }} / {{ machines?.length || 0 }}
      </div>
    </div>

    <!-- 设备表单弹窗 -->
    <MachineEditDialog v-model="dialogVisible" :machine="selectedMachine" @saved="loadData" />

    <!-- 设备类型选择弹窗 -->
    <el-dialog
      v-model="machineTypeSelectorVisible"
      title="設備タイプ選択"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-checkbox-group v-model="selectedMachineTypes" class="machine-type-checkbox-group">
        <el-checkbox label="切断" />
        <el-checkbox label="面取" />
        <el-checkbox label="SW" />
        <el-checkbox label="成型" />
        <el-checkbox label="溶接" />
        <el-checkbox label="メッキ" />
        <el-checkbox label="検査" />
        <el-checkbox label="その他" />
      </el-checkbox-group>
      <template #footer>
        <el-button @click="machineTypeSelectorVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="confirmMachineTypeSelection">確定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useWindowSize } from '@vueuse/core'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Tools,
  Filter,
  Refresh,
  Plus,
  Search,
  Management,
  CircleCheck,
  DataAnalysis,
  InfoFilled,
  Edit,
  Delete,
  MoreFilled,
  Clock,
  Tickets,
  Printer,
  Download,
} from '@element-plus/icons-vue'
import { fetchMachines, deleteMachine, exportMachineToCSV } from '@/api/master/machineMaster'
import MachineEditDialog from './MachineEditDialog.vue'
import { Machine } from '@/types/master'

// 响应式检测
const { width } = useWindowSize()
const isMobile = computed(() => width.value < 768)

// 数据状态
const machines = ref<Machine[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const selectedMachine = ref<Machine | null>(null)
const machineTypeSelectorVisible = ref(false)
const selectedMachineTypes = ref<string[]>([])

// 筛选状态
const filters = ref({
  searchText: '',
  machineType: [] as string[],
  status: '',
  minEfficiency: undefined as number | undefined,
  maxEfficiency: undefined as number | undefined,
})

// 计算属性
const activeMachinesCount = computed(
  () => (machines.value || []).filter((machine) => machine.status === 'active').length,
)

const averageEfficiency = computed(() => {
  const validMachines = (machines.value || []).filter((machine) => machine.efficiency !== undefined)
  if (validMachines.length === 0) return 0
  const total = validMachines.reduce((sum, machine) => sum + (machine.efficiency || 0), 0)
  return Math.round(total / validMachines.length)
})

const hasActiveFilters = computed(() => {
  return (
    filters.value.searchText ||
    (filters.value.machineType && filters.value.machineType.length > 0) ||
    filters.value.status ||
    filters.value.minEfficiency !== undefined ||
    filters.value.maxEfficiency !== undefined
  )
})

// 筛选后的设备列表
const filteredMachines = computed(() => {
  let result = machines.value || []

  // 按搜索文本筛选（设备CD或设备名）
  if (filters.value.searchText) {
    const searchText = filters.value.searchText.toLowerCase()
    result = result.filter(
      (machine) =>
        machine.machine_cd?.toLowerCase().includes(searchText) ||
        machine.machine_name?.toLowerCase().includes(searchText),
    )
  }

  // 按设备类型筛选（支持多选）
  if (filters.value.machineType && filters.value.machineType.length > 0) {
    result = result.filter(
      (machine) => machine.machine_type && filters.value.machineType.includes(machine.machine_type),
    )
  }

  // 按状态筛选
  if (filters.value.status) {
    result = result.filter((machine) => machine.status === filters.value.status)
  }

  // 按效率范围筛选
  if (filters.value.minEfficiency !== undefined) {
    result = result.filter(
      (machine) =>
        machine.efficiency !== undefined && machine.efficiency >= filters.value.minEfficiency!,
    )
  }

  if (filters.value.maxEfficiency !== undefined) {
    result = result.filter(
      (machine) =>
        machine.efficiency !== undefined && machine.efficiency <= filters.value.maxEfficiency!,
    )
  }

  return result
})

// 辅助函数
const getMachineTypeTagType = (type: string) => {
  const typeMap: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = {
    切断: 'primary',
    面取: 'success',
    SW: 'warning',
    成型: 'info',
    溶接: 'danger',
    メッキ: 'warning',
    検査: 'info',
  }
  return typeMap[type] || 'info'
}

const getStatusTagType = (status: string) => {
  switch (status) {
    case 'active':
      return 'success'
    case 'maintenance':
      return 'warning'
    case 'inactive':
      return 'info'
    default:
      return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active':
      return '稼働中'
    case 'maintenance':
      return '修理中'
    case 'inactive':
      return '停止中'
    default:
      return status
  }
}

const getEfficiencyColor = (efficiency: number) => {
  if (efficiency >= 90) return '#67c23a'
  if (efficiency >= 70) return '#e6a23c'
  return '#f56c6c'
}

// 事件处理
const handleFilter = () => {
  // 筛选逻辑已通过computed属性实现
}

const clearFilters = () => {
  filters.value = {
    searchText: '',
    machineType: [],
    status: '',
    minEfficiency: undefined,
    maxEfficiency: undefined,
  }
}

const clearEfficiencyRange = () => {
  filters.value.minEfficiency = undefined
  filters.value.maxEfficiency = undefined
  handleFilter()
}

const handleCommand = (command: string) => {
  const [action, machineId] = command.split('-')
  const machine = (machines.value || []).find((m) => m.id === parseInt(machineId))

  if (!machine) return

  if (action === 'edit') {
    openDialog(machine)
  } else if (action === 'delete') {
    handleDelete(machine.id)
  }
}

// 数据操作
const loadData = async () => {
  loading.value = true
  try {
    const response: any = await fetchMachines()
    console.log('API 返回数据:', response)

    // 处理不同的数据结构
    if (Array.isArray(response)) {
      // 如果拦截器直接返回了数组
      machines.value = response
    } else if (response?.data && Array.isArray(response.data)) {
      // 如果返回的是 { success: true, data: [...] }
      machines.value = response.data
    } else if (response?.list && Array.isArray(response.list)) {
      // 如果返回的是 { list: [...], total: ... }
      machines.value = response.list
    } else {
      console.warn('未知的数据结构:', response)
      machines.value = []
    }
  } catch (error) {
    console.error('設備データの読み込みエラー:', error)
    ElMessage.error('設備データの読み込みに失敗しました')
    machines.value = []
  } finally {
    loading.value = false
  }
}

const openDialog = (machine?: Machine) => {
  selectedMachine.value = machine ? { ...machine } : null
  dialogVisible.value = true
}

const handleDelete = async (id: number | undefined) => {
  if (!id) {
    ElMessage.error('設備IDが無効です')
    return
  }

  try {
    await ElMessageBox.confirm('この設備を削除しますか？', '確認', {
      type: 'warning',
      confirmButtonText: 'はい',
      cancelButtonText: 'キャンセル',
    })

    await deleteMachine(id)
    ElMessage.success('削除しました')
    loadData()
  } catch {
    // ユーザーがキャンセルした場合は何もしない
  }
}

// 将特殊类型归类到"その他"
const normalizeMachineType = (type: string | undefined): string => {
  if (!type) return 'その他'

  const otherTypes = ['外注検査', '外注溶接', '外注メッキ', '外注成型', '溶接前検査', '外注切断']

  if (otherTypes.includes(type)) {
    return 'その他'
  }

  return type
}

// 打开设备类型选择器
const openMachineTypeSelector = () => {
  if (filteredMachines.value.length === 0) {
    ElMessage.warning('印刷する設備がありません')
    return
  }
  // 获取所有可用的设备类型（规范化后）
  const normalizedTypes = filteredMachines.value
    .map((m) => normalizeMachineType(m.machine_type))
    .filter((type): type is string => !!type)

  const availableTypes = Array.from(new Set(normalizedTypes))

  // 确保有"その他"选项（如果有特殊类型）
  const hasOtherTypes = filteredMachines.value.some((m) => {
    const otherTypes = ['外注検査', '外注溶接', '外注メッキ', '外注成型', '溶接前検査', '外注切断']
    return m.machine_type && otherTypes.includes(m.machine_type)
  })

  if (hasOtherTypes && !availableTypes.includes('その他')) {
    availableTypes.push('その他')
  }

  // 默认不选中任何类型
  selectedMachineTypes.value = []
  machineTypeSelectorVisible.value = true
}

// 确认设备类型选择
const confirmMachineTypeSelection = async () => {
  if (selectedMachineTypes.value.length === 0) {
    ElMessage.warning('印刷する設備タイプを選択してください。')
    return
  }
  machineTypeSelectorVisible.value = false
  await generateAndPrintQRCodes()
}

// 生成二维码并打印
const generateAndPrintQRCodes = async () => {
  // 根据选择的类型过滤设备（考虑类型规范化）
  let machinesToPrint = filteredMachines.value
  if (selectedMachineTypes.value.length > 0) {
    machinesToPrint = machinesToPrint.filter((machine) => {
      const normalizedType = normalizeMachineType(machine.machine_type)
      return selectedMachineTypes.value.includes(normalizedType)
    })
  }

  if (machinesToPrint.length === 0) {
    ElMessage.warning('印刷する設備がありません')
    return
  }

  try {
    // 动态导入 qrcode 库
    let QRCode: any
    try {
      QRCode = (await import('qrcode')).default
    } catch (error) {
      ElMessage.error(
        'QRコードライブラリが見つかりません。以下のコマンドでインストールしてください: npm install qrcode',
      )
      return
    }

    // 创建打印窗口内容
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.error('ポップアップがブロックされました。ブラウザの設定を確認してください')
      return
    }

    // 按设备名排序
    const sortedMachines = [...machinesToPrint].sort((a, b) => {
      const nameA = a.machine_name || ''
      const nameB = b.machine_name || ''
      return nameA.localeCompare(nameB, 'ja')
    })

    // 生成所有二维码（按排序后的顺序）
    const qrCodes: Array<{ dataUrl: string; machine: Machine }> = []
    for (const machine of sortedMachines) {
      if (machine.machine_cd) {
        try {
          const qrDataUrl = await QRCode.toDataURL(machine.machine_cd, {
            width: 95,
            margin: 2,
            color: {
              dark: '#000000',
              light: '#FFFFFF',
            },
          })
          qrCodes.push({ dataUrl: qrDataUrl, machine })
        } catch (error) {
          console.error(`QRコード生成エラー (${machine.machine_cd}):`, error)
        }
      }
    }

    if (qrCodes.length === 0) {
      printWindow.close()
      ElMessage.error('QRコードの生成に失敗しました')
      return
    }

    // 创建打印HTML（A4纸纵向布局，每行5个二维码，每页40个）
    const qrCodesPerRow = 5 // A4纵向每行5个
    const qrCodesPerPage = 40 // A4纵向可以放40个二维码（每行5个，共8行）
    const totalPages = qrCodes.length > 0 ? Math.ceil(qrCodes.length / qrCodesPerPage) : 0

    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>設備QRコード印刷</title>
        <style>
          @page {
            size: A4 portrait;
            margin: 0;
          }
          body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
          }
          .page {
            width: 210mm;
            height: 297mm;
            padding: 12mm;
            margin: 0;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
          }
          .page:not(:last-child) {
            page-break-after: always;
          }
          .page:last-child {
            page-break-after: avoid;
          }
          .page-title {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 8mm;
            color: #333;
            flex-shrink: 0;
          }
          .qr-grid {
            display: grid;
            grid-template-columns: repeat(${qrCodesPerRow}, 1fr);
            grid-template-rows: repeat(8, 1fr);
            gap: 1.2mm;
            width: 100%;
            height: 100%;
            align-content: start;
          }
          .qr-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1mm;
            border: 1px solid #ddd;
            border-radius: 2px;
            page-break-inside: avoid;
            box-sizing: border-box;
          }
          .qr-code {
            width: 70px;
            height: 70px;
            margin-bottom: 2px;
            flex-shrink: 0;
          }
          .qr-machine-name {
            font-size: 12px;
            font-weight: bold;
            text-align: center;
            color: #000;
            word-break: break-all;
            line-height: 1.3;
            margin-top: 2px;
            padding: 0 2px;
          }
          @media print {
            body {
              margin: 0;
              padding: 0;
            }
            .page {
              margin: 0;
              padding: 12mm;
            }
          }
        </style>
      </head>
      <body>
    `

    // 生成每一页（横向填充）
    for (let page = 0; page < totalPages; page++) {
      const startIndex = page * qrCodesPerPage
      const endIndex = Math.min(startIndex + qrCodesPerPage, qrCodes.length)

      // 如果这一页没有内容，跳过
      if (startIndex >= qrCodes.length || endIndex <= startIndex) {
        break
      }

      // 获取这一页的二维码数据（已经按设备名排序）
      const pageQRCodes = qrCodes.slice(startIndex, endIndex)

      // 如果这一页没有数据，跳过（防止空白页）
      if (pageQRCodes.length === 0) {
        break
      }

      html += `<div class="page">`
      html += `<div class="page-title">設備マスタQR</div>`
      html += `<div class="qr-grid">`

      // 横向填充：第1行从左到右，然后第2行从左到右，以此类推
      for (let i = 0; i < pageQRCodes.length; i++) {
        const { dataUrl, machine } = pageQRCodes[i]
        // 计算在网格中的位置（横向填充）
        const col = i % qrCodesPerRow // 列索引（0-4）
        const row = Math.floor(i / qrCodesPerRow) // 行索引（0-7）
        const gridColumn = col + 1 // CSS Grid 列从1开始
        const gridRow = row + 1 // CSS Grid 行从1开始

        html += `
          <div class="qr-item" style="grid-column: ${gridColumn}; grid-row: ${gridRow};">
            <img src="${dataUrl}" alt="${machine.machine_cd}" class="qr-code" />
            ${machine.machine_name ? `<div class="qr-machine-name">${machine.machine_name}</div>` : ''}
          </div>
        `
      }

      html += `</div></div>`
    }

    html += `
      </body>
      </html>
    `

    // 写入打印窗口
    printWindow.document.write(html)
    printWindow.document.close()

    // 等待内容加载完成后打印
    printWindow.onload = () => {
      setTimeout(() => {
        let isClosed = false
        let fallbackTimeout: ReturnType<typeof setTimeout> | null = null

        // 关闭窗口的函数
        const closeWindow = () => {
          if (!isClosed) {
            isClosed = true
            // 清除备用定时器
            if (fallbackTimeout) {
              clearTimeout(fallbackTimeout)
              fallbackTimeout = null
            }
            // 延迟关闭，确保打印对话框已经完全关闭
            setTimeout(() => {
              try {
                printWindow.close()
              } catch (error) {
                console.error('窗口关闭エラー:', error)
              }
            }, 100)
          }
        }

        // 监听 afterprint 事件（打印对话框关闭后触发，无论是打印还是取消）
        printWindow.addEventListener('afterprint', closeWindow)

        // 监听窗口焦点变化（当打印对话框关闭，窗口重新获得焦点时）
        let focusTimeout: ReturnType<typeof setTimeout> | null = null
        printWindow.addEventListener('focus', () => {
          // 延迟关闭，确保打印对话框已经完全关闭
          if (focusTimeout) {
            clearTimeout(focusTimeout)
          }
          focusTimeout = setTimeout(() => {
            closeWindow()
          }, 300)
        })

        // 备用方案：如果 afterprint 事件不触发，使用定时器（5秒后自动关闭）
        fallbackTimeout = setTimeout(() => {
          if (!isClosed) {
            closeWindow()
          }
        }, 5000)

        // 开始打印
        printWindow.print()
      }, 250)
    }

    ElMessage.success(`${qrCodes.length}件のQRコードを生成しました`)
  } catch (error) {
    console.error('QRコード生成エラー:', error)
    ElMessage.error('QRコードの生成に失敗しました')
  }
}

// 导出CSV文件
const exportToCSV = async () => {
  try {
    loading.value = true

    // 获取所有分页数据（不分页）
    const allDataResponse: any = await fetchMachines()

    let allMachinesData: Machine[] = []
    if (Array.isArray(allDataResponse)) {
      allMachinesData = allDataResponse
    } else if (allDataResponse?.data && Array.isArray(allDataResponse.data)) {
      allMachinesData = allDataResponse.data
    } else if (allDataResponse?.list && Array.isArray(allDataResponse.list)) {
      allMachinesData = allDataResponse.list
    } else {
      allMachinesData = []
    }

    // 应用筛选条件
    let filteredData = allMachinesData

    // 按搜索文本筛选（设备CD或设备名）
    if (filters.value.searchText) {
      const searchText = filters.value.searchText.toLowerCase()
      filteredData = filteredData.filter(
        (machine) =>
          machine.machine_cd?.toLowerCase().includes(searchText) ||
          machine.machine_name?.toLowerCase().includes(searchText),
      )
    }

    // 按设备类型筛选（支持多选）
    if (filters.value.machineType && filters.value.machineType.length > 0) {
      filteredData = filteredData.filter(
        (machine) =>
          machine.machine_type && filters.value.machineType.includes(machine.machine_type),
      )
    }

    // 按状态筛选
    if (filters.value.status) {
      filteredData = filteredData.filter((machine) => machine.status === filters.value.status)
    }

    // 按效率范围筛选
    if (filters.value.minEfficiency !== undefined) {
      filteredData = filteredData.filter(
        (machine) =>
          machine.efficiency !== undefined && machine.efficiency >= filters.value.minEfficiency!,
      )
    }

    if (filters.value.maxEfficiency !== undefined) {
      filteredData = filteredData.filter(
        (machine) =>
          machine.efficiency !== undefined && machine.efficiency <= filters.value.maxEfficiency!,
      )
    }

    if (filteredData.length === 0) {
      ElMessage.warning('出力する設備がありません')
      return
    }

    // 准备导出数据：只包含設備CD和設備名
    const exportData = filteredData.map((machine) => ({
      machine_cd: machine.machine_cd || '',
      machine_name: machine.machine_name || '',
    }))

    // 调用后端API导出CSV
    await exportMachineToCSV(exportData)

    ElMessage.success(`${exportData.length}件のデータをCSVファイルに出力しました`)
  } catch (error) {
    console.error('CSV出力エラー:', error)
    ElMessage.error('CSVファイルの出力に失敗しました')
  } finally {
    loading.value = false
  }
}

// 页面初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.machine-master-container {
  padding: 12px;
  background: linear-gradient(135deg, #f3e7f8 0%, #d1c4e9 100%);
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.title-section {
  flex: 1;
}

.main-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 4px;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 1.4rem;
  color: #8e44ad;
}

.subtitle {
  color: #7f8c8d;
  margin: 0;
  font-size: 0.85rem;
}

.header-stats {
  display: flex;
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 10px;
  text-align: center;
  min-width: 100px;
  box-shadow: 0 2px 8px rgba(142, 68, 173, 0.3);
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.8rem;
  opacity: 0.9;
  margin-top: 2px;
}

/* 操作区域 */
.action-section {
  background: white;
  border-radius: 12px;
  padding: 0;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

/* 筛选标题区 */
.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: #2d3748;
}

.filter-icon {
  font-size: 1.3rem;
  color: #8e44ad;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.clear-btn {
  color: #718096;
  transition: all 0.3s ease;
}

.clear-btn:hover {
  color: #8e44ad;
  transform: scale(1.05);
}

.qr-print-btn {
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(243, 156, 18, 0.3);
  transition: all 0.3s ease;
  color: white;
}

.qr-print-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(243, 156, 18, 0.4);
}

.qr-print-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.export-csv-btn {
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(39, 174, 96, 0.3);
  transition: all 0.3s ease;
  color: white;
}

.export-csv-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(39, 174, 96, 0.4);
}

.export-csv-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.add-machine-btn {
  background: linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(142, 68, 173, 0.3);
  transition: all 0.3s ease;
}

.add-machine-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(142, 68, 173, 0.4);
}

/* 筛选网格 */
.filters-grid {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr;
  gap: 16px;
  padding: 16px;
  background: white;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.search-item {
  grid-column: span 1;
}

.efficiency-range {
  grid-column: span 1;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  color: #4a5568;
  margin-bottom: 4px;
}

.filter-label .el-icon {
  font-size: 1rem;
  color: #8e44ad;
}

.filter-input {
  transition: all 0.3s ease;
}

.filter-input:hover {
  transform: translateY(-1px);
}

.efficiency-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-separator {
  color: #8e44ad;
  font-weight: 600;
}

.search-active {
  color: #8e44ad;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.5;
  }
}

/* 选项样式 */
.type-option,
.status-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  gap: 8px;
}

.type-desc,
.status-desc {
  font-size: 0.8rem;
  color: #718096;
  margin-left: 8px;
}

/* 筛选摘要 */
.filter-summary {
  padding: 12px 16px;
  background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
  border-top: 1px solid #e2e8f0;
}

.summary-text {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #4a5568;
  font-weight: 500;
}

.summary-icon {
  color: #8e44ad;
}

.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.active-filters .el-tag {
  cursor: pointer;
  transition: all 0.3s ease;
}

.active-filters .el-tag:hover {
  transform: scale(1.05);
}

/* 移动端卡片视图 */
.mobile-view {
  margin-bottom: 24px;
}

.machines-grid {
  display: grid;
  gap: 16px;
}

.machine-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.machine-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.machine-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8e44ad 0%, #9b59b6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.machine-info {
  flex: 1;
}

.machine-name {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 4px;
  color: #2c3e50;
}

.machine-code {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin: 0 0 8px;
  font-family: monospace;
}

.machine-type,
.machine-time {
  font-size: 0.9rem;
  color: #95a5a6;
  margin: 0 0 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.machine-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.machine-actions {
  flex-shrink: 0;
}

/* 桌面端表格视图 */
.desktop-view {
  margin-bottom: 24px;
}

.table-card {
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: none;
  margin-bottom: 12px;
}

.modern-table {
  border-radius: 12px;
  overflow: hidden;
}

.machine-code-cell,
.machine-name-cell,
.time-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.code-icon,
.name-icon,
.time-icon {
  color: #8e44ad;
  font-size: 1rem;
  flex-shrink: 0;
}

.efficiency-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.efficiency-text {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
}

.no-data {
  color: #bdc3c7;
  font-style: italic;
}

.action-buttons-table {
  display: flex;
  gap: 8px;
  justify-content: center;
}

/* 结果区域 */
.result-section {
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  text-align: center;
}

.result-info {
  color: #7f8c8d;
  font-size: 0.85rem;
}

/* 设备类型选择弹窗样式 */
.machine-type-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }

  .header-stats {
    align-self: stretch;
    justify-content: space-around;
  }

  .filters-grid {
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }

  .search-item {
    grid-column: span 2;
  }

  .efficiency-range {
    grid-column: span 2;
  }
}

@media (max-width: 768px) {
  .machine-master-container {
    padding: 16px;
  }

  .page-header {
    padding: 24px 20px;
  }

  .main-title {
    font-size: 1.6rem;
  }

  .filter-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 20px 24px;
  }

  .filter-actions {
    justify-content: stretch;
  }

  .filter-actions > * {
    flex: 1;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 24px 20px;
  }

  .search-item,
  .efficiency-range {
    grid-column: span 1;
  }

  .filter-summary {
    padding: 16px 20px;
  }

  .stat-card {
    min-width: auto;
    flex: 1;
  }

  .efficiency-inputs {
    flex-direction: column;
    gap: 8px;
  }

  .range-separator {
    display: none;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.4rem;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .machine-card {
    padding: 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .machine-actions {
    align-self: flex-end;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .machine-master-container {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .page-header,
  .action-section,
  .table-card,
  .result-section,
  .machine-card {
    background: rgba(45, 55, 72, 0.8);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .main-title {
    color: #e2e8f0;
  }

  .subtitle,
  .result-info {
    color: #a0aec0;
  }
}

/* 动画效果 */
.machine-card,
.table-card,
.page-header,
.action-section,
.result-section {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-table th) {
  background-color: #f8fafc;
  color: #2d3748;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #f7fafc;
}

:deep(.el-tag) {
  border-radius: 12px;
  font-weight: 500;
}

:deep(.el-progress-bar__outer) {
  border-radius: 6px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 6px;
}
</style>
