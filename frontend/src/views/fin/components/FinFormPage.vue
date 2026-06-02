<!--
  FIN 汎用シングルトン設定フォーム。
  apiBase の先頭レコード（無ければ新規）を 1 件編集する用途（会計設定など）。
-->
<template>
  <div class="fin-form-page">
    <div class="fin-page-header">
      <div class="fin-page-title">
        <el-icon><Tools /></el-icon>
        <span>{{ title }}</span>
      </div>
    </div>

    <el-card shadow="never" class="fin-form-card" v-loading="loading">
      <el-form :model="form" label-width="160px" style="max-width: 640px">
        <el-form-item v-for="f in fields" :key="f.prop" :label="f.label" :required="f.required">
          <el-switch v-if="f.type === 'switch'" v-model="form[f.prop]" />
          <el-input-number
            v-else-if="f.type === 'number'"
            v-model="form[f.prop]"
            :controls="false"
            style="width: 100%"
          />
          <el-date-picker
            v-else-if="f.type === 'date'"
            v-model="form[f.prop]"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
          <el-input v-else v-model="form[f.prop]" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="saving" @click="save">
            <el-icon><Check /></el-icon>保存
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Tools, Check } from '@element-plus/icons-vue'
import { createFinResource } from '@/api/fin'
import type { FinField } from './types'

const props = defineProps<{ title: string; apiBase: string; fields: FinField[] }>()

type Row = Record<string, unknown>
const api = createFinResource<Row>(props.apiBase)
const loading = ref(false)
const saving = ref(false)
const recordId = ref<number | null>(null)
const form = reactive<Row>({})

async function load() {
  loading.value = true
  try {
    const data = await api.list({ page: 1, page_size: 1 })
    const first = data.items?.[0]
    if (first) {
      recordId.value = (first.id as number) ?? null
      props.fields.forEach((f) => {
        form[f.prop] = first[f.prop]
      })
    }
  } catch {
    /* noop */
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    if (recordId.value) {
      await api.update(recordId.value, { ...form })
    } else {
      const created = await api.create({ ...form })
      recordId.value = (created?.id as number) ?? null
    }
    ElMessage.success('保存しました')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.fin-form-page { padding: 16px; }
.fin-page-header { margin-bottom: 12px; }
.fin-page-title { display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 700; }
</style>
