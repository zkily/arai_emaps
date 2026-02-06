<template>
  <div class="supplier-list-page">
    <!-- 动态背景 -->
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
    </div>

    <!-- 页面头部 -->
    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"><OfficeBuilding /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">仕入先管理</h1>
            <div class="header-subtitle">{{ pagination.total }} 件</div>
          </div>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="showAddDialog">
            <el-icon><Plus /></el-icon>新規登録
          </el-button>
          <el-button @click="exportData">
            <el-icon><Download /></el-icon>エクスポート
          </el-button>
        </div>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="filter-section modern-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="キーワード">
          <el-input v-model="filters.keyword" placeholder="コード・名称で検索" clearable @keyup.enter="handleSearch" />
        </el-form-item>
        <el-form-item label="種別">
          <el-select v-model="filters.supplier_type" placeholder="種別を選択" clearable>
            <el-option label="メーカー" value="manufacturer" />
            <el-option label="商社" value="distributor" />
            <el-option label="サービス" value="service" />
            <el-option label="その他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="評価">
          <el-select v-model="filters.rating" placeholder="評価" clearable>
            <el-option label="A" value="A" />
            <el-option label="B" value="B" />
            <el-option label="C" value="C" />
            <el-option label="D" value="D" />
          </el-select>
        </el-form-item>
        <el-form-item label="状態">
          <el-select v-model="filters.is_active" placeholder="状態" clearable>
            <el-option label="有効" :value="true" />
            <el-option label="無効" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>検索
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>リセット
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据表格 -->
    <div class="table-section modern-card">
      <el-table :data="suppliers" v-loading="loading" stripe border class="modern-table">
        <el-table-column prop="supplier_code" label="仕入先コード" width="130">
          <template #default="{ row }">
            <span class="link-text" @click="viewSupplier(row)">{{ row.supplier_code }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="supplier_name" label="仕入先名" min-width="180" />
        <el-table-column prop="supplier_type_name" label="種別" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.supplier_type_name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="電話番号" width="130" />
        <el-table-column prop="email" label="メール" width="180" />
        <el-table-column prop="rating" label="評価" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="getRatingType(row.rating)" size="small">{{ row.rating || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="payment_term" label="支払条件" width="100" />
        <el-table-column label="状態" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '有効' : '無効' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right" align="center">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="viewSupplier(row)">詳細</el-button>
            <el-button size="small" type="warning" link @click="editSupplier(row)">編集</el-button>
            <el-button size="small" :type="row.is_active ? 'danger' : 'success'" link @click="toggleStatus(row)">
              {{ row.is_active ? '無効化' : '有効化' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" destroy-on-close>
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="仕入先コード" prop="supplier_code">
              <el-input v-model="formData.supplier_code" :disabled="isEdit" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="仕入先名" prop="supplier_name">
              <el-input v-model="formData.supplier_name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="種別" prop="supplier_type">
              <el-select v-model="formData.supplier_type" style="width: 100%">
                <el-option label="メーカー" value="manufacturer" />
                <el-option label="商社" value="distributor" />
                <el-option label="サービス" value="service" />
                <el-option label="その他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="カナ">
              <el-input v-model="formData.supplier_name_kana" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="電話番号">
              <el-input v-model="formData.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="FAX">
              <el-input v-model="formData.fax" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="メール">
              <el-input v-model="formData.email" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ウェブサイト">
              <el-input v-model="formData.website" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="郵便番号">
          <el-input v-model="formData.postal_code" style="width: 150px" />
        </el-form-item>
        <el-form-item label="住所">
          <el-input v-model="formData.address" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="支払条件">
              <el-input v-model="formData.payment_term" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="与信限度額">
              <el-input-number v-model="formData.credit_limit" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="備考">
          <el-input v-model="formData.remarks" type="textarea" :rows="3" />
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { OfficeBuilding, Plus, Download, Search, Refresh } from '@element-plus/icons-vue'
import { getSupplierList, createSupplier, updateSupplier, toggleSupplierStatus } from '@/api/erp/supplier'
import type { Supplier } from '@/types/erp/supplier'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const loading = ref(false)
const submitting = ref(false)
const suppliers = ref<Supplier[]>([])

const filters = reactive({
  keyword: '',
  supplier_type: '',
  rating: '',
  is_active: undefined as boolean | undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 50,
  total: 0
})

// 弹窗相关
const dialogVisible = ref(false)
const isEdit = ref(false)
const dialogTitle = computed(() => isEdit.value ? '仕入先編集' : '仕入先登録')
const formRef = ref<FormInstance>()
const formData = reactive<Partial<Supplier>>({
  supplier_code: '',
  supplier_name: '',
  supplier_name_kana: '',
  supplier_type: 'manufacturer',
  phone: '',
  fax: '',
  email: '',
  website: '',
  postal_code: '',
  address: '',
  payment_term: '',
  credit_limit: undefined,
  remarks: ''
})

const formRules: FormRules = {
  supplier_code: [{ required: true, message: '仕入先コードを入力してください', trigger: 'blur' }],
  supplier_name: [{ required: true, message: '仕入先名を入力してください', trigger: 'blur' }],
  supplier_type: [{ required: true, message: '種別を選択してください', trigger: 'change' }]
}

// 获取评价标签类型
const getRatingType = (rating: string) => {
  const typeMap: Record<string, string> = {
    A: 'success',
    B: 'primary',
    C: 'warning',
    D: 'danger'
  }
  return typeMap[rating] || 'info'
}

// 显示新增弹窗
const showAddDialog = () => {
  isEdit.value = false
  Object.assign(formData, {
    supplier_code: '',
    supplier_name: '',
    supplier_name_kana: '',
    supplier_type: 'manufacturer',
    phone: '',
    fax: '',
    email: '',
    website: '',
    postal_code: '',
    address: '',
    payment_term: '',
    credit_limit: undefined,
    remarks: ''
  })
  dialogVisible.value = true
}

// 查看供应商
const viewSupplier = (row: Supplier) => {
  router.push(`/erp/supplier/${row.id}`)
}

// 编辑供应商
const editSupplier = (row: Supplier) => {
  isEdit.value = true
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 切换状态
const toggleStatus = async (row: Supplier) => {
  try {
    const action = row.is_active ? '無効化' : '有効化'
    await ElMessageBox.confirm(`この仕入先を${action}しますか？`, '確認', { type: 'warning' })
    await toggleSupplierStatus(row.id, !row.is_active)
    ElMessage.success(`${action}しました`)
    fetchData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作に失敗しました')
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()
  
  submitting.value = true
  try {
    if (isEdit.value && formData.id) {
      await updateSupplier(formData.id, formData)
      ElMessage.success('更新しました')
    } else {
      await createSupplier(formData)
      ElMessage.success('登録しました')
    }
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('保存に失敗しました')
  } finally {
    submitting.value = false
  }
}

// 导出
const exportData = () => {
  ElMessage.info('エクスポート機能は開発中です')
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

// 重置
const resetFilters = () => {
  filters.keyword = ''
  filters.supplier_type = ''
  filters.rating = ''
  filters.is_active = undefined
  pagination.page = 1
  fetchData()
}

// 分页
const handleSizeChange = () => {
  pagination.page = 1
  fetchData()
}

const handleCurrentChange = () => {
  fetchData()
}

// 获取数据
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      keyword: filters.keyword || undefined,
      supplier_type: filters.supplier_type || undefined,
      rating: filters.rating || undefined,
      is_active: filters.is_active,
      page: pagination.page,
      page_size: pagination.pageSize
    }
    const res = await getSupplierList(params)
    suppliers.value = res.data?.items || res.items || []
    pagination.total = res.data?.total || res.total || 0
  } catch (error) {
    console.error('データ取得に失敗しました', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.supplier-list-page {
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
}

.dynamic-background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  animation: float 20s ease-in-out infinite;
}

.orb-1 { width: 300px; height: 300px; top: -150px; right: -150px; }
.orb-2 { width: 200px; height: 200px; bottom: -100px; left: -100px; animation-delay: -10s; }

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-30px); }
}

.modern-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #9254de, #b37feb);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.header-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0;
}

.header-subtitle {
  font-size: 14px;
  color: #8492a6;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.modern-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.filter-section {
  padding: 20px;
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.table-section {
  padding: 20px;
}

.modern-table {
  border-radius: 8px;
  overflow: hidden;
}

.link-text {
  color: #409eff;
  cursor: pointer;
}

.link-text:hover {
  text-decoration: underline;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>
