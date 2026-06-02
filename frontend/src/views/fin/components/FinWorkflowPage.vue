<!--
  FIN 汎用ワークフロー（申請→承認）ページ。
  申請一覧を表示し、承認/却下で status を更新する。詳細な多段承認は
  fin_approval_flow / fin_approval_instance を用いた専用ロジックで拡張する。
-->
<template>
  <div class="fin-workflow-page">
    <div class="fin-page-header">
      <div class="fin-page-title">
        <el-icon><CircleCheck /></el-icon>
        <span>{{ title }}</span>
      </div>
      <div class="fin-page-actions">
        <el-select v-model="statusFilter" placeholder="ステータス" clearable style="width: 160px" @change="reload">
          <el-option label="申請中" value="submitted" />
          <el-option label="承認済" value="approved" />
          <el-option label="却下" value="rejected" />
        </el-select>
        <el-button type="primary" @click="reload"><el-icon><Search /></el-icon>表示</el-button>
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
          show-overflow-tooltip
        >
          <template v-if="col.prop === 'status'" #default="{ row }">
            <el-tag :type="statusType(String(row.status))" size="small">{{ statusLabel(String(row.status)) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="承認操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button
              link
              type="success"
              size="small"
              :disabled="row.status === 'approved'"
              @click="decide(row, 'approved')"
            >承認</el-button>
            <el-button
              link
              type="danger"
              size="small"
              :disabled="row.status === 'rejected'"
              @click="decide(row, 'rejected')"
            >却下</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="fin-pager">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="reload"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { CircleCheck, Search } from '@element-plus/icons-vue'
import { createFinResource } from '@/api/fin'
import type { FinColumn } from './types'

const props = defineProps<{ title: string; apiBase: string; columns: FinColumn[] }>()

type Row = Record<string, unknown>
const api = createFinResource<Row>(props.apiBase)
const rows = ref<Row[]>([])
const loading = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const statusFilter = ref('')

function statusLabel(s: string) {
  return { submitted: '申請中', approved: '承認済', rejected: '却下', draft: '下書き', paid: '支払済' }[s] || s
}
function statusType(s: string): 'success' | 'danger' | 'warning' | 'info' {
  if (s === 'approved' || s === 'paid') return 'success'
  if (s === 'rejected') return 'danger'
  if (s === 'submitted') return 'warning'
  return 'info'
}

async function reload() {
  loading.value = true
  try {
    const data = await api.list({ page: page.value, page_size: pageSize.value, status: statusFilter.value || undefined })
    rows.value = data.items || []
    total.value = data.total || 0
  } catch {
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function decide(row: Row, status: 'approved' | 'rejected') {
  await api.update(row.id as number, { status })
  ElMessage.success(status === 'approved' ? '承認しました' : '却下しました')
  await reload()
}

onMounted(reload)
</script>

<style scoped>
.fin-workflow-page { padding: 16px; }
.fin-page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.fin-page-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; }
.fin-page-actions { display: flex; gap: 10px; }
.fin-pager { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
