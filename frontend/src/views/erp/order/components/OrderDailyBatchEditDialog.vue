<template>
  <el-dialog
    :model-value="props.visible"
    @update:modelValue="(val) => emit('update:visible', val)"
    width="75%"
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
              <h2 class="dialog-title">日別受注編集</h2>
            </div>
            <div class="save-summary-header" v-if="changedRows.size > 0">
              <el-icon class="summary-icon">
                <InfoFilled />
              </el-icon>
              <span class="summary-text">{{ changedRows.size }}件の変更があります</span>
            </div>
          </div>
          <!-- 情報カードエリア -->
          <div class="info-section">
            <div class="info-card">
              <div class="info-icon">
                <el-icon>
                  <Document />
                </el-icon>
              </div>
              <div class="info-content">
                <span class="info-label">月注文ID</span>
                <span class="info-value">{{ orderDailyList[0]?.monthly_order_id ?? '-' }}</span>
              </div>
            </div>

            <div class="stats-cards">
              <div class="stat-card">
                <div class="stat-icon total">
                  <el-icon>
                    <List />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-number">{{ orderDailyList.length }}</span>
                  <span class="stat-label">総件数</span>
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
                  <span class="stat-label">変更済み</span>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon confirmed">
                  <el-icon>
                    <Check />
                  </el-icon>
                </div>
                <div class="stat-content">
                  <span class="stat-number">
                    {{ orderDailyList.filter((row) => row.status === '出荷済').length }}
                  </span>
                  <span class="stat-label">出荷済み</span>
                </div>
              </div>
            </div>
          </div>
          <div class="header-actions">
            <el-button
              type="default"
              :disabled="saving || orderDailyList.length === 0"
              @click="handlePrint"
              class="print-btn-header"
            >
              <el-icon>
                <Printer />
              </el-icon>
              印刷
            </el-button>
            <el-button
              type="default"
              :disabled="saving || orderDailyList.length === 0"
              @click="handleUpdateForecastUnits"
              class="update-forecast-btn"
            >
              <el-icon>
                <Refresh />
              </el-icon>
              内示本数更新
            </el-button>
            <el-button
              type="primary"
              :loading="saving"
              @click="handleBatchSave"
              class="save-btn-header"
              :disabled="changedRows.size === 0"
            >
              <el-icon>
                <Check />
              </el-icon>
              一括保存
            </el-button>
            <el-button class="close-btn" @click="handleClose" text>
              <el-icon>
                <Close />
              </el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </template>

    <!-- Table -->
    <el-table
      v-loading="loading"
      :data="orderDailyList"
      border
      stripe
      show-summary
      :summary-method="getSummaries"
      sum-text="合計"
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
      <el-table-column label="納入先名" prop="destination_name" min-width="120" />
      <el-table-column label="製品名" prop="product_name" min-width="140" />
      <el-table-column label="製品タイプ" prop="product_type" width="100" align="center" />
      <el-table-column label="入数" prop="unit_per_box" width="55" align="center" />

      <el-table-column label="月" prop="month" width="45" align="center" />
      <el-table-column label="日" prop="day" width="40" align="center" />
      <el-table-column label="曜日" prop="weekday" width="50" align="center" />

      <!-- 確定箱数（編集） -->
      <el-table-column label="確定箱数" prop="confirmed_boxes" width="100" align="center">
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
      <el-table-column label="確定本数" prop="confirmed_units" width="100" align="center">
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
      <el-table-column label="内示本数" prop="forecast_units" width="100" align="center">
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
      <!-- 納入日 -->
      <el-table-column label="納入日" prop="delivery_date" width="85" align="center">
        <template #default="{ row }">
          <span>{{ formatDate(row.delivery_date) }}</span>
        </template>
      </el-table-column>
      <!-- 備考 -->
      <!-- <el-table-column label="備考" min-width="150">
        <template #default="{ row }">
          <el-input v-model="row.remarks" placeholder="備考" :disabled="saving" @input="markRowChanged(row)" />
        </template>
      </el-table-column> -->
    </el-table>
    <div v-if="!loading && orderDailyList.length === 0" class="empty-message">
      データがありません
    </div>
    <div v-if="!loading && !props.monthlyOrderId" class="empty-message">
      月注文IDが指定されていません
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
import { fetchDailyOrdersByMonthlyOrderId, batchUpdateDailyOrders } from '@/api/order/order'
import { ElMessage } from 'element-plus'
import { Edit, Close, Document, List, Check, InfoFilled, Refresh, Printer } from '@element-plus/icons-vue'
import type { OrderDaily } from '@/types/order'

