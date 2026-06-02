<!--
  FIN 汎用バッチ処理ページ。
  対象一覧を表示し、選択行に対して一括処理（決算締め・給与計算・仕訳一括生成等）を実行する。
  実際の処理は各 services/（posting_service / calc_engine 等）の専用エンドポイントへ
  actionPath を差し替えて接続する。未接続時は確認のみのスケルトン動作。
-->
<template>
  <div class="fin-batch-page">
    <div class="fin-page-header">
      <div class="fin-page-title">
        <el-icon><Cpu /></el-icon>
        <span>{{ title }}</span>
      </div>
      <div class="fin-page-actions">
        <el-button type="primary" :disabled="!selection.length" :loading="running" @click="runBatch">
          <el-icon><Cpu /></el-icon>一括処理（{{ selection.length }}件）
        </el-button>
      </div>
    </div>

    <el-card shadow="never">
      <el-table
        :data="rows"
        v-loading="loading"
        stripe
        border
        height="calc(100vh - 260px)"
        @selection-change="(s: Row[]) => (selection = s)"
      >
        <el-table-column type="selection" width="50" fixed />
        <el-table-column
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :min-width="col.width || 140"
          show-overflow-tooltip
        />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { Cpu } from '@element-plus/icons-vue'
import request from '@/shared/api/request'
import { createFinResource } from '@/api/fin'
import type { FinColumn } from './types'

const props = defineProps<{
  title: string
  apiBase: string
  columns: FinColumn[]
  actionPath?: string
}>()

type Row = Record<string, unknown>
const api = createFinResource<Row>(props.apiBase)
const rows = ref<Row[]>([])
const selection = ref<Row[]>([])
const loading = ref(false)
const running = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

async function reload() {
  loading.value = true
  try {
    const data = await api.list({ page: page.value, page_size: pageSize.value })
    rows.value = data.items || []
    total.value = data.total || 0
  } catch {
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function runBatch() {
  await ElMessageBox.confirm(`${selection.value.length}件を一括処理します。よろしいですか？`, '確認', {
    type: 'warning',
  })
  running.value = true
  try {
    const ids = selection.value.map((r) => r.id)
    if (props.actionPath) {
      await request.post(props.actionPath, { ids })
      ElMessage.success('一括処理を実行しました')
      await reload()
    } else {
      ElMessage.info('処理エンドポイント未接続（生成スケルトン）。services/ 実装後に actionPath を設定してください。')
    }
  } finally {
    running.value = false
  }
}

onMounted(reload)
</script>

<style scoped>
.fin-batch-page { padding: 16px; }
.fin-page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.fin-page-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; }
.fin-page-actions { display: flex; gap: 10px; }
.fin-pager { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
