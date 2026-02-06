<template>
  <div class="order-log-page">
    <!-- 🔍 フィルター区域 -->
    <div class="filter-form">
      <el-form :inline="true" :model="filters" class="filter-inline">
        <el-form-item label="アクション">
          <el-select v-model="filters.action" placeholder="選択" clearable style="width: 150px">
            <el-option label="Insert" value="insert" />
            <el-option label="Update" value="update" />
            <el-option label="Error" value="error" />
          </el-select>
        </el-form-item>

        <el-form-item label="対象タイプ">
          <el-select v-model="filters.target_type" placeholder="選択" clearable style="width: 180px">
            <el-option label="Order Monthly" value="order_monthly" />
            <el-option label="Order Daily" value="order_daily" />
            <el-option label="System" value="system" />
          </el-select>
        </el-form-item>

        <el-form-item label="キーワード">
          <el-input v-model="filters.keyword" placeholder="メッセージ検索" clearable style="width: 250px" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="fetchList">検索</el-button>
          <el-button @click="resetFilter">リセット</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 📋 テーブル区域 -->
    <el-card class="log-table-card">
      <el-table :data="logList" :key="logList.length" stripe border v-loading="loading"
        @row-dblclick="handleRowDblClick">
        <el-table-column label="アクション" prop="action" width="100" align="center" />
        <el-table-column label="対象タイプ" prop="target_type" width="150" align="center" />
        <el-table-column label="対象ID" prop="target_id" width="180" />
        <el-table-column label="メッセージ" prop="message" />
        <el-table-column label="作成日時" prop="created_at" width="180" />
      </el-table>

      <!-- 📄 ページネーション -->
      <div class="pagination">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.pageSize"
          :total="pagination.total" layout="prev, pager, next, total" background @current-change="fetchList" />
      </div>
    </el-card>

    <!-- 🔥 ログ詳細ダイアログ -->
    <el-dialog v-model="detailDialogVisible" title="📋 ログ詳細" width="600px" destroy-on-close>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="アクション">{{ selectedLog?.action }}</el-descriptions-item>
        <el-descriptions-item label="対象タイプ">{{ selectedLog?.target_type }}</el-descriptions-item>
        <el-descriptions-item label="対象ID">{{ selectedLog?.target_id }}</el-descriptions-item>
        <el-descriptions-item label="メッセージ">{{ selectedLog?.message }}</el-descriptions-item>
        <el-descriptions-item label="作成日時">{{ selectedLog?.created_at }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailDialogVisible = false">閉じる</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { fetchLogs } from '@/api/order/order'; // ✅ 注意路径

const filters = ref({
  action: '',
  target_type: '',
  keyword: '',
});

interface LogItem {
  action: string
  target_type: string
  target_id: string
  message: string
  created_at: string
}

const logList = ref<LogItem[]>([]);
const loading = ref(false);
const pagination = ref({
  page: 1,
  pageSize: 20,
  total: 0,
});

// 🔥 详细Dialog控制
const detailDialogVisible = ref(false);
const selectedLog = ref<LogItem | null>(null);

// 🔥 双击一行打开详细Dialog
const handleRowDblClick = (row: LogItem) => {
  selectedLog.value = { ...row };
  detailDialogVisible.value = true;
};

// 🔥 数据取得
const fetchList = async () => {
  loading.value = true;
  try {
    const res = await fetchLogs({
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      ...filters.value,
    });
    logList.value = res.list || [];
    pagination.value.total = res.total || 0;
  } catch (error) {
    console.error('ログ一覧取得失敗', error);
  } finally {
    loading.value = false;
  }
};

// 🔄 リセット
const resetFilter = () => {
  filters.value = { action: '', target_type: '', keyword: '' };
  pagination.value.page = 1;
  fetchList();
};

onMounted(() => {
  fetchList();
});
</script>

<style scoped>
.order-log-page {
  padding: 20px;
}

.filter-form {
  margin-bottom: 20px;
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.log-table-card {
  margin-top: 10px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>
