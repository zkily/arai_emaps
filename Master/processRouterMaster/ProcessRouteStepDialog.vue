<template>
  <el-dialog class="route-step-dialog" v-model="visible" :title="''" width="520px" top="10vh"
    :close-on-click-modal="false" @close="onClose">
    <div class="dialog-title">
      <span class="icon">{{ mode === 'add' ? '📦' : '✏️' }}</span>
      <span>{{ mode === 'add' ? 'ステップ追加' : 'ステップ編集' }}</span>
    </div>
    <el-form :model="form" :rules="rules" ref="formRef" label-width="130px" class="form-section card-section">
      <el-row :gutter="10">
        <el-col :span="24">
          <el-form-item label="🔢 順番" prop="step_no">
            <el-input-number v-model="form.step_no" :min="1" />
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="🛠️ 工程" prop="process_cd">
            <el-select v-model="form.process_cd" placeholder="工程を選択" clearable filterable>
              <el-option v-for="item in processOptions" :key="item.cd" :label="`${item.cd}｜${item.name}`"
                :value="item.cd" />
            </el-select>
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="📉 歩留（%）" prop="yield_percent">
            <el-input-number v-model="form.yield_percent" :min="0" :max="100" :precision="1" placeholder="工程選択で自動設定"
              style="width: 100%" />
            <div class="field-hint">※ 工程選択時に自動設定されます</div>
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="⏱️ 標準サイクル(s)" prop="cycle_sec">
            <el-input-number v-model="form.cycle_sec" :min="0" :precision="1" placeholder="工程選択で自動設定"
              style="width: 100%" />
            <div class="field-hint">※ 工程選択時に自動設定されます</div>
          </el-form-item>
        </el-col>

        <el-col :span="24">
          <el-form-item label="💬 備考">
            <el-input v-model="form.remarks" type="textarea" :rows="2" placeholder="補足情報など" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="onClose">❌ キャンセル</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">💾 保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { createRouteStep, updateRouteStep } from '@/api/master/processRouterMaster'
import { getProcessOptions, getProcessDetails } from '@/api/options'
import type { OptionItem } from '@/types/master'

// 假设 RouteStepItem 类型如下（如有不同请替换为实际类型）
interface RouteStepItem {
  id?: number
  step_no: number
  process_cd: string
  yield_percent: number
  cycle_sec: number
  remarks?: string
}
const props = defineProps<{
  visible: boolean
  routeCd: string
  mode: 'add' | 'edit'
  initialData?: Partial<RouteStepItem>
}>()
const emit = defineEmits(['update:visible', 'saved'])

const visible = ref(props.visible)
watch(() => props.visible, (val) => {
  visible.value = val
  if (val) initialize()
})

const formRef = ref()
const form = reactive({
  id: undefined as number | undefined,
  step_no: 1,
  process_cd: '' as string,
  yield_percent: 100,
  cycle_sec: 0,
  remarks: ''
})

const processOptions = ref<OptionItem[]>([])
const saving = ref(false)

// 监听工程选择变化，自动填入默认值
watch(() => form.process_cd, async (newProcessCd, oldProcessCd) => {
  console.log('工程选择变化:', { newProcessCd, oldProcessCd, mode: props.mode })

  // 只在新增模式下，且工程代码发生变化时自动填入
  if (props.mode === 'add' && newProcessCd && newProcessCd !== oldProcessCd) {
    console.log('开始获取工程详细信息:', newProcessCd)
    try {
      const response = await getProcessDetails(newProcessCd)
      console.log('API响应:', response)

      if (response.success && response.data) {
        // 自动填入默认歩留和サイクル时间
        // default_yield是小数形式(0.95)，需要转换为百分比(95)
        const defaultYield = response.data.default_yield ? (response.data.default_yield * 100) : 100
        const defaultCycle = response.data.default_cycle_sec || 0

        console.log('设置默认值:', {
          原始yield: response.data.default_yield,
          转换后yield: defaultYield,
          cycle: defaultCycle
        })

        form.yield_percent = defaultYield
        form.cycle_sec = defaultCycle

        ElMessage.success({
          message: `工程「${response.data.process_name}」のデフォルト値を設定しました (歩留: ${defaultYield}%, サイクル: ${defaultCycle}s)`,
          duration: 3000
        })
      } else {
        console.warn('API响应无效:', response)
      }
    } catch (error) {
      console.error('工程詳細情報の取得に失敗:', error)
      ElMessage.warning('工程詳細情報の取得に失敗しました')
    }
  }
})

const initialize = async () => {
  // ① 加载 process master
  processOptions.value = await getProcessOptions()

  // ② 设置 form
  if (props.mode === 'edit' && props.initialData) {
    Object.assign(form, props.initialData)
  } else {
    Object.assign(form, {
      id: undefined,
      step_no: 1,
      process_cd: '',
      yield_percent: 100,
      cycle_sec: 0,
      remarks: ''
    })
  }
}

const rules = {
  step_no: [{ required: true, message: '順番は必須です', trigger: 'blur' }],
  process_cd: [{ required: true, message: '工程を選択してください', trigger: 'change' }]
}

const handleSubmit = () => {
  formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    saving.value = true

    try {
      if (props.mode === 'add') {
        await createRouteStep(props.routeCd, form)
      } else {
        await updateRouteStep(form.id as number, form)
      }
      ElMessage.success('保存成功')
      emit('update:visible', false)
      emit('saved')
    } catch (err: unknown) {
      let msg = '保存失敗'
      if (typeof err === 'object' && err !== null) {
        const e = err as { message?: string }
        msg = e.message || msg
      }
      ElMessage.error(msg)
    } finally {
      saving.value = false
    }
  })
}

const onClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.route-step-dialog :deep(.el-dialog) {
  border-radius: 16px;
}

.dialog-title {
  font-size: 22px;
  font-weight: bold;
  color: #2c3e50;
  padding: 20px 24px 12px;
  border-bottom: 1px solid #ebeef5;
  background: linear-gradient(to right, #e6f7ff, #ffffff);
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-title .icon {
  margin-right: 8px;
  font-size: 22px;
}

.card-section {
  background: #fafafa;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 18px;
  padding: 24px 18px 10px 18px;
}

.form-section {
  padding: 0;
}

.dialog-footer {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding-top: 10px;
}

.field-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.2;
}

@media (max-width: 600px) {
  .route-step-dialog :deep(.el-dialog) {
    width: 99vw !important;
    min-width: 0;
  }

  .card-section {
    padding: 6px 2px 4px 2px;
  }

  .dialog-title {
    font-size: 18px;
    padding: 14px 10px 8px 10px;
  }
}
</style>
