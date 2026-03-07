<template>
  <div class="numbering-rule">
    <div class="page-header">
      <h2>採番ルール管理</h2>
      <p class="subtitle">各伝票番号（例: SO-202310-001）の自動採番ルール設定</p>
    </div>

    <el-card class="action-card" shadow="never">
      <el-button type="primary" :icon="Plus" @click="handleAdd">新規ルール追加</el-button>
      <el-button :icon="Refresh" @click="handleRefresh">リフレッシュ</el-button>
    </el-card>

    <el-card class="table-card" shadow="never">
      <el-table :data="ruleList" v-loading="loading" stripe border>
        <el-table-column prop="code" label="ルールコード" width="120" />
        <el-table-column prop="name" label="ルール名" min-width="150" />
        <el-table-column prop="prefix" label="プレフィックス" width="120" />
        <el-table-column prop="format" label="フォーマット" min-width="180">
          <template #default="{ row }">
            <code class="format-code">{{ row.format }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="example" label="例" width="180">
          <template #default="{ row }">
            <el-tag type="info">{{ row.example }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="current_number" label="現在番号" width="100" align="right" />
        <el-table-column prop="reset_type" label="リセット" width="100">
          <template #default="{ row }">
            <el-tag :type="getResetTypeTag(row.reset_type)" size="small">{{ row.reset_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="ステータス" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.status" @change="handleStatusChange(row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="handleEdit(row)">編集</el-button>
            <el-button size="small" type="info" link @click="handleTest(row)">テスト</el-button>
            <el-button size="small" type="danger" link @click="handleDelete(row)">削除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 編集ダイアログ -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="650px" destroy-on-close>
      <el-form :model="ruleForm" :rules="formRules" ref="formRef" label-width="140px">
        <el-form-item label="ルールコード" prop="code">
          <el-input v-model="ruleForm.code" placeholder="例: SALES_ORDER" />
        </el-form-item>
        <el-form-item label="ルール名" prop="name">
          <el-input v-model="ruleForm.name" placeholder="例: 受注番号" />
        </el-form-item>
        <el-form-item label="プレフィックス" prop="prefix">
          <el-input v-model="ruleForm.prefix" placeholder="例: SO" />
        </el-form-item>
        <el-form-item label="フォーマット" prop="format">
          <el-input v-model="ruleForm.format" placeholder="例: {PREFIX}-{YYYY}{MM}-{SEQ:4}" />
          <div class="form-tip">
            利用可能な変数: {PREFIX}, {YYYY}, {YY}, {MM}, {DD}, {SEQ:桁数}
          </div>
        </el-form-item>
        <el-form-item label="連番開始値" prop="start_number">
          <el-input-number v-model="ruleForm.start_number" :min="1" />
        </el-form-item>
        <el-form-item label="連番増分" prop="increment">
          <el-input-number v-model="ruleForm.increment" :min="1" />
        </el-form-item>
        <el-form-item label="リセットタイミング" prop="reset_type">
          <el-select v-model="ruleForm.reset_type" style="width: 100%">
            <el-option label="リセットなし" value="never" />
            <el-option label="日次" value="daily" />
            <el-option label="月次" value="monthly" />
            <el-option label="年次" value="yearly" />
          </el-select>
        </el-form-item>
        <el-form-item label="プレビュー">
          <el-tag size="large" type="success">{{ previewNumber }}</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import dayjs from 'dayjs'

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref<FormInstance>()

const ruleForm = reactive({
  id: 0,
  code: '',
  name: '',
  prefix: '',
  format: '{PREFIX}-{YYYY}{MM}-{SEQ:4}',
  start_number: 1,
  increment: 1,
  reset_type: 'monthly',
})

const formRules: FormRules = {
  code: [{ required: true, message: 'ルールコードを入力してください', trigger: 'blur' }],
  name: [{ required: true, message: 'ルール名を入力してください', trigger: 'blur' }],
  prefix: [{ required: true, message: 'プレフィックスを入力してください', trigger: 'blur' }],
  format: [{ required: true, message: 'フォーマットを入力してください', trigger: 'blur' }],
}

const ruleList = ref([
  { id: 1, code: 'SALES_ORDER', name: '受注番号', prefix: 'SO', format: '{PREFIX}-{YYYY}{MM}-{SEQ:4}', example: 'SO-202602-0001', current_number: 156, reset_type: '月次', status: true },
  { id: 2, code: 'QUOTATION', name: '見積番号', prefix: 'QT', format: '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', example: 'QT-20260205-001', current_number: 42, reset_type: '日次', status: true },
  { id: 3, code: 'PURCHASE_ORDER', name: '発注番号', prefix: 'PO', format: '{PREFIX}-{YYYY}-{SEQ:5}', example: 'PO-2026-00089', current_number: 89, reset_type: '年次', status: true },
  { id: 4, code: 'INVOICE', name: '請求書番号', prefix: 'INV', format: '{PREFIX}{YYYY}{MM}-{SEQ:4}', example: 'INV202602-0023', current_number: 23, reset_type: '月次', status: true },
  { id: 5, code: 'SHIPMENT', name: '出荷番号', prefix: 'SHP', format: '{PREFIX}-{YYYY}{MM}{DD}-{SEQ:3}', example: 'SHP-20260205-015', current_number: 15, reset_type: '日次', status: true },
])

const dialogTitle = computed(() => isEdit.value ? '採番ルール編集' : '採番ルール新規追加')

const previewNumber = computed(() => {
  const now = dayjs().tz('Asia/Tokyo')
  let result = ruleForm.format
    .replace('{PREFIX}', ruleForm.prefix)
    .replace('{YYYY}', now.format('YYYY'))
    .replace('{YY}', now.format('YY'))
    .replace('{MM}', now.format('MM'))
    .replace('{DD}', now.format('DD'))

  const seqMatch = result.match(/\{SEQ:(\d+)\}/)
  if (seqMatch) {
    const digits = parseInt(seqMatch[1])
    result = result.replace(seqMatch[0], String(ruleForm.start_number).padStart(digits, '0'))
  }
  return result
})

type TagType = 'primary' | 'success' | 'warning' | 'info' | 'danger'
const getResetTypeTag = (type: string): TagType => {
  const tags: Record<string, TagType> = { '日次': 'success', '月次': 'primary', '年次': 'warning', 'なし': 'info' }
  return tags[type] || 'info'
}

const handleAdd = () => {
  isEdit.value = false
  Object.assign(ruleForm, { id: 0, code: '', name: '', prefix: '', format: '{PREFIX}-{YYYY}{MM}-{SEQ:4}', start_number: 1, increment: 1, reset_type: 'monthly' })
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  Object.assign(ruleForm, row)
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm(`ルール「${row.name}」を削除しますか？`, '確認', { type: 'warning' })
  ElMessage.success('削除しました（TODO: API呼び出し）')
}

const handleTest = (row: any) => {
  ElMessage.success(`次の番号: ${row.example.replace(/\d+$/, (m: string) => String(parseInt(m) + 1).padStart(m.length, '0'))}`)
}

const handleStatusChange = (row: any) => {
  ElMessage.success(`ステータスを${row.status ? '有効' : '無効'}にしました（TODO: API呼び出し）`)
}

const handleRefresh = () => {
  ElMessage.info('リフレッシュ（TODO: API呼び出し）')
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  submitting.value = true
  setTimeout(() => {
    submitting.value = false
    dialogVisible.value = false
    ElMessage.success('保存しました（TODO: API呼び出し）')
  }, 1000)
}
</script>

<style scoped>
.numbering-rule {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: #303133;
}

.subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.action-card {
  margin-bottom: 16px;
}

.format-code {
  background: #f4f4f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
}

.form-tip {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
