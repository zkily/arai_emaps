<template>
  <div class="cutting-logs-page">
    <div class="main-shell">
      <header class="shell-head">
        <div class="shell-head__brand">
          <div class="brand-mark">
            <el-icon :size="18"><FolderOpened /></el-icon>
          </div>
          <div class="brand-copy">
            <h1 class="shell-title">材料使用取込</h1>
            <div class="shell-meta">
              <span class="meta-tag">取込元</span>
              <span class="meta-path" :title="csvPathHint">{{ csvPathHint }}</span>
            </div>
          </div>
        </div>
        <div class="shell-head__actions">
          <div class="count-pill">
            <span class="count-pill__n">{{ total }}</span>
            <span class="count-pill__u">件</span>
          </div>
          <el-button type="success" size="small" :icon="Upload" :loading="importing" @click="onImport">
            CSV 取込
          </el-button>
          <el-button size="small" :icon="Refresh" :loading="loading" @click="fetchList">更新</el-button>
        </div>
      </header>

      <div class="shell-filters">
        <el-input
          v-model="keyword"
          placeholder="キーワード"
          clearable
          :prefix-icon="Search"
          size="small"
          class="f-keyword"
          @keyup.enter="onSearch"
        />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="～"
          start-placeholder="開始"
          end-placeholder="終了"
          value-format="YYYY-MM-DD"
          size="small"
          class="f-dates"
        />
        <el-button type="primary" size="small" :icon="Search" @click="onSearch">検索</el-button>
      </div>

      <div class="shell-table">
        <el-table
          :data="list"
          v-loading="loading"
          border
          stripe
          size="small"
          class="data-table"
          height="calc(100vh - 158px)"
        >
          <el-table-column prop="id" label="ID" width="64" align="center" />
          <el-table-column prop="item" label="項目" width="120" show-overflow-tooltip />
          <el-table-column prop="log_date" label="日付" width="100" />
          <el-table-column prop="log_time" label="時間" width="88" />
          <el-table-column prop="hd_no" label="HDNo" width="140" show-overflow-tooltip />
          <el-table-column prop="operator_name" label="担当者" width="88" show-overflow-tooltip />
          <el-table-column label="材料コード" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              {{ toPlainCodeDisplay(row.material_cd) }}
            </template>
          </el-table-column>
          <el-table-column label="製造番号" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              {{ toPlainCodeDisplay(row.manufacture_no) }}
            </template>
          </el-table-column>
          <el-table-column label="管理コード" min-width="140" show-overflow-tooltip>
            <template #default="{ row }">
              {{ toPlainCodeDisplay(row.management_code) }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="取込日時" width="160" show-overflow-tooltip />
          <el-table-column prop="raw_line" label="元行" min-width="200" show-overflow-tooltip />
        </el-table>
      </div>

      <footer class="shell-foot">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next"
          size="small"
          background
          @current-change="fetchList"
          @size-change="onSizeChange"
        />
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, Upload, FolderOpened } from '@element-plus/icons-vue'
import {
  getMaterialCuttingCsvStatus,
  getMaterialCuttingLogs,
  importMaterialCuttingCsv,
  type MaterialCuttingLogItem,
} from '@/api/material'
import { toPlainCodeDisplay } from '@/utils/plainCodeDisplay'

/** マウント時に csv-status の path で更新 */
const csvPathHint = ref('…')

const loadCsvPathHint = async () => {
  try {
    const st = await getMaterialCuttingCsvStatus()
    if (st?.data?.path) csvPathHint.value = st.data.path
    else csvPathHint.value = '—'
  } catch {
    csvPathHint.value = '—'
  }
}

const loading = ref(false)
const importing = ref(false)
const keyword = ref('')
const dateRange = ref<[string, string] | null>(null)
const page = ref(1)
const pageSize = ref(50)
const total = ref(0)
const list = ref<MaterialCuttingLogItem[]>([])