// 日付フォーマット関数
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-'
  try {
    const date = new Date(dateString)
    return `${date.getMonth() + 1}/${date.getDate()}`
  } catch (e) {
    return dateString.toString()
  }
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
    orderDailyList.value = list
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
    ElMessage.warning('変更されたデータがありません')
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
      ElMessage.warning('送信データがありません')
      return
    }
    console.log('✅ 送信する更新データ:', JSON.stringify(updates, null, 2))

    await batchUpdateDailyOrders({ list: updates })

    ElMessage.success('一括保存成功しました！')
    changedRows.value.clear()
    emit('saved')
    emit('update:visible', false)
  } catch (error: unknown) {
    console.error('一括保存失敗', error)
    const errorMessage = error instanceof Error ? error.message : '保存に失敗しました'
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
      sums[index] = '合計'
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
    ElMessage.success(`${updatedCount}件の内示本数を更新しました`)
  } else {
    ElMessage.info('更新対象のデータがありません（確定本数が0より大きい行がありません）')
  }
}

// 打印功能
const handlePrint = () => {
  if (orderDailyList.value.length === 0) {
    ElMessage.warning('印刷するデータがありません')
    return
  }

  // 按製品名分组
  const groupedByProduct: Record<string, { name: string; orders: OrderDaily[] }> = {}
  
  orderDailyList.value.forEach((order) => {
    const productName = order.product_name || '未設定'
    if (!groupedByProduct[productName]) {
      groupedByProduct[productName] = {
        name: productName,
        orders: []
      }
    }
    groupedByProduct[productName].orders.push(order)
  })

  // 获取月注文ID
  const monthlyOrderId = orderDailyList.value[0]?.monthly_order_id || '-'
  
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
  
  sortedProducts.forEach(([productName, data]) => {
    // 按日期排序
    const sortedOrders = [...data.orders].sort((a, b) => {
      if (a.year !== b.year) return a.year - b.year
      if (a.month !== b.month) return a.month - b.month
      if (a.day !== b.day) return a.day - b.day
      return 0
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
              <th>納入先</th>
              <th>製品タイプ</th>
              <th>入数</th>
              <th>月</th>
              <th>日</th>
              <th>曜日</th>
              <th>確定箱数</th>
              <th>確定本数</th>
              <th>内示本数</th>
              <th>差異</th>
              <th>納入日</th>
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
          <td style="text-align: center;">${order.month || '-'}</td>
          <td style="text-align: center;">${order.day || '-'}</td>
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
              <td colspan="6" style="text-align: right; font-weight: bold;">合計</td>
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
    ElMessage.error('印刷ウィンドウを開けません')
    return
  }

  // 打印样式
  const html = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <title>日別受注編集 - 印刷</title>
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
        <h1>📄 日別受注編集（印刷用）</h1>
        <div class="print-info">月注文ID: ${monthlyOrderId}</div>
        <div class="print-date">印刷日時: ${printDate}</div>
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
/* 日本简约风格对话框 */
.japanese-minimalist {
  --el-dialog-padding-primary: 6px;
}

.modern-daily-edit-dialog {
  max-width: 90vw;
  width: 75vw;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  background-color: #ffffff;
  border: 1px solid #e0e0e0;
  animation: dialogFadeIn 0.3s ease-out;
}

@keyframes dialogFadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modern-daily-edit-dialog :deep(.el-dialog__body) {
  padding: 3px 10px;
  background-color: #ffffff;
}

.modern-daily-edit-dialog :deep(.el-dialog__footer) {
  padding: 3px 10px;
  background-color: #fafafa;
  border-top: 1px solid #e0e0e0;
}

/* ヘッダースタイル - 日本简约风格 */
.dialog-header {
  background: linear-gradient(180deg, #fafafa 0%, #f5f5f5 100%);
  padding: 6px 10px;
  margin: 0;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}

.dialog-header .header-content {
  min-height: 36px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
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
  padding: 2px 6px;
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1px solid #fde68a;
  border-radius: 3px;
  color: #b45309;
  font-size: 10px;
  white-space: nowrap;
  animation: pulse 2s ease-in-out infinite;
  box-shadow: 0 1px 2px rgba(180, 83, 9, 0.1);
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.9;
  }
}

.save-summary-header .summary-icon {
  color: #f59e0b;
  font-size: 11px;
}

.save-summary-header .summary-text {
  font-size: 10px;
  font-weight: 500;
}

.title-icon {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.title-icon:hover {
  background: linear-gradient(135deg, #c7d2fe 0%, #a5b4fc 100%);
  transform: scale(1.05);
}

.title-icon .el-icon {
  font-size: 16px;
  color: #555555;
}

.title-text {
  color: #1f2937;
}

.dialog-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 0.3px;
}

.close-btn {
  width: 24px;
  height: 24px;
  border-radius: 3px;
  background: transparent;
  color: #666666;
  transition: all 0.2s ease;
  padding: 0;
}

.close-btn:hover {
  background: #fee2e2;
  color: #dc2626;
  transform: rotate(90deg);
}

/* ヘッダー内の保存ボタンスタイル */
.save-btn-header {
  min-width: 90px;
  height: 28px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 3px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid #d0d0d0;
  padding: 0 10px;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border-color: #4f46e5;
  color: white;
  box-shadow: 0 2px 4px rgba(79, 70, 229, 0.2);
}

.save-btn-header:hover:not(:disabled) {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  border-color: #4338ca;
  box-shadow: 0 4px 8px rgba(79, 70, 229, 0.3);
  transform: translateY(-1px);
}

.save-btn-header:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(79, 70, 229, 0.2);
}

.save-btn-header:disabled {
  background: #e5e7eb;
  border-color: #e5e7eb;
  color: #9ca3af;
  box-shadow: none;
  cursor: not-allowed;
}

.save-btn-header .el-icon {
  font-size: 12px;
}

/* 印刷ボタンスタイル */
.print-btn-header {
  min-width: 80px;
  height: 28px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 3px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid #d0d0d0;
  padding: 0 10px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-color: #059669;
  color: white;
  box-shadow: 0 2px 4px rgba(5, 150, 105, 0.2);
}

.print-btn-header:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  border-color: #047857;
  box-shadow: 0 4px 8px rgba(5, 150, 105, 0.3);
  transform: translateY(-1px);
}

.print-btn-header:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(5, 150, 105, 0.2);
}

.print-btn-header:disabled {
  background: #e5e7eb;
  border-color: #e5e7eb;
  color: #9ca3af;
  box-shadow: none;
  cursor: not-allowed;
}

.print-btn-header .el-icon {
  font-size: 12px;
}

/* 内示本数更新ボタンスタイル */
.update-forecast-btn {
  min-width: 110px;
  height: 28px;
  font-size: 11px;
  font-weight: 600;
  border-radius: 3px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid #d0d0d0;
  padding: 0 10px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-color: #d97706;
  color: white;
  box-shadow: 0 2px 4px rgba(217, 119, 6, 0.2);
}

.update-forecast-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
  border-color: #b45309;
  box-shadow: 0 4px 8px rgba(217, 119, 6, 0.3);
  transform: translateY(-1px);
}

.update-forecast-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(217, 119, 6, 0.2);
}

