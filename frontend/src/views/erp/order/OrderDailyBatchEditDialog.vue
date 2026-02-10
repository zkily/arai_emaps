<template>
  <el-dialog
    :model-value="props.visible"
    @update:modelValue="(val) => emit('update:visible', val)"
    width="52%"
    top="2vh"
    destroy-on-close
    :before-close="handleClose"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    class="modern-daily-edit-dialog japanese-minimalist"
    :show-close="false"
  >
    <!-- カスタムヘッダー -->
    <template #header>
      <div class="dialog-header">
        <div class="header-content">
          <div class="title-section">
            <div class="title-icon">
              <el-icon>
                <Edit />
              </el-icon>
            </div>
            <div class="title-text">
              <h2 class="dialog-title">{{ t('orderDailyBatchEdit.title') }}</h2>
            </div>
            <div class="save-summary-header" v-if="changedRows.size > 0">
              <el-icon class="summary-icon">
                <InfoFilled />
              </el-icon>
              <span class="summary-text">{{ t('orderDailyBatchEdit.changesCount', { n: changedRows.size }) }}</span>
            </div>
          </div>
          <!-- 情報カードエリア -->
          <div class="info-section">
            <div class="stats-cards">
              <div class="stat-card">
                <div class="stat-icon total">
                  <el-icon>
                    <List />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-number">{{ orderDailyList.length }}</span>
                  <span class="stat-label">{{ t('orderDailyBatchEdit.statTotal') }}</span>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon changed">
                  <el-icon>
                    <Edit />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-number">{{ changedRows.size }}</span>
                  <span class="stat-label">{{ t('orderDailyBatchEdit.statChanged') }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="header-actions">
            <el-button
              :disabled="saving || orderDailyList.length === 0"
              @click="handlePrint"
              class="de-btn de-btn-print"
            >
              <el-icon><Printer /></el-icon>
              {{ t('orderDailyBatchEdit.btnPrint') }}
            </el-button>
            <el-button
              :disabled="saving || orderDailyList.length === 0"
              @click="handleUpdateForecastUnits"
              class="de-btn de-btn-forecast"
            >
              <el-icon><Refresh /></el-icon>
              {{ t('orderDailyBatchEdit.btnUpdateForecast') }}
            </el-button>
            <el-button
              :loading="saving"
              @click="handleBatchSave"
              class="de-btn de-btn-save"
              :disabled="changedRows.size === 0"
            >
              <el-icon><Check /></el-icon>
              {{ t('orderDailyBatchEdit.btnBatchSave') }}
            </el-button>
            <el-button class="de-btn de-btn-close" @click="handleClose">
              <el-icon><Close /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </template>

    <!-- Table（幅を保持しつつ小画面で横スクロール） -->
    <div class="table-responsive">
    <el-table
      v-loading="loading"
      :data="orderDailyList"
      border
      stripe
      show-summary
      :summary-method="getSummaries"
      :sum-text="t('orderDailyBatchEdit.sumText')"
      :default-sort="{ prop: 'date', order: 'ascending' }"
      class="daily-edit-table compact-table"
      height="476"
      size="small"
      :row-key="(row) => row.id"
      :row-class-name="tableRowClassName"
      :cell-style="{
        padding: '2px 4px',
        fontSize: '11px',
        fontWeight: '400',
        color: '#1f2937',
      }"
      :header-cell-style="{
        padding: '4px 4px',
        fontSize: '11px',
        fontWeight: '600',
        backgroundColor: '#f5f5f5',
        color: '#374151',
        textAlign: 'center',
      }"
    >
      <!-- <el-table-column label="納入先CD" prop="destination_cd" width="90" align="center" /> -->
      <el-table-column :label="t('orderDailyBatchEdit.colDestinationName')" prop="destination_name" width="146" />
      <el-table-column :label="t('orderDailyBatchEdit.colProductName')" prop="product_name" width="142" />
      <el-table-column :label="t('orderDailyBatchEdit.colProductType')" prop="product_type" width="90" align="center" />
      <el-table-column :label="t('orderDailyBatchEdit.colUnitPerBox')" prop="unit_per_box" width="55" align="center" />

      <el-table-column :label="t('orderDailyBatchEdit.colShipDate')" prop="date" width="110" align="center" sortable :sort-method="(a: OrderDaily, b: OrderDaily) => sortByDate(a.date, b.date)">
        <template #default="{ row }">
          <span class="cell-ship-date">{{ formatDateOnly(row.date) }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="t('orderDailyBatchEdit.colWeekday')" prop="weekday" width="50" align="center" />
      <el-table-column :label="t('orderDailyBatchEdit.colDeliveryDate')" prop="delivery_date" width="70" align="center">
        <template #default="{ row }">
          <span class="cell-delivery-date">{{ formatDate(row.delivery_date) }}</span>
        </template>
      </el-table-column>

      <!-- 確定箱数（編集） -->
      <el-table-column :label="t('orderDailyBatchEdit.colConfirmedBoxes')" prop="confirmed_boxes" width="100" align="center">
        <template #default="{ row, $index }">
          <el-input
            :disabled="saving"
            class="compact-input"
            :model-value="row.confirmed_boxes === 0 ? '' : row.confirmed_boxes"
            @update:model-value="
              (val) => {
                row.confirmed_boxes = val === '' ? 0 : Number(val)
                handleConfirmedBoxesChange(row)
              }
            "
            @keydown.enter="focusNextInput($index)"
            @keydown.up.prevent="handleKeyNavigationBoxes($event as KeyboardEvent, $index)"
            @keydown.down.prevent="handleKeyNavigationBoxes($event as KeyboardEvent, $index)"
            @keydown.left.prevent="handleKeyNavigationBoxes($event as KeyboardEvent, $index)"
            @keydown.right.prevent="handleKeyNavigationBoxes($event as KeyboardEvent, $index)"
            :ref="
              (el) => {
                if (el && '$el' in el) {
                  confirmedBoxesInputs[$index] =
                    (el.$el.querySelector('input') as HTMLInputElement) || undefined
                }
              }
            "
          />
        </template>
      </el-table-column>

      <!-- 確定本数（編集可能） -->
      <el-table-column :label="t('orderDailyBatchEdit.colConfirmedUnits')" prop="confirmed_units" width="100" align="center">
        <template #default="{ row, $index }">
          <el-input
            :model-value="row.confirmed_units === 0 ? '' : row.confirmed_units"
            :disabled="saving"
            class="compact-input"
            @update:model-value="
              (val) => {
                row.confirmed_units = val === '' ? 0 : Number(val)
                markRowChanged(row)
              }
            "
            @keydown.enter="focusNextConfirmedUnitsInput($index)"
            @keydown.up.prevent="handleKeyNavigationUnits($event as KeyboardEvent, $index)"
            @keydown.down.prevent="handleKeyNavigationUnits($event as KeyboardEvent, $index)"
            @keydown.left.prevent="handleKeyNavigationUnits($event as KeyboardEvent, $index)"
            @keydown.right.prevent="handleKeyNavigationUnits($event as KeyboardEvent, $index)"
            :ref="
              (el) => {
                if (el && '$el' in el) {
                  confirmedUnitsInputs[$index] =
                    (el.$el.querySelector('input') as HTMLInputElement) || undefined
                }
              }
            "
          />
        </template>
      </el-table-column>
      <!-- 内示本数（編集可能） -->
      <el-table-column :label="t('orderDailyBatchEdit.colForecastUnits')" prop="forecast_units" width="100" align="center">
        <template #default="{ row, $index }">
          <el-input
            :model-value="row.forecast_units === 0 ? '' : row.forecast_units"
            :disabled="saving"
            class="compact-input"
            @update:model-value="
              (val) => {
                row.forecast_units = val === '' ? 0 : Number(val)
                markRowChanged(row)
              }
            "
            @keydown.enter="focusNextForecastUnitsInput($index)"
            @keydown.up.prevent="handleKeyNavigationForecast($event as KeyboardEvent, $index)"
            @keydown.down.prevent="handleKeyNavigationForecast($event as KeyboardEvent, $index)"
            @keydown.left.prevent="handleKeyNavigationForecast($event as KeyboardEvent, $index)"
            @keydown.right.prevent="handleKeyNavigationForecast($event as KeyboardEvent, $index)"
            :ref="
              (el) => {
                if (el && '$el' in el) {
                  forecastUnitsInputs[$index] =
                    (el.$el.querySelector('input') as HTMLInputElement) || undefined
                }
              }
            "
          />
        </template>
      </el-table-column>
      <!-- 備考 -->
      <!-- <el-table-column label="備考" min-width="150">
        <template #default="{ row }">
          <el-input v-model="row.remarks" placeholder="備考" :disabled="saving" @input="markRowChanged(row)" />
        </template>
      </el-table-column> -->
    </el-table>
    </div>
    <div v-if="!loading && orderDailyList.length === 0" class="empty-message">
      {{ t('orderDailyBatchEdit.emptyNoData') }}
    </div>
    <div v-if="!loading && !props.monthlyOrderId" class="empty-message">
      {{ t('orderDailyBatchEdit.emptyNoMonthlyId') }}
    </div>

    <!-- Footer -->
    <template #footer>
      <div class="footer-section"></div>
    </template>

    <!-- 保存中オーバーレイ -->
    <el-overlay v-if="saving" class="global-saving-overlay" />
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { fetchDailyOrdersByMonthlyOrderId, batchUpdateDailyOrders } from '@/api/order/order'
import { ElMessage } from 'element-plus'
import { Edit, Close, List, Check, InfoFilled, Refresh, Printer } from '@element-plus/icons-vue'
import type { OrderDaily } from '@/types/order'

const { t } = useI18n()

// 日付フォーマット（日付列・納入日用）
const formatDateOnly = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  try {
    const d = new Date(dateString)
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  } catch (e) {
    return String(dateString)
  }
}
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  try {
    const d = new Date(dateString)
    return `${d.getMonth() + 1}/${d.getDate()}`
  } catch (e) {
    return String(dateString)
  }
}

