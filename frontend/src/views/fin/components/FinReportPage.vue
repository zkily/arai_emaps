<!--
  FIN 汎用レポート（読み取り専用）ページ。
  期間・キーワードで絞り込み、結果をテーブル表示する。集計ロジックは
  バックエンドの専用エンドポイント（posting_service 等）が整備され次第、
  apiBase を差し替えるか *.custom.vue で拡張する。
-->
<template>
  <div class="fin-report-page">
    <div class="fin-page-header">
      <div class="fin-page-title">
        <el-icon><DataAnalysis /></el-icon>
        <span>{{ title }}</span>
      </div>
      <div class="fin-page-actions">
        <el-input v-model="keyword" placeholder="キーワード" clearable style="width: 220px" @keyup.enter="reload" @clear="reload" />
        <el-button type="primary" @click="reload"><el-icon><Search /></el-icon>表示</el-button>
        <el-button @click="exportCsv"><el-icon><Download /></el-icon>CSV</el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-table :data="rows" v-loading="loading" stripe border height="calc(100vh - 260px)">
        <el-table-column type="index" label="#" width="55" align="center" />
        <el-table-column
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :min-width="col.width || 140"
          :align="col.align || 'left'"
          show-overflow-tooltip
        />
      </el-table>
      <div class="fin-pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[50, 100, 200]"
          layout="total, sizes, prev, pager, next"
          @current-change="reload"
          @size-change="reload"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { DataAnalysis, Search, Download } from '@element-plus/icons-vue'
import { createFinResource } from '@/api/fin'
import type { FinColumn } from './types'

const props = defineProps<{ title: string; apiBase: string; columns: FinColumn[] }>()

type Row = Record<string, unknown>
const api = createFinResource<Row>(props.apiBase)
const rows = ref<Row[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const keyword = ref('')

async function reload() {
  loading.value = true
  try {
    const data = await api.list({ page: page.value, page_size: pageSize.value, q: keyword.value || undefined })
    rows.value = data.items || []
    total.value = data.total || 0
  } catch {
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function exportCsv() {
  if (!rows.value.length) {
    ElMessage.info('データがありません')
    return
  }
  const header = props.columns.map((c) => c.label).join(',')
  const body = rows.value
    .map((r) => props.columns.map((c) => String(r[c.prop] ?? '')).join(','))
    .join('\n')
  const blob = new Blob([`\uFEFF${header}\n${body}`], { type: 'text/csv;charset=utf-8' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${props.title}.csv`
  a.click()
}

onMounted(reload)
</script>

<style scoped>
.fin-report-page { padding: 16px; }
.fin-page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.fin-page-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; }
.fin-page-actions { display: flex; gap: 10px; }
.fin-pager { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