.update-forecast-btn:disabled {
  background: #e5e7eb;
  border-color: #e5e7eb;
  color: #9ca3af;
  box-shadow: none;
  cursor: not-allowed;
}

.update-forecast-btn .el-icon {
  font-size: 12px;
}

/* 情報エリアスタイル - コンパクト（ヘッダー内） */
.info-section {
  margin: 0;
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
  flex: 1;
  justify-content: flex-end;
  min-width: 0;
}

.info-card,
.stat-card {
  background: #ffffff;
  border-radius: 3px;
  padding: 4px 8px;
  border: 1px solid #e0e0e0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.info-card {
  flex-shrink: 0;
  min-width: 140px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.info-icon {
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #4a5568;
  font-size: 12px;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.info-card:hover .info-icon {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  color: #4f46e5;
}

.info-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-label {
  font-size: 10px;
  color: #666666;
  font-weight: 500;
  white-space: nowrap;
}

.info-value {
  font-size: 11px;
  font-weight: 600;
  color: #1f2937;
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  white-space: nowrap;
}

.stats-cards {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 70px;
  padding: 4px 6px;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.stat-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.stat-icon {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.stat-icon.total {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
}

.stat-icon.changed {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.stat-icon.confirmed {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.stat-card:hover .stat-icon {
  transform: scale(1.1);
}

.stat-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-number {
  font-size: 12px;
  font-weight: 700;
  color: #1f2937;
  line-height: 1;
  white-space: nowrap;
}

.stat-label {
  font-size: 9px;
  color: #666666;
  font-weight: 400;
  margin: 0;
  white-space: nowrap;
}

/* コンパクトテーブルスタイル - 日本简约风格 */
.daily-edit-table {
  border-radius: 4px;
  overflow: hidden;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  margin-top: 4px;
}

.daily-edit-table.compact-table {
  font-size: 11px;
}

/* ヘッダースタイル */
.daily-edit-table :deep(.el-table__header) th {
  background-color: #f5f5f5;
  color: #374151;
  font-weight: 600;
  font-size: 11px;
  padding: 4px 4px;
  height: 28px;
  border-bottom: 1px solid #e0e0e0;
}

/* 行スタイル */
.daily-edit-table :deep(.el-table__row) {
  height: 28px;
  transition: all 0.2s ease;
}

.daily-edit-table :deep(.el-table__row:hover) {
  background-color: #f0f9ff !important;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.1);
}

.daily-edit-table :deep(.el-table__row:nth-child(even)) {
  background-color: #fafafa;
}

.daily-edit-table :deep(.el-table__row.row-changed) {
  background-color: #fffbeb !important;
  border-left: 2px solid #f59e0b;
}

/* セルスタイル */
.daily-edit-table :deep(.el-table__cell) {
  padding: 2px 4px;
  border-bottom: 1px solid #f0f0f0;
}

/* 入力欄スタイル */
.daily-edit-table :deep(.el-input__wrapper) {
  background-color: #ffffff;
  border: 1px solid #d0d0d0;
  border-radius: 3px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: none;
  padding: 0 6px;
  min-height: 22px;
}

.daily-edit-table :deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.1);
}

.daily-edit-table :deep(.el-input__wrapper.is-focus) {
  border-color: #4f46e5;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.15);
  background-color: #fafbff;
}

.daily-edit-table :deep(.el-input__inner) {
  text-align: center;
  font-size: 11px;
  height: 22px;
  line-height: 22px;
  padding: 0;
  color: #333333;
  font-weight: 400;
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
  background-color: #f5f5f5 !important;
  font-weight: 700 !important;
  font-size: 11px !important;
  color: #1f2937;
  padding: 4px 4px !important;
  height: 28px;
  border-top: 1px solid #e0e0e0 !important;
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

/* レスポンシブ調整 */
@media (max-width: 900px) {
  .modern-daily-edit-dialog {
    width: 98vw;
    max-width: 100vw;
    border-radius: 0;
  }

  .dialog-header {
    padding: 4px 8px;
  }

  .dialog-title {
    font-size: 13px;
  }

  .info-section,
  .stats-cards {
    gap: 4px;
  }
}

@media (max-width: 700px) {
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
}
</style>