/** 出荷日でソート用 */
const sortByDate = (dateA: string | null | undefined, dateB: string | null | undefined): number => {
  const ta = dateA ? new Date(dateA).getTime() : 0
  const tb = dateB ? new Date(dateB).getTime() : 0
  return ta - tb
}

const confirmedBoxesInputs = ref<(HTMLInputElement | undefined)[]>([])
const confirmedUnitsInputs = ref<(HTMLInputElement | undefined)[]>([])
const forecastUnitsInputs = ref<(HTMLInputElement | undefined)[]>([])

// Enterキーで次の入力欄に移動（確定箱数）
const focusNextInput = async (currentIndex: number) => {
  await nextTick()
  const nextInput = confirmedBoxesInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
    nextInput.select()
  }
}

// Enterキーで次の入力欄に移動（確定本数）
const focusNextConfirmedUnitsInput = async (currentIndex: number) => {
  await nextTick()
  const nextInput = confirmedUnitsInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
    nextInput.select()
  }
}

// Enterキーで次の入力欄に移動（内示本数）
const focusNextForecastUnitsInput = async (currentIndex: number) => {
  await nextTick()
  const nextInput = forecastUnitsInputs.value[currentIndex + 1]
  if (nextInput) {
    nextInput.focus()
    nextInput.select()
  }
}

