<template>
  <el-dialog
    v-model="visible"
    :title="`出荷番号詳細：${shippingItems.length > 0 ? shippingItems[0].shipping_no : ''}`"
    width="90%"
    @close="handleClose"
    destroy-on-close
    :close-on-click-modal="false"
    top="5vh"
    class="shipping-detail-dialog"
  >
    <div v-loading="loading" element-loading-text="データを読み込み中...">
      <!-- 出荷基本情報 -->
      <el-card class="shipping-summary-card" shadow="never" v-if="shippingItems.length > 0">
        <template #header>
          <div class="summary-header">
            <el-icon class="summary-icon"><Van /></el-icon>
            <span class="summary-title">出荷情報</span>
          </div>
        </template>
        <el-descriptions :column="4" border class="shipping-summary">
          <el-descriptions-item label="出荷番号" :span="2">
            <div class="shipping-no-edit-container">
              <div class="shipping-no-display">
                <span class="shipping-no-prefix">{{ shippingNoPrefix }}</span>
                <div class="shipping-no-suffix-edit">
                  <el-input-number
                    v-if="editingShippingNo"
                    v-model="editableShippingNoSuffix"
                    :min="1"
                    :max="99"
                    :precision="0"
                    controls-position="right"
                    size="small"
                    class="suffix-input"
                    @blur="saveShippingNoChange"
                    @keyup.enter="saveShippingNoChange"
                  />
                  <el-tag
                    v-else
                    type="primary"
                    effect="light"
                    class="shipping-no-suffix-tag"
                    @click="startEditShippingNo"
                  >
                    {{ shippingNoSuffix }}
                  </el-tag>
                </div>
              </div>
              <el-button
                v-if="!editingShippingNo && isEditable"
                size="small"
                link
                @click="startEditShippingNo"
                class="edit-suffix-btn"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="状態" :span="1">
            <el-tag :type="statusColor(shippingItems[0].status)" effect="dark">
              {{ shippingItems[0].status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="製品件数" :span="1">
            <el-tag type="info" effect="light">{{ shippingItems.length }}件</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="出荷日" :span="1">
            <span>{{ formatDate(shippingItems[0].shipping_date) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="納入日" :span="1">
            <span>{{ formatDate(shippingItems[0].delivery_date || '') }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="納入先" :span="1">
            <span
              >{{ shippingItems[0].destination_cd }} - {{ shippingItems[0].destination_name }}</span
            >
          </el-descriptions-item>
          <el-descriptions-item label="合計数量" :span="1">
            <el-tag type="success" effect="light">{{ totalUnits.toLocaleString() }}本</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 製品一覧表 -->
      <el-card class="products-table-card" shadow="never">
        <template #header>
          <div class="table-header">
            <el-icon class="table-icon"><List /></el-icon>
            <span class="table-title">製品一覧</span>
            <div class="header-actions">
              <el-button
                v-if="isEditable"
                type="primary"
                size="small"
                @click="enableBatchEdit"
                :disabled="batchEditMode"
              >
                <el-icon><Edit /></el-icon>
                一括編集
              </el-button>
              <el-button
                v-if="batchEditMode"
                type="success"
                size="small"
                @click="saveBatchEdit"
                :loading="saveLoading"
              >
                <el-icon><Check /></el-icon>
                保存
              </el-button>
              <el-button v-if="batchEditMode" size="small" @click="cancelBatchEdit">
                <el-icon><Close /></el-icon>
                キャンセル
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          :data="shippingItems"
          border
          stripe
          class="products-table"
          :row-class-name="getRowClassName"
        >
          <el-table-column label="コード" width="160" align="center">
            <template #default="{ row }">
              <el-tag type="primary" effect="light" class="code-tag">
                {{ row.shipping_no }}_{{ row.product_cd }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="製品CD" prop="product_cd" width="100" align="center">
            <template #default="{ row }">
              <el-tag size="small" effect="plain">{{ row.product_cd }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="製品名" prop="product_name" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">
              <el-input v-if="batchEditMode" v-model="row.product_name" size="small" />
              <span v-else>{{ row.product_name }}</span>
            </template>
          </el-table-column>

          <el-table-column label="箱タイプ" prop="box_type" width="100" align="center">
            <template #default="{ row }">
              <el-select
                v-if="batchEditMode"
                v-model="row.box_type"
                size="small"
                style="width: 100%"
              >
                <el-option label="小箱" value="小箱" />
                <el-option label="大箱" value="大箱" />
                <el-option label="TP箱" value="TP箱" />
                <el-option label="特殊" value="特殊" />
              </el-select>
              <el-tag v-else size="small" :type="getBoxTypeTagType(row.box_type)" effect="dark">
                {{ row.box_type || '未設定' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="箱数" prop="confirmed_boxes" width="100" align="right">
            <template #default="{ row }">
              <el-input-number
                v-if="batchEditMode"
                v-model="row.confirmed_boxes"
                :min="0"
                size="small"
                style="width: 100%"
              />
              <div v-else class="number-cell">
                <span class="number-value">{{ (row.confirmed_boxes || 0).toLocaleString() }}</span>
                <span class="number-unit">箱</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="数量（本）" prop="confirmed_units" width="120" align="right">
            <template #default="{ row }">
              <el-input-number
                v-if="batchEditMode"
                v-model="row.confirmed_units"
                :min="1"
                size="small"
                style="width: 100%"
              />
              <div v-else class="number-cell">
                <span class="number-value">{{ (row.confirmed_units || 0).toLocaleString() }}</span>
                <span class="number-unit">本</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="備考" prop="remarks" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">
              <el-input
                v-if="batchEditMode"
                v-model="row.remarks"
                type="textarea"
                :rows="1"
                size="small"
              />
              <span v-else>{{ row.remarks || '-' }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 合計行 -->
        <div class="table-summary">
          <el-row :gutter="20" class="summary-row">
            <el-col :span="12">
              <div class="summary-item">
                <span class="summary-label">合計箱数：</span>
                <span class="summary-value">{{ totalBoxes.toLocaleString() }}箱</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="summary-item">
                <span class="summary-label">合計数量：</span>
                <span class="summary-value">{{ totalUnits.toLocaleString() }}本</span>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose" size="default">
          <el-icon><Close /></el-icon>
          閉じる
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Van, List, Edit, Check, Close } from '@element-plus/icons-vue'

const props = defineProps({
  shippingItem: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['close', 'refresh'])

const visible = ref(true)
const loading = ref(false)
const saveLoading = ref(false)
const batchEditMode = ref(false)
// 定义接口
interface ShippingItem {
  id: number
  shipping_no: string
  shipping_date: string
  delivery_date: string | null
  destination_cd: string
  destination_name: string
  product_cd: string
  product_name: string
  product_alias: string | null
  box_type: string | null
  confirmed_boxes: number
  confirmed_units: number
  unit: string
  status: string
  remarks: string | null
  created_at: string
  updated_at: string
  [key: string]: unknown
}

const shippingItems = ref<ShippingItem[]>([])
const originalShippingItems = ref<ShippingItem[]>([])
const editingShippingNo = ref(false)
const editableShippingNoSuffix = ref(1)
const originalShippingNo = ref('')

const isEditable = computed(() => {
  if (shippingItems.value.length === 0) return false
  // 未発行または発行済状態のみ編集可能
  return ['未発行', '発行済'].includes(shippingItems.value[0].status)
})

const totalBoxes = computed(() => {
  return shippingItems.value.reduce((sum, item) => sum + (item.confirmed_boxes || 0), 0)
})

const totalUnits = computed(() => {
  return shippingItems.value.reduce((sum, item) => sum + (item.confirmed_units || 0), 0)
})

const shippingNoPrefix = computed(() => {
  if (shippingItems.value.length === 0) return ''
  const shippingNo = shippingItems.value[0].shipping_no
  return shippingNo.slice(0, -2) // 前面部分（除了最后两位）
})

const shippingNoSuffix = computed(() => {
  if (shippingItems.value.length === 0) return '01'
  const shippingNo = shippingItems.value[0].shipping_no
  return shippingNo.slice(-2) // 最后两位
})

function statusColor(status: string): 'info' | 'success' | 'warning' | 'danger' {
  switch (status) {
    case '未発行':
      return 'info'
    case '発行済':
      return 'success'
    case '出荷済':
      return 'warning'
    case 'キャンセル':
      return 'danger'
    default:
      return 'info'
  }
}

function getBoxTypeTagType(boxType: string): 'success' | 'primary' | 'warning' | 'danger' | 'info' {
  switch (boxType) {
    case '小箱':
      return 'success'
    case '大箱':
      return 'primary'
    case 'TP箱':
      return 'warning'
    case '特殊':
      return 'danger'
    default:
      return 'info'
  }
}

function getRowClassName(_payload: { row: ShippingItem; rowIndex: number }) {
  return batchEditMode.value ? 'editable-row' : ''
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '未設定'
  try {
    // 使用日本标准时间格式化日期
    const date = new Date(dateStr + 'T00:00:00+09:00') // 确保使用JST时区
    return date
      .toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        timeZone: 'Asia/Tokyo',
      })
      .replace(/\//g, '-')
  } catch (e) {
    return dateStr
  }
}

watch(
  () => props.shippingItem,
  (newVal) => {
    if (!newVal?.shipping_no) return
    fetchShippingDetails(newVal.shipping_no)
  },
  { immediate: true },
)

async function fetchShippingDetails(shippingNo: string) {
  loading.value = true
  try {
    // 获取同一出荷番号的所有製品
    const res = await request.get(`/api/shipping/${shippingNo}/items`)
    if (res && Array.isArray(res)) {
      shippingItems.value = [...res]
      originalShippingItems.value = JSON.parse(JSON.stringify(res)) // 深拷贝保存原始数据
      originalShippingNo.value = shippingNo
      // 初始化编辑用的后缀数字
      editableShippingNoSuffix.value = parseInt(shippingNo.slice(-2)) || 1
    } else {
      ElMessage.error('出荷詳細の取得に失敗しました')
    }
  } catch (error) {
    console.error('出荷詳細取得エラー:', error)
    ElMessage.error('出荷詳細の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

function enableBatchEdit() {
  batchEditMode.value = true
  // 保存当前数据用于取消时恢复
  originalShippingItems.value = JSON.parse(JSON.stringify(shippingItems.value))
}

function cancelBatchEdit() {
  batchEditMode.value = false
  // 恢复原始数据
  shippingItems.value = JSON.parse(JSON.stringify(originalShippingItems.value))
}

async function saveBatchEdit() {
  // 验证数据
  const invalidItems = shippingItems.value.filter(
    (item) => !item.confirmed_units || item.confirmed_units <= 0,
  )

  if (invalidItems.length > 0) {
    ElMessage.warning('数量が0以下の製品があります。正しい数量を入力してください')
    return
  }

  try {
    // 显示详细的更新确认对话框
    const confirmMessage = `
      <div style="text-align: left;">
        <p><strong>以下の更新を実行します：</strong></p>
        <ul style="margin: 10px 0; padding-left: 20px;">
          <li>製品情報の更新: ${shippingItems.value.length}件</li>
          <li>関連するピッキングタスクの更新</li>
          <li>関連するピッキングリストの更新</li>
        </ul>
        <p style="color: #E6A23C; margin-top: 15px;">
          <i class="el-icon-warning"></i>
          この操作は複数のテーブルに影響します。続行しますか？
        </p>
      </div>
    `

    await ElMessageBox.confirm(confirmMessage, '確認', {
      confirmButtonText: '更新実行',
      cancelButtonText: 'キャンセル',
      type: 'warning',
      dangerouslyUseHTMLString: true,
      customClass: 'enhanced-confirm-dialog',
    })

    saveLoading.value = true

    // 使用增强的API端点
    const response = await request.put(`/api/shipping/${originalShippingNo.value}/enhanced`, {
      shipping_no: originalShippingNo.value,
      shipping_date: shippingItems.value[0].shipping_date,
      delivery_date: shippingItems.value[0].delivery_date,
      destination_cd: shippingItems.value[0].destination_cd,
      destination_name: shippingItems.value[0].destination_name,
      items: shippingItems.value.map((item) => ({
        id: item.id,
        product_cd: item.product_cd,
        product_name: item.product_name,
        confirmed_units: item.confirmed_units,
        confirmed_boxes: item.confirmed_boxes,
        box_type: item.box_type,
        remarks: item.remarks,
      })),
      shipping_no_changed: false, // 批量编辑不改变出荷番号
    })

    // 显示详细的成功消息
    const successData = response.data
    if (successData.data && successData.data.update_stats) {
      const stats = successData.data.update_stats
      ElMessage.success({
        message: `更新完了: 製品情報(${stats.shipping_items}件)`,
        duration: 3000,
      })
    } else {
      ElMessage.success('出荷情報を一括更新しました')
    }

    batchEditMode.value = false
    emit('refresh')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('一括保存エラー:', error)
      ElMessage.error('一括保存に失敗しました: ' + (error.response?.data?.message || error.message))
    }
  } finally {
    saveLoading.value = false
  }
}

function startEditShippingNo() {
  if (!isEditable.value) return
  editingShippingNo.value = true
  editableShippingNoSuffix.value = parseInt(shippingNoSuffix.value) || 1
}

async function saveShippingNoChange() {
  if (!editingShippingNo.value) return

  try {
    // 基本验证
    if (editableShippingNoSuffix.value < 1 || editableShippingNoSuffix.value > 99) {
      ElMessage.warning('出荷番号の後2桁は01-99の範囲で入力してください')
      editableShippingNoSuffix.value = parseInt(shippingNoSuffix.value) || 1
      editingShippingNo.value = false
      return
    }

    const newSuffix = String(editableShippingNoSuffix.value).padStart(2, '0')
    const newShippingNo = shippingNoPrefix.value + newSuffix

    // 如果没有变化，直接退出编辑模式
    if (newShippingNo === originalShippingNo.value) {
      editingShippingNo.value = false
      return
    }

    // 使用新的验证API
    const validationResponse = await request.post('/api/shipping/validate-shipping-no-change', {
      old_shipping_no: originalShippingNo.value,
      new_shipping_no: newShippingNo,
    })

    const validationData = validationResponse.data
    if (!validationData.success) {
      ElMessage.warning(validationData.message)
      editableShippingNoSuffix.value = parseInt(shippingNoSuffix.value) || 1
      editingShippingNo.value = false
      return
    }

    if (!validationData.data.is_valid) {
      ElMessage.warning('指定された出荷番号は使用できません')
      editableShippingNoSuffix.value = parseInt(shippingNoSuffix.value) || 1
      editingShippingNo.value = false
      return
    }

    // 显示详细的影响范围确认
    const affectedTables = validationData.data.affected_tables
    const confirmMessage = `
      <div style="text-align: left;">
        <p><strong>出荷番号を変更します：</strong></p>
        <p style="margin: 10px 0;">
          <span style="color: #F56C6C;">${originalShippingNo.value}</span>
          →
          <span style="color: #67C23A;">${newShippingNo}</span>
        </p>
        <p><strong>影響するテーブル：</strong></p>
        <ul style="margin: 10px 0; padding-left: 20px;">
          <li>出荷アイテム: ${shippingItems.value.length}件</li>
          <li>ピッキングタスク: ${affectedTables.picking_tasks_count}件</li>
          <li>ピッキングリスト: ${affectedTables.picking_list_count}件</li>
          <li>出荷記録: ${affectedTables.shipping_records_count}件</li>
          <li>日次オーダー: ${affectedTables.order_daily_count}件</li>
        </ul>
        <p style="color: #E6A23C; margin-top: 15px;">
          <i class="el-icon-warning"></i>
          この操作は複数のテーブルの出荷番号を一括更新します。続行しますか？
        </p>
      </div>
    `

    await ElMessageBox.confirm(confirmMessage, '出荷番号変更確認', {
      confirmButtonText: '変更実行',
      cancelButtonText: 'キャンセル',
      type: 'warning',
      dangerouslyUseHTMLString: true,
      customClass: 'enhanced-confirm-dialog',
    })

    saveLoading.value = true

    // 使用增强的更新API
    const response = await request.put(`/api/shipping/${originalShippingNo.value}/enhanced`, {
      shipping_no: newShippingNo,
      shipping_date: shippingItems.value[0].shipping_date,
      delivery_date: shippingItems.value[0].delivery_date,
      destination_cd: shippingItems.value[0].destination_cd,
      destination_name: shippingItems.value[0].destination_name,
      product_cd: shippingItems.value[0].product_cd,
      product_name: shippingItems.value[0].product_name,
      confirmed_units: shippingItems.value[0].confirmed_units,
      confirmed_boxes: shippingItems.value[0].confirmed_boxes,
      box_type: shippingItems.value[0].box_type,
      remarks: shippingItems.value[0].remarks,
      shipping_no_changed: true,
    })

    // 显示详细的成功消息
    const successData = response.data
    if (successData.data && successData.data.update_stats) {
      const stats = successData.data.update_stats
      ElMessage.success({
        message: `出荷番号更新完了: shipping_items(${stats.shipping_items}), picking_tasks(${stats.picking_tasks}), picking_list(${stats.picking_list}), shipping_records(${stats.shipping_records}), order_daily(${stats.order_daily})`,
        duration: 5000,
      })
    } else {
      ElMessage.success('出荷番号を更新しました')
    }

    originalShippingNo.value = newShippingNo
    editingShippingNo.value = false

    // 重新获取数据
    await fetchShippingDetails(newShippingNo)
    emit('refresh')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('出荷番号更新エラー:', error)
      ElMessage.error(
        '出荷番号の更新に失敗しました: ' + (error.response?.data?.message || error.message),
      )
    }
    editableShippingNoSuffix.value = parseInt(shippingNoSuffix.value) || 1
    editingShippingNo.value = false
  } finally {
    saveLoading.value = false
  }
}

function handleClose() {
  if (batchEditMode.value || editingShippingNo.value) {
    ElMessageBox.confirm('編集中のデータがあります。保存せずに閉じますか？', '確認', {
      confirmButtonText: '閉じる',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })
      .then(() => {
        visible.value = false
        emit('close')
      })
      .catch(() => {
        // ユーザーがキャンセルした場合は何もしない
      })
  } else {
    visible.value = false
    emit('close')
  }
}
</script>

<style scoped>
/* 添加增强确认对话框的样式 */
:deep(.enhanced-confirm-dialog) {
  .el-message-box__content {
    text-align: left;
  }

  .el-message-box__message {
    margin: 0;
  }

  ul {
    color: #606266;
    font-size: 14px;
  }

  li {
    margin: 5px 0;
  }
}

/* 编辑模式的视觉增强 */
.products-table {
  :deep(.el-table__row.editing-row) {
    background-color: #f0f9ff;
  }

  :deep(.el-input-number) {
    width: 100%;
  }

  :deep(.el-select) {
    width: 100%;
  }
}

/* 保存按钮的加载状态 */
.header-actions {
  .el-button.is-loading {
    pointer-events: none;
  }
}

.shipping-detail-dialog {
  .shipping-summary-card {
    margin-bottom: 20px;
    border: 1px solid #e4e7ed;
    border-radius: 8px;

    .summary-header {
      display: flex;
      align-items: center;
      gap: 8px;

      .summary-icon {
        color: #409eff;
        font-size: 18px;
      }

      .summary-title {
        font-weight: 600;
        color: #303133;
      }
    }

    .shipping-summary {
      .shipping-no-edit-container {
        display: flex;
        align-items: center;
        gap: 8px;

        .shipping-no-display {
          display: flex;
          align-items: center;
          gap: 2px;

          .shipping-no-prefix {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
            color: #409eff;
          }

          .shipping-no-suffix-edit {
            .suffix-input {
              width: 80px;

              :deep(.el-input__inner) {
                font-family: 'Courier New', monospace;
                font-weight: 600;
                text-align: center;
                padding: 0 8px;
              }
            }

            .shipping-no-suffix-tag {
              font-family: 'Courier New', monospace;
              font-size: 14px;
              font-weight: 600;
              letter-spacing: 0.5px;
              cursor: pointer;
              transition: all 0.3s ease;

              &:hover {
                background-color: #ecf5ff;
                border-color: #b3d8ff;
                transform: scale(1.05);
              }
            }
          }
        }

        .edit-suffix-btn {
          color: #409eff;
          padding: 4px;

          &:hover {
            background-color: #ecf5ff;
          }
        }
      }
    }
  }

  .products-table-card {
    border: 1px solid #e4e7ed;
    border-radius: 8px;

    .table-header {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .table-icon {
        color: #67c23a;
        font-size: 18px;
        margin-right: 8px;
      }

      .table-title {
        font-weight: 600;
        color: #303133;
        flex: 1;
      }

      .header-actions {
        display: flex;
        gap: 8px;
      }
    }

    .products-table {
      margin-bottom: 16px;

      .code-tag {
        font-family: 'Courier New', monospace;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.3px;
      }

      .number-cell {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 4px;

        .number-value {
          font-weight: 600;
          color: #303133;
        }

        .number-unit {
          font-size: 12px;
          color: #909399;
        }
      }
    }

    .table-summary {
      padding: 16px;
      background-color: #f8f9fa;
      border-radius: 6px;
      border: 1px solid #e9ecef;

      .summary-row {
        .summary-item {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;

          .summary-label {
            font-weight: 500;
            color: #606266;
          }

          .summary-value {
            font-weight: 600;
            font-size: 16px;
            color: #409eff;
          }
        }
      }
    }
  }
}

:deep(.el-table .editable-row) {
  background-color: #f0f9ff;
}

:deep(.el-descriptions__label) {
  width: 120px;
  font-weight: 500;
}

:deep(.el-tag) {
  font-weight: 500;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