const fetchList = async () => {
  loading.value = true
  try {
    const [startDate, endDate] = dateRange.value ?? [undefined, undefined]
    const res = await getMaterialCuttingLogs({
      page: page.value,
      pageSize: pageSize.value,
      keyword: keyword.value.trim() || undefined,
      startDate,
      endDate,
    })
    list.value = res?.data?.list ?? []
    total.value = res?.data?.total ?? 0
  } catch (e: unknown) {
    const msg = e && typeof e === 'object' && 'response' in e
      ? String((e as { response?: { data?: { detail?: string } } }).response?.data?.detail ?? '')
      : ''
    ElMessage.error(msg || '一覧の取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  page.value = 1
  fetchList()
}

const onSizeChange = () => {
  page.value = 1
  fetchList()
}

const onImport = async () => {
  try {
    await ElMessageBox.confirm(
      '共有フォルダの CSV を取り込みます。よろしいですか？',
      '材料使用取込',
      {
        type: 'warning',
        confirmButtonText: '取込',
        cancelButtonText: 'キャンセル',
      },
    )
  } catch {
    return
  }
  importing.value = true
  try {
    const res = await importMaterialCuttingCsv()
    const n = res.imported ?? 0
    const errN = res.errors_count ?? 0
    const dp = res.deleted_prune ?? 0
    const dw = res.deleted_window ?? 0
    const sk = res.skipped_before_retention ?? 0
    ElMessage.success(
      `取込 ${n} 件 / 削除(保持期間外) ${dp} / 削除(CSV日付帯) ${dw} / CSVスキップ(期間外) ${sk} / エラー行 ${errN}`,
    )
    if (res.errors?.length) {
      ElMessage.warning(res.errors.slice(0, 3).join(' / '))
    }
    await fetchList()
  } catch (e: unknown) {
    const detail =
      e && typeof e === 'object' && 'response' in e
        ? (e as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : undefined
    ElMessage.error(typeof detail === 'string' ? detail : '取込に失敗しました')
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  void fetchList()
  void loadCsvPathHint()
})
</script>

<style scoped>
.cutting-logs-page {
  padding: 8px 10px 10px;
  box-sizing: border-box;
  min-height: 100%;
  background:
    radial-gradient(1200px 400px at 12% -10%, rgba(13, 148, 136, 0.09), transparent 55%),
    radial-gradient(900px 360px at 100% 0%, rgba(59, 130, 246, 0.06), transparent 50%),
    linear-gradient(180deg, #eef2f6 0%, #e2e8f0 100%);
}

.main-shell {
  max-width: 1680px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow:
    0 1px 0 rgba(255, 255, 255, 0.9) inset,
    0 8px 32px -8px rgba(15, 23, 42, 0.12),
    0 2px 8px -2px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.shell-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 8px 12px;
  background: linear-gradient(105deg, #f8fafc 0%, #f1f5f9 48%, #ecfdf5 100%);
  border-bottom: 1px solid rgba(148, 163, 184, 0.35);
}

.shell-head__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.brand-mark {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: linear-gradient(145deg, #14b8a6 0%, #0d9488 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(13, 148, 136, 0.35);
}

.brand-copy {
  min-width: 0;
  flex: 1;
}

.shell-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.shell-meta {
  margin-top: 3px;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-size: 11px;
  line-height: 1.35;
}

.meta-tag {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(15, 23, 42, 0.06);
  color: #64748b;
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.meta-path {
  min-width: 0;
  color: #475569;
  font-family: ui-monospace, 'Cascadia Code', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shell-head__actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.count-pill {
  display: inline-flex;
  align-items: baseline;
  gap: 3px;
  padding: 4px 10px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid rgba(13, 148, 136, 0.25);
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.count-pill__n {
  font-size: 15px;
  font-weight: 700;
  color: #0d9488;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.count-pill__u {
  font-size: 11px;
  color: #64748b;
}

.shell-filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #fafbfc;
  border-bottom: 1px solid #e8ecf0;
}

.f-keyword {
  width: 200px;
  max-width: min(320px, 42vw);
}

.f-dates {
  width: 220px;
}

.shell-table {
  padding: 0;
  background: #fff;
}

.shell-table :deep(.el-table) {
  --el-table-border-color: #e8ecf0;
  --el-table-header-bg-color: #f4f6f9;
}

.shell-table :deep(.el-table__header-wrapper th) {
  font-weight: 600;
  font-size: 11px;
  color: #475569;
  text-transform: none;
  letter-spacing: 0.01em;
}

.shell-table :deep(.el-table .cell) {
  padding: 4px 8px;
  line-height: 1.35;
}

.shell-table :deep(.el-table td) {
  font-size: 12px;
  color: #334155;
}

.shell-table :deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafbfc;
}

.data-table {
  width: 100%;
}

.shell-foot {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 5px 10px 6px;
  background: linear-gradient(180deg, #fafbfc 0%, #f4f6f9 100%);
  border-top: 1px solid #e8ecf0;
}

.shell-foot :deep(.el-pagination) {
  flex-wrap: wrap;
  justify-content: flex-end;
  row-gap: 4px;
}
</style>