// キーボード矢印キーで移動（確定箱数）
const handleKeyNavigationBoxes = async (event: KeyboardEvent, rowIndex: number) => {
  await handleKeyNavigation(event, rowIndex, 0)
}

// キーボード矢印キーで移動（確定本数）
const handleKeyNavigationUnits = async (event: KeyboardEvent, rowIndex: number) => {
  await handleKeyNavigation(event, rowIndex, 1)
}

// キーボード矢印キーで移動（内示本数）
const handleKeyNavigationForecast = async (event: KeyboardEvent, rowIndex: number) => {
  await handleKeyNavigation(event, rowIndex, 2)
}

// 共通のキーボードナビゲーション処理
const handleKeyNavigation = async (event: KeyboardEvent, rowIndex: number, colIndex: number) => {
  const totalRows = orderDailyList.value.length
  let targetRowIndex = rowIndex
  let targetColIndex = colIndex
  let targetInput: HTMLInputElement | undefined

  switch (event.key) {
    case 'ArrowUp':
      // 上に移動
      if (rowIndex > 0) {
        targetRowIndex = rowIndex - 1
        targetColIndex = colIndex
      } else {
        return // 最初の行なので移動しない
      }
      break
    case 'ArrowDown':
      // 下に移動
      if (rowIndex < totalRows - 1) {
        targetRowIndex = rowIndex + 1
        targetColIndex = colIndex
      } else {
        return // 最後の行なので移動しない
      }
      break
    case 'ArrowLeft':
      // 左に移動
      if (colIndex > 0) {
        targetRowIndex = rowIndex
        targetColIndex = colIndex - 1
      } else {
        return // 最初の列なので移動しない
      }
      break
    case 'ArrowRight':
      // 右に移動
      if (colIndex < 2) {
        targetRowIndex = rowIndex
        targetColIndex = colIndex + 1
      } else {
        return // 最後の列なので移動しない
      }
      break
    default:
      return // 他のキーは処理しない
  }

  // 移動先の入力框を取得
  await nextTick()
  if (targetColIndex === 0) {
    targetInput = confirmedBoxesInputs.value[targetRowIndex]
  } else if (targetColIndex === 1) {
    targetInput = confirmedUnitsInputs.value[targetRowIndex]
  } else if (targetColIndex === 2) {
    targetInput = forecastUnitsInputs.value[targetRowIndex]
  }

  if (targetInput) {
    event.preventDefault()
    targetInput.focus()
    targetInput.select()
  }
}

const props = defineProps<{
  visible: boolean
  monthlyOrderId: string
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'saved'): void
}>()

const orderDailyList = ref<OrderDaily[]>([])
const changedRows = ref<Set<number>>(new Set())
const loading = ref(false)
const saving = ref(false)

watch(
  () => props.monthlyOrderId,
  async (val) => {
    if (val) await loadDailyOrders()
    else orderDailyList.value = []
  },
  { immediate: true },
)

