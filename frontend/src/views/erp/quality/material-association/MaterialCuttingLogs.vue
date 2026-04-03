<template>
  <div class="cutting-logs-page">
    <div class="page-header">
      <div class="header-left">
        <div class="title-wrap">
          <h2>材料使用取込</h2>
          <p>
            共有フォルダの materialCutting.csv を手動取込（材料使用ログ）。デフォルトは「5日より古い行を削除 → CSVの日付最小〜最大の範囲を削除 → 取込」で再取込時の重複を防ぎます（log_date インデックス利用で高速）。
          </p>
        </div>
        <div class="header-stats">
          <el-tag type="info" effect="light">総件数 {{ total }}</el-tag>
        </div>
      </div>
      <div class="header-actions">
        <el-button type="success" :icon="Upload" :loading="importing" @click="onImport">
          CSV取込（手動）
        </el-button>
        <el-button type="primary" :icon="Refresh" :loading="loading" @click="fetchList">再読込</el-button>
      </div>
    </div>

    <div class="import-options">
      <el-checkbox v-model="fullReplace" size="small" border>
        テーブル全件置換（TRUNCATE・最速／CSVに無い履歴は消えます）
      </el-checkbox>
      <span v-if="!fullReplace" class="retain-wrap">
        <span class="retain-label">保持日数</span>
        <el-input-number v-model="retainDays" :min="0" :max="3650" size="small" controls-position="right" />
        <span class="retain-hint">0＝古い行を残したまま、CSV日付帯のみ置換</span>
      </span>
    </div>

    <div class="path-hint">
      <el-icon><FolderOpened /></el-icon>
      <span class="path-text">{{ csvPathHint }}</span>
    </div>

    <div class="filter-bar">
      <el-input
        v-model="keyword"
        placeholder="材料コード・製造番号・管理コード・HDNo・担当者で検索"
        clearable
        :prefix-icon="Search"
        size="small"
        class="filter-keyword"
        @keyup.enter="onSearch"
      />
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="～"
        start-placeholder="開始日"
        end-placeholder="終了日"
        value-format="YYYY-MM-DD"
        size="small"
        class="filter-dates"
      />
      <el-button type="primary" size="small" :icon="Search" @click="onSearch">検索</el-button>
    </div>

    <div class="table-card">
      <el-table
        :data="list"
        v-loading="loading"
        border
        stripe
        size="small"
        height="calc(100vh - 280px)"
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
      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100, 200]"
          layout="total, sizes, prev, pager, next"
          small
          background
          @current-change="fetchList"
          @size-change="onSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Search, Upload, FolderOpened } from '@element-plus/icons-vue'
import {
  getMaterialCuttingLogs,
  importMaterialCuttingCsv,
  type MaterialCuttingLogItem,
} from '@/api/material'
import { toPlainCodeDisplay } from '@/utils/plainCodeDisplay'

const csvPathHint =
  '\\\\192.168.1.200\\社内共有\\02_生産管理部\\Data\\BT-data\\受信\\materialCutting.csv'

const fullReplace = ref(false)
const retainDays = ref(5)

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
  const msg = fullReplace.value
    ? 'テーブルを TRUNCATE してから CSV を全件取込します。既存の材料使用ログはすべて削除されます。続行しますか？'
    : `保持日数 ${retainDays.value}：それより古い行を削除し、CSV の日付範囲内を置換してから取込します（重複しません）。よろしいですか？`
  try {
    await ElMessageBox.confirm(msg, '材料使用取込', {
      type: 'warning',
      confirmButtonText: '取込',
      cancelButtonText: 'キャンセル',
    })
  } catch {
    return
  }
  importing.value = true
  try {
    const res = await importMaterialCuttingCsv({
      full_replace: fullReplace.value,
      retain_days: fullReplace.value ? undefined : retainDays.value,
    })
    const n = res.imported ?? 0
    const errN = res.errors_count ?? 0
    if (res.full_replace) {
      ElMessage.success(`取込完了（全件置換）：${n} 件・エラー行 ${errN}`)
    } else {
      const dp = res.deleted_prune ?? 0
      const dw = res.deleted_window ?? 0
      const sk = res.skipped_before_retention ?? 0
      ElMessage.success(
        `取込 ${n} 件 / 削除(保持期間外) ${dp} / 削除(CSV日付帯) ${dw} / CSVスキップ(期間外) ${sk} / エラー行 ${errN}`,
      )
    }
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

onMounted(fetchList)
</script>

<style scoped>
.cutting-logs-page {
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: linear-gradient(145deg, #f4f7fb 0%, #eef3f9 100%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
  border-radius: 10px;
  padding: 10px 12px;
  color: #fff;
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.22);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.title-wrap h2 {
  margin: 0;
  font-size: 18px;
  line-height: 1.2;
}

.title-wrap p {
  margin: 3px 0 0;
  color: rgba(255, 255, 255, 0.92);
  font-size: 12px;
}

.header-stats {
  display: flex;
  gap: 6px;
}

.import-options {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px 16px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 12px;
  color: #475569;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.retain-wrap {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.retain-label {
  color: #64748b;
}

.retain-hint {
  color: #94a3b8;
  font-size: 11px;
}

.path-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 12px;
  color: #475569;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.path-text {
  word-break: break-all;
  font-family: ui-monospace, monospace;
}

.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 8px 10px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
}

.filter-keyword {
  flex: 1;
  min-width: 200px;
  max-width: 360px;
}

.filter-dates {
  width: 260px;
}

.table-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 6px;
  box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
}

.table-card :deep(.el-table th) {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}

.pager {
  display: flex;
  justify-content: flex-end;
  padding: 8px 4px 4px;
}
</style>
