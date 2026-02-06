<template>
  <div class="stock-movement">
    <div class="page-header">
      <h2>入出庫移動</h2>
      <p class="subtitle">倉庫間移動・良品/不良品区分変更・セット品組立/分解</p>
    </div>

    <!-- タブ切替 -->
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 倉庫間移動 -->
      <el-tab-pane label="倉庫間移動" name="transfer">
        <el-card shadow="never">
          <el-form :model="transferForm" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="移動元倉庫" required>
                  <el-select v-model="transferForm.from_warehouse" placeholder="倉庫選択" filterable>
                    <el-option v-for="w in warehouses" :key="w.cd" :label="w.name" :value="w.cd" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="移動先倉庫" required>
                  <el-select v-model="transferForm.to_warehouse" placeholder="倉庫選択" filterable>
                    <el-option v-for="w in warehouses" :key="w.cd" :label="w.name" :value="w.cd" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="品番" required>
              <el-select v-model="transferForm.product_code" placeholder="品番選択" filterable>
                <el-option v-for="p in products" :key="p.cd" :label="`${p.cd} - ${p.name}`" :value="p.cd" />
              </el-select>
            </el-form-item>
            <el-form-item label="ロット番号">
              <el-input v-model="transferForm.lot_no" placeholder="ロット番号" />
            </el-form-item>
            <el-form-item label="移動数量" required>
              <el-input-number v-model="transferForm.quantity" :min="1" />
              <span class="available-stock">（在庫: {{ availableStock }}）</span>
            </el-form-item>
            <el-form-item label="備考">
              <el-input v-model="transferForm.remarks" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleTransfer">移動実行</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- 区分変更 -->
      <el-tab-pane label="区分変更" name="status_change">
        <el-card shadow="never">
          <el-form :model="statusForm" label-width="120px">
            <el-form-item label="倉庫" required>
              <el-select v-model="statusForm.warehouse" placeholder="倉庫選択" filterable>
                <el-option v-for="w in warehouses" :key="w.cd" :label="w.name" :value="w.cd" />
              </el-select>
            </el-form-item>
            <el-form-item label="品番" required>
              <el-select v-model="statusForm.product_code" placeholder="品番選択" filterable>
                <el-option v-for="p in products" :key="p.cd" :label="`${p.cd} - ${p.name}`" :value="p.cd" />
              </el-select>
            </el-form-item>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="変更前区分" required>
                  <el-select v-model="statusForm.from_status" placeholder="区分選択">
                    <el-option label="良品" value="good" />
                    <el-option label="不良品" value="defective" />
                    <el-option label="保留" value="hold" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="変更後区分" required>
                  <el-select v-model="statusForm.to_status" placeholder="区分選択">
                    <el-option label="良品" value="good" />
                    <el-option label="不良品" value="defective" />
                    <el-option label="保留" value="hold" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="変更数量" required>
              <el-input-number v-model="statusForm.quantity" :min="1" />
            </el-form-item>
            <el-form-item label="理由" required>
              <el-input v-model="statusForm.reason" placeholder="変更理由" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleStatusChange">区分変更実行</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>

      <!-- セット品組立/分解 -->
      <el-tab-pane label="セット品組立/分解" name="kit">
        <el-card shadow="never">
          <el-form :model="kitForm" label-width="120px">
            <el-form-item label="処理種別" required>
              <el-radio-group v-model="kitForm.type">
                <el-radio-button value="assembly">組立</el-radio-button>
                <el-radio-button value="disassembly">分解</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="倉庫" required>
              <el-select v-model="kitForm.warehouse" placeholder="倉庫選択" filterable>
                <el-option v-for="w in warehouses" :key="w.cd" :label="w.name" :value="w.cd" />
              </el-select>
            </el-form-item>
            <el-form-item label="セット品番" required>
              <el-select v-model="kitForm.kit_product" placeholder="セット品選択" filterable>
                <el-option v-for="k in kitProducts" :key="k.cd" :label="`${k.cd} - ${k.name}`" :value="k.cd" />
              </el-select>
            </el-form-item>
            <el-form-item label="数量" required>
              <el-input-number v-model="kitForm.quantity" :min="1" />
            </el-form-item>
            <el-form-item label="構成部品">
              <el-table :data="kitComponents" border size="small">
                <el-table-column prop="product_code" label="品番" width="120" />
                <el-table-column prop="product_name" label="品名" min-width="150" />
                <el-table-column prop="required_qty" label="必要数" width="80" align="right" />
                <el-table-column prop="available_qty" label="在庫" width="80" align="right" />
              </el-table>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleKit">{{ kitForm.type === 'assembly' ? '組立実行' : '分解実行' }}</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-tab-pane>
    </el-tabs>

    <!-- 移動履歴 -->
    <el-card shadow="never" class="history-card">
      <template #header>移動履歴（直近20件）</template>
      <el-table :data="movementHistory" stripe size="small">
        <el-table-column prop="movement_date" label="日時" width="150" />
        <el-table-column prop="type" label="種別" width="100" />
        <el-table-column prop="product_code" label="品番" width="120" />
        <el-table-column prop="from_location" label="移動元" width="150" />
        <el-table-column prop="to_location" label="移動先" width="150" />
        <el-table-column prop="quantity" label="数量" width="80" align="right" />
        <el-table-column prop="user_name" label="実行者" width="100" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const activeTab = ref('transfer')
const warehouses = ref<{ cd: string; name: string }[]>([])
const products = ref<{ cd: string; name: string }[]>([])
const kitProducts = ref<{ cd: string; name: string }[]>([])
const kitComponents = ref<any[]>([])
const movementHistory = ref<any[]>([])
const availableStock = ref(0)

const transferForm = reactive({ from_warehouse: '', to_warehouse: '', product_code: '', lot_no: '', quantity: 1, remarks: '' })
const statusForm = reactive({ warehouse: '', product_code: '', from_status: '', to_status: '', quantity: 1, reason: '' })
const kitForm = reactive({ type: 'assembly', warehouse: '', kit_product: '', quantity: 1 })

onMounted(() => { loadData() })

const loadData = async () => {
  // TODO: API呼び出し
}

const handleTransfer = () => { ElMessage.success('倉庫間移動を実行しました') }
const handleStatusChange = () => { ElMessage.success('区分変更を実行しました') }
const handleKit = () => { ElMessage.success(`セット品${kitForm.type === 'assembly' ? '組立' : '分解'}を実行しました`) }
</script>

<style scoped>
.stock-movement { padding: 20px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px 0; color: #303133; }
.subtitle { margin: 0; color: #909399; font-size: 14px; }
.available-stock { margin-left: 12px; color: #909399; }
.history-card { margin-top: 20px; }
</style>