const loadDailyOrders = async () => {
  if (!props.monthlyOrderId) {
    orderDailyList.value = []
    return
  }
  loading.value = true
  try {
    const res = await fetchDailyOrdersByMonthlyOrderId(props.monthlyOrderId)
    console.log('APIレスポンス:', res)
    let list: OrderDaily[] = []
    if (res && res.list) {
      if (Array.isArray(res.list)) {
        list = res.list
      } else if (typeof res.list === 'object') {
        list = [res.list]
      }
    }
    // 最後の確定箱数が0より大きい日付のインデックスを検索
    let lastPositiveBoxIndex = -1
    for (let i = list.length - 1; i >= 0; i--) {
      if (list[i].confirmed_boxes > 0) {
        lastPositiveBoxIndex = i
        break
      }
    }
    // 最後の0より大きい日付から前へ、確定箱数が空または0以下の場合、確定本数を0に設定
    if (lastPositiveBoxIndex >= 0) {
      for (let i = lastPositiveBoxIndex; i >= 0; i--) {
        if (list[i].confirmed_boxes <= 0) {
          list[i].confirmed_units = 0
        }
      }
    }
    orderDailyList.value = list.slice().sort((a, b) => sortByDate(a.date, b.date))
    changedRows.value.clear()
  } catch (error) {
    console.error('まとめ編集データ取得失敗', error)
    orderDailyList.value = []
  } finally {
    loading.value = false
    await nextTick()
    // refは自動的に設定されるため、手動初期化は不要
  }
}

const markRowChanged = (row: OrderDaily) => {
  if (row.id) changedRows.value.add(Number(row.id))
}

const handleConfirmedBoxesChange = (row: OrderDaily) => {
  const unitPerBox = row.unit_per_box ?? 0
  if (unitPerBox > 0) {
    row.confirmed_units = row.confirmed_boxes * unitPerBox
  } else {
    // 入数が0の場合、確定箱数を確定本数として使用
    row.confirmed_units = row.confirmed_boxes
  }
  markRowChanged(row)
}

const handleBatchSave = async () => {
  if (saving.value) return
  if (changedRows.value.size === 0) {
    ElMessage.warning(t('orderDailyBatchEdit.msgNoChangedData'))
    return
  }

  saving.value = true
  try {
    const updates = orderDailyList.value
      .filter((row) => {
        const id = Number(row.id)
        return Number.isInteger(id) && id > 0 && changedRows.value.has(id)
      })
      .map((row) => ({
        id: Number(row.id),
        forecast_units: Number(row.forecast_units ?? 0),
        confirmed_boxes: Number(row.confirmed_boxes ?? 0),
        confirmed_units: Number(row.confirmed_units ?? 0),
        status: row.status ?? '未出荷',
        remarks: row.remarks ?? '',
      }))

    if (updates.length === 0) {
      ElMessage.warning(t('orderDailyBatchEdit.msgNoPayload'))
      return
    }
    console.log('✅ 送信する更新データ:', JSON.stringify(updates, null, 2))

    await batchUpdateDailyOrders({ list: updates })

    ElMessage.success(t('orderDailyBatchEdit.msgSaveSuccess'))
    changedRows.value.clear()
    emit('saved')
    emit('update:visible', false)
  } catch (error: unknown) {
    console.error('一括保存失敗', error)
    const errorMessage = error instanceof Error ? error.message : t('orderDailyBatchEdit.msgSaveFailed')
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const tableRowClassName = ({ row }: { row: OrderDaily }) => {
  return changedRows.value.has(row.id!) ? 'edited-row' : ''
}

interface SummaryMethodProps {
  columns: Array<{ property: string; label: string }>
  data: OrderDaily[]
}

const getSummaries = ({ columns, data }: SummaryMethodProps) => {
  const sums: string[] = []
  columns.forEach((column, index) => {
    if (index === 0) {
      sums[index] = t('orderDailyBatchEdit.sumText')
      return
    }

    if (['forecast_units', 'confirmed_boxes', 'confirmed_units'].includes(column.property)) {
      let sum = 0
      data.forEach((item) => {
        const value = Number(item[column.property as keyof OrderDaily]) || 0
        sum += value
      })
      sums[index] = sum > 0 ? sum.toLocaleString() : ''
    } else {
      sums[index] = ''
    }
  })
  return sums
}

const handleClose = () => {
  emit('update:visible', false)
}

// 内示本数更新処理
const handleUpdateForecastUnits = () => {
  if (saving.value || orderDailyList.value.length === 0) return

  let updatedCount = 0
  orderDailyList.value.forEach((row) => {
    const confirmedUnits = Number(row.confirmed_units ?? 0)
    if (confirmedUnits > 0) {
      row.forecast_units = confirmedUnits
      markRowChanged(row)
      updatedCount++
    }
  })

  if (updatedCount > 0) {
    ElMessage.success(t('orderDailyBatchEdit.msgForecastUpdated', { n: updatedCount }))
  } else {
    ElMessage.info(t('orderDailyBatchEdit.msgNoForecastTarget'))
  }
}

// 打印功能
const handlePrint = () => {
  if (orderDailyList.value.length === 0) {
    ElMessage.warning(t('orderDailyBatchEdit.msgNoPrintData'))
    return
  }

  const thDest = t('orderDailyBatchEdit.printColDestination')
  const thProductType = t('orderDailyBatchEdit.printColProductType')
  const thUnitPerBox = t('orderDailyBatchEdit.printColUnitPerBox')
  const thDate = t('orderDailyBatchEdit.printColDate')
  const thWeekday = t('orderDailyBatchEdit.printColWeekday')
  const thConfirmedBoxes = t('orderDailyBatchEdit.printColConfirmedBoxes')
  const thConfirmedUnits = t('orderDailyBatchEdit.printColConfirmedUnits')
  const thForecastUnits = t('orderDailyBatchEdit.printColForecastUnits')
  const thDiff = t('orderDailyBatchEdit.printColDiff')
  const thDeliveryDate = t('orderDailyBatchEdit.printColDeliveryDate')
  const printSumLabel = t('orderDailyBatchEdit.printSum')
  const printTitleStr = t('orderDailyBatchEdit.printTitle')
  const printHeadingStr = t('orderDailyBatchEdit.printHeading')
  const printDateLabelStr = t('orderDailyBatchEdit.printDateLabel')

  // 按製品名分组
  const groupedByProduct: Record<string, { name: string; orders: OrderDaily[] }> = {}
  
  orderDailyList.value.forEach((order) => {
    const productName = order.product_name || t('orderDailyBatchEdit.unset')
    if (!groupedByProduct[productName]) {
      groupedByProduct[productName] = {
        name: productName,
        orders: []
      }
    }
    groupedByProduct[productName].orders.push(order)
  })

  // 获取当前日期
  const japanDate = new Date(new Date().toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' }))
  const printDate = japanDate.toLocaleString('ja-JP', { 
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })

  // 构建打印HTML
  let printContent = ''
  
  // 按製品名排序
  const sortedProducts = Object.entries(groupedByProduct).sort((a, b) => 
    a[0].localeCompare(b[0], 'ja')
  )
  
  sortedProducts.forEach(([, data]) => {
    // 按日期排序（使用数据库 date 字段）
    const sortedOrders = [...data.orders].sort((a, b) => {
      const ta = a.date ? new Date(a.date).getTime() : 0
      const tb = b.date ? new Date(b.date).getTime() : 0
      return ta - tb
    })

    // 计算合计
    let totalConfirmedBoxes = 0
    let totalConfirmedUnits = 0
    let totalForecastUnits = 0
    let totalDifference = 0

    sortedOrders.forEach((order) => {
      const confirmedBoxes = Number(order.confirmed_boxes || 0)
      const confirmedUnits = Number(order.confirmed_units || 0)
      const forecastUnits = Number(order.forecast_units || 0)
      const difference = confirmedUnits - forecastUnits

      totalConfirmedBoxes += confirmedBoxes
      totalConfirmedUnits += confirmedUnits
      totalForecastUnits += forecastUnits
      totalDifference += difference
    })

    // 製品名标题
    printContent += `
      <div class="product-group">
        <div class="group-header">
          <h2>${data.name}</h2>
        </div>
        <table class="print-table">
          <thead>
            <tr>
              <th>${thDest}</th>
              <th>${thProductType}</th>
              <th>${thUnitPerBox}</th>
              <th>${thDate}</th>
              <th>${thWeekday}</th>
              <th>${thConfirmedBoxes}</th>
              <th>${thConfirmedUnits}</th>
              <th>${thForecastUnits}</th>
              <th>${thDiff}</th>
              <th>${thDeliveryDate}</th>
            </tr>
          </thead>
          <tbody>
    `

    sortedOrders.forEach((order) => {
      const confirmedUnits = Number(order.confirmed_units || 0)
      const forecastUnits = Number(order.forecast_units || 0)
      const difference = confirmedUnits - forecastUnits

      printContent += `
        <tr>
          <td>${order.destination_name || '-'}</td>
          <td>${order.product_type || '-'}</td>
          <td style="text-align: right;">${order.unit_per_box || 0}</td>
          <td style="text-align: center;">${formatDateOnly(order.date)}</td>
          <td style="text-align: center;">${order.weekday || '-'}</td>
          <td style="text-align: right;">${order.confirmed_boxes || 0}</td>
          <td style="text-align: right;">${order.confirmed_units || 0}</td>
          <td style="text-align: right;">${order.forecast_units || 0}</td>
          <td style="text-align: right;">${difference}</td>
          <td>${formatDate(order.delivery_date)}</td>
        </tr>
      `
    })

    // 合计行
    printContent += `
          </tbody>
          <tfoot>
            <tr class="summary-row">
              <td colspan="5" style="text-align: right; font-weight: bold;">${printSumLabel}</td>
              <td style="text-align: right; font-weight: bold;">${totalConfirmedBoxes}</td>
              <td style="text-align: right; font-weight: bold;">${totalConfirmedUnits}</td>
              <td style="text-align: right; font-weight: bold;">${totalForecastUnits}</td>
              <td style="text-align: right; font-weight: bold;">${totalDifference}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>
    `
  })

  // 打开打印窗口
  const printWindow = window.open('', '_blank', 'width=1000,height=800')
  if (!printWindow) {
    ElMessage.error(t('orderDailyBatchEdit.msgPrintWindowFailed'))
    return
  }

  // 打印样式
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>${printTitleStr}</title>
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        body {
          font-family: 'MS Gothic', 'Yu Gothic', 'Meiryo', sans-serif;
          padding: 30px;
          color: #333;
        }
        .print-header {
          text-align: center;
          margin-bottom: 30px;
          border-bottom: 2px solid #666;
          padding-bottom: 20px;
        }
        .print-header h1 {
          font-size: 24px;
          margin-bottom: 15px;
          color: #333;
        }
        .print-info {
          font-size: 14px;
          color: #666;
          margin-bottom: 10px;
        }
        .print-date {
          font-size: 14px;
          color: #666;
        }
        .product-group {
          margin-bottom: 40px;
          break-inside: avoid;
        }
        .group-header {
          margin-bottom: 20px;
          padding-bottom: 10px;
          border-bottom: 1px solid #ddd;
        }
        .group-header h2 {
          font-size: 18px;
          color: #333;
          margin: 0;
        }
        .print-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 20px;
          box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
        }
        .print-table th,
        .print-table td {
          border: 1px solid #dcdfe6;
          padding: 8px 12px;
          text-align: left;
          font-size: 12px;
        }
        .print-table th {
          background-color: #f5f7fa;
          color: #333;
          font-weight: 600;
          text-align: center;
        }
        .print-table tr:nth-child(even) {
          background-color: #fafafa;
        }
        .print-table tfoot .summary-row {
          background-color: #f5f7fa !important;
          border-top: 2px solid #666;
        }
        .print-table tfoot .summary-row td {
          font-weight: bold;
          background-color: #f5f7fa !important;
        }
        @media print {
          body {
            padding: 0;
          }
          .print-header {
            margin-bottom: 20px;
            padding-bottom: 15px;
          }
          .print-header h1 {
            font-size: 20px;
            margin-bottom: 10px;
          }
          .print-date {
            font-size: 12px;
          }
          .product-group {
            margin-bottom: 30px;
            page-break-inside: avoid;
          }
          .group-header h2 {
            font-size: 16px;
          }
          .print-table th,
          .print-table td {
            font-size: 11px;
            padding: 6px 4px;
          }
          .print-table th {
            background-color: #f5f7fa !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .print-table tfoot .summary-row {
            background-color: #f5f7fa !important;
            border-top: 2px solid #666;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .print-table tfoot .summary-row td {
            font-weight: bold;
            background-color: #f5f7fa !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
        }
      </style>
    </head>
    <body onload="window.print()">
      <div class="print-header">
        <h1>📄 ${printHeadingStr}</h1>
        <div class="print-date">${printDateLabelStr}: ${printDate}</div>
      </div>
      ${printContent}
    </body>
    </html>
  `

  printWindow.document.open()
  printWindow.document.write(html)
  printWindow.document.close()
  printWindow.focus()
}
</script>

<style scoped>
/* 现代精美UI - 紧凑布局 */
.japanese-minimalist {
  --el-dialog-padding-primary: 0;
}

.modern-daily-edit-dialog :deep(.el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.2);
}
.modern-daily-edit-dialog {
  max-width: 95vw;
  width: 80vw;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 56px rgba(0, 0, 0, 0.14), 0 0 0 1px rgba(0, 0, 0, 0.04);
  background: #fff;
  animation: dialogFadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes dialogFadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.96);
  }

  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modern-daily-edit-dialog :deep(.el-dialog__body) {
  padding: 6px 10px;
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
}

.modern-daily-edit-dialog :deep(.el-dialog__footer) {
  padding: 0;
  background-color: transparent;
  border-top: none;
  display: none;
}

/* ヘッダー - 玻璃质感 */
.dialog-header {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.95) 0%, rgba(139, 92, 246, 0.95) 100%);
  backdrop-filter: blur(12px);
  padding: 8px 14px;
  margin: 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 12px rgba(99, 102, 241, 0.2);
  position: relative;
  overflow: hidden;
}

.dialog-header::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, transparent 60%);
  pointer-events: none;
}

.dialog-header .header-content {
  min-height: 28px;
  position: relative;
  z-index: 1;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.title-section {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.save-summary-header {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
  padding: 3px 8px;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  color: #fff;
  font-size: 11px;
  white-space: nowrap;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.save-summary-header .summary-icon {
  color: #fde047;
  font-size: 12px;
}

.save-summary-header .summary-text {
  font-size: 11px;
  font-weight: 600;
}

.title-icon {
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(8px);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.25);
  transition: transform 0.2s;
}

.title-icon .el-icon {
  font-size: 16px;
  color: #fff;
}

.title-text {
  color: #fff;
}

.dialog-title {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  letter-spacing: 0.3px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
}

/* ヘッダーボタン - 颜色区分 */
.de-btn {
  height: 30px;
  font-size: 12px;
  font-weight: 600;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 0 12px;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  min-width: 0;
}
.de-btn .el-icon {
  font-size: 14px;
}
/* 印刷 - 灰/中性 */
.de-btn-print {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(8px);
}
.de-btn-print:hover:not(:disabled) {
  background: rgba(148, 163, 184, 0.9);
  color: #fff;
  border-color: rgba(148, 163, 184, 1);
  transform: translateY(-1px);
}
.de-btn-print:disabled {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.45);
  border-color: rgba(255, 255, 255, 0.15);
  cursor: not-allowed;
}
/* 内示本数更新 - 青绿/Teal */
.de-btn-forecast {
  background: rgba(20, 184, 166, 0.85);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.25);
  box-shadow: 0 2px 8px rgba(20, 184, 166, 0.3);
}
.de-btn-forecast:hover:not(:disabled) {
  background: rgba(13, 148, 136, 1);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(20, 184, 166, 0.4);
}
.de-btn-forecast:disabled {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.45);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: none;
  cursor: not-allowed;
}
/* 一括保存 - 绿色主操作 */
.de-btn-save {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
  border: none;
  box-shadow: 0 2px 10px rgba(16, 185, 129, 0.4);
  min-width: 96px;
}
.de-btn-save:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #fff;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.5);
}
.de-btn-save:disabled {
  background: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.5);
  box-shadow: none;
  cursor: not-allowed;
}
/* 关闭 - 描边，悬停红 */
.de-btn-close {
  width: 30px;
  padding: 0;
  min-width: 30px;
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.3);
}
.de-btn-close:hover {
  background: rgba(239, 68, 68, 0.9);
  color: #fff;
  border-color: rgba(239, 68, 68, 1);
  transform: translateY(-1px);
}

/* 情報エリア - 紧凑 */
.info-section {
  margin: 0;
  display: flex;
  gap: 5px;
  align-items: center;
  flex-wrap: wrap;
  flex: 1;
  justify-content: flex-end;
  min-width: 0;
}

.info-card,
.stat-card {
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(8px);
  border-radius: 6px;
  padding: 4px 8px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.info-card {
  flex-shrink: 0;
  min-width: 140px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-card:hover {
  background: rgba(255, 255, 255, 0.3);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.info-icon {
  width: 22px;
  height: 22px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 13px;
  flex-shrink: 0;
  transition: all 0.3s ease;
}

.info-card:hover .info-icon {
  background: rgba(255, 255, 255, 0.5);
  transform: rotate(10deg);
}

.info-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  white-space: nowrap;
}

.info-value {
  font-size: 12px;
  font-weight: 700;
  color: #ffffff;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  white-space: nowrap;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.stats-cards {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 5px;
  min-width: 72px;
  padding: 4px 8px;
  flex-shrink: 0;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.28);
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
  transform: translateY(-1px);
}

.stat-icon {
  width: 20px;
  height: 20px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 11px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.25);
}

.stat-icon.total {
  background: rgba(99, 102, 241, 0.3);
}

.stat-icon.changed {
  background: rgba(245, 158, 11, 0.3);
}

.stat-card:hover .stat-icon {
  transform: scale(1.15) rotate(5deg);
}

.stat-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 5px;
}

.stat-number {
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  line-height: 1;
  white-space: nowrap;
}

.stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
  margin: 0;
  white-space: nowrap;
}

/* テーブル幅保持・横スクロール用ラッパー */
.table-responsive {
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin-top: 4px;
}
.table-responsive .daily-edit-table {
  min-width: 863px; /* 列幅合計を維持 */
}

/* コンパクトテーブルスタイル - 现代精美风格 */
.daily-edit-table {
  border-radius: 8px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.daily-edit-table.compact-table {
  font-size: 11px;
}

/* 出荷日・納入日の色分け */
.daily-edit-table .cell-ship-date {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: #e3f2fd;
  color: #1565c0;
  font-weight: 500;
}
.daily-edit-table .cell-delivery-date {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: #e8f5e9;
  color: #2e7d32;
  font-weight: 500;
}

/* ヘッダースタイル */
.daily-edit-table :deep(.el-table__header) th {
  background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%);
  color: #1e293b;
  font-weight: 700;
  font-size: 11px;
  padding: 6px 4px;
  height: 32px;
  border-bottom: 2px solid #e2e8f0;
}

/* 行スタイル */
.daily-edit-table :deep(.el-table__row) {
  height: 32px;
  transition: all 0.2s ease;
}

.daily-edit-table :deep(.el-table__row:hover) {
  background-color: #f0f9ff !important;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.daily-edit-table :deep(.el-table__row:nth-child(even)) {
  background-color: #fafbfc;
}

.daily-edit-table :deep(.el-table__row.row-changed) {
  background: linear-gradient(to right, #fef3c7 0%, #fef9e7 100%) !important;
  border-left: 3px solid #f59e0b;
}

/* セルスタイル */
.daily-edit-table :deep(.el-table__cell) {
  padding: 2px 4px;
  border-bottom: 1px solid #f0f0f0;
}

/* 入力欄スタイル - 现代精美风格 */
.daily-edit-table :deep(.el-input__wrapper) {
  background-color: #ffffff;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  padding: 0 8px;
  min-height: 26px;
}

.daily-edit-table :deep(.el-input__wrapper:hover) {
  border-color: #667eea;
  box-shadow: 0 2px 4px rgba(102, 126, 234, 0.1);
}

.daily-edit-table :deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
  background: linear-gradient(to bottom, #ffffff 0%, #fafbff 100%);
}

.daily-edit-table :deep(.el-input__inner) {
  text-align: center;
  font-size: 12px;
  height: 26px;
  line-height: 26px;
  padding: 0;
  color: #1f2937;
  font-weight: 500;
}

.compact-input {
  width: 70px !important;
}

.compact-select {
  width: 85px !important;
}

/* セレクトボックススタイル */
.daily-edit-table :deep(.el-select .el-input__wrapper) {
  background-color: #ffffff;
}

/* 編集状態行スタイル */
.edited-row {
  background: #fefce8 !important;
}

.edited-row td:first-child {
  position: relative;
}

.edited-row td:first-child::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background-color: #facc15;
}

/* 合計行スタイル */
.daily-edit-table :deep(.el-table__footer) td {
  background: linear-gradient(to bottom, #f8fafc 0%, #f1f5f9 100%) !important;
  font-weight: 700 !important;
  font-size: 12px !important;
  color: #1e293b;
  padding: 6px 4px !important;
  height: 32px;
  border-top: 2px solid #cbd5e1 !important;
}

/* フッターエリアスタイル */
.footer-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.save-summary {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 3px;
  color: #b45309;
}

.summary-icon {
  color: #f59e0b;
  font-size: 12px;
}

.summary-text {
  font-size: 11px;
  font-weight: 500;
  color: #b45309;
}

.footer-buttons {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

/* ボタンスタイル - 日本简约风格 */
.cancel-btn,
.save-btn {
  min-width: 90px;
  height: 28px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 3px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid #d0d0d0;
  padding: 0 10px;
}

.cancel-btn {
  background: #ffffff;
  color: #4b5563;
}

.cancel-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.save-btn {
  background: #6b7280;
  border-color: #6b7280;
  color: white;
  box-shadow: none;
}

.save-btn:hover:not(:disabled) {
  background: #4b5563;
  border-color: #4b5563;
}

.save-btn:disabled {
  background: #e5e7eb;
  border-color: #e5e7eb;
  color: #9ca3af;
  box-shadow: none;
  cursor: not-allowed;
}

.save-btn .el-icon,
.cancel-btn .el-icon {
  font-size: 12px;
}

/* 保存中オーバーレイスタイル */
.global-saving-overlay {
  position: fixed;
  inset: 0;
  background: rgba(248, 250, 252, 0.6);
  backdrop-filter: blur(2px);
  z-index: 9999;
}

/* 空メッセージスタイル */
.empty-message {
  text-align: center;
  color: #999;
  padding: 16px 0;
  font-size: 11px;
}

/* レスポンシブ調整 - 现代精美响应式设计 */
@media (max-width: 1400px) {
  .modern-daily-edit-dialog {
    width: 90vw;
    max-width: 95vw;
  }
}

@media (max-width: 1200px) {
  .modern-daily-edit-dialog {
    width: 95vw;
    max-width: 98vw;
  }

  .modern-daily-edit-dialog :deep(.el-dialog__body) {
    padding: 6px 10px;
  }
}

@media (max-width: 900px) {
  .modern-daily-edit-dialog {
    width: 98vw;
    max-width: 100vw;
    border-radius: 8px;
  }

  .dialog-header {
    padding: 8px 12px;
  }

  .dialog-title {
    font-size: 14px;
  }

  .info-section,
  .stats-cards {
    gap: 4px;
  }

  .table-responsive .daily-edit-table {
    min-width: 863px;
  }
}

@media (max-width: 700px) {
  .modern-daily-edit-dialog {
    border-radius: 0;
  }

  .modern-daily-edit-dialog :deep(.el-dialog__body) {
    padding: 4px 8px;
  }

  .dialog-header {
    padding: 6px 10px;
  }

  .dialog-header .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }

  .header-actions {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .footer-section {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .footer-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    width: 100%;
  }

  .save-summary {
    justify-content: center;
  }

  .daily-edit-table :deep(.el-table__cell),
  .daily-edit-table :deep(.el-table__header th) {
    padding: 2px 3px;
    font-size: 10px;
  }

  .table-responsive .daily-edit-table {
    min-width: 863px;
  }
}

@media (max-width: 480px) {
  .info-section {
    flex-direction: column;
  }

  .stats-cards {
    flex-wrap: wrap;
    width: 100%;
  }

  .stat-card {
    flex: 1;
    min-width: 0;
  }
}
</style>
