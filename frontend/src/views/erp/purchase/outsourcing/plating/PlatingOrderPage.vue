<template>
  <div class="outsourcing-order-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h2 class="title">
            <div class="title-icon">
              <el-icon><Brush /></el-icon>
            </div>
            <span class="title-text">外注メッキ注文</span>
            <div class="title-badge">
              <span class="badge-text">{{ orderList.length }}</span>
            </div>
          </h2>
          <p class="subtitle">外注メッキ加工の注文作成・管理を行います</p>
        </div>
      </div>
    </div>

    <!-- 検索フィルター -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <!-- 期間フィルタ -->
        <div class="filter-group">
          <span class="filter-label">期間</span>
          <div class="date-filter-container">
            <el-date-picker
              v-model="filters.dateRange"
              type="daterange"
              range-separator="〜"
              start-placeholder="開始日"
              end-placeholder="終了日"
              value-format="YYYY-MM-DD"
              class="date-picker"
              @change="handleSearch"
            />
            <div class="date-quick-btns">
              <el-button size="small" @click="setDatePrev" class="quick-btn">
                <el-icon><ArrowLeft /></el-icon>
              </el-button>
              <el-button
                size="small"
                @click="setDateToday"
                type="primary"
                class="quick-btn today-btn"
              >
                今日
              </el-button>
              <el-button size="small" @click="setDateNext" class="quick-btn">
                <el-icon><ArrowRight /></el-icon>
              </el-button>
              <el-button size="small" @click="setDateThisMonth" class="quick-btn month-btn">
                今月
              </el-button>
            </div>
          </div>
        </div>

        <!-- 外注先フィルタ -->
        <div class="filter-group">
          <span class="filter-label">外注先</span>
          <el-select
            v-model="filters.supplier"
            placeholder="全て"
            clearable
            filterable
            class="supplier-select"
            @change="handleSearch"
          >
            <el-option
              v-for="s in supplierOptions"
              :key="s.value"
              :label="s.label"
              :value="s.value"
            />
          </el-select>
        </div>

        <!-- 製品フィルタ -->
        <div class="filter-group">
          <span class="filter-label">製品</span>
          <el-select
            v-model="filters.productName"
            placeholder="全て"
            clearable
            filterable
            class="product-select"
            @change="handleSearch"
          >
            <el-option v-for="name in productNameOptions" :key="name" :label="name" :value="name" />
          </el-select>
        </div>

        <!-- 状態フィルタ -->
        <div class="filter-group">
          <span class="filter-label">状態</span>
          <el-select
            v-model="filters.status"
            placeholder="全て"
            clearable
            class="status-select"
            @change="handleSearch"
          >
            <el-option label="未発注" value="未発注" />
            <el-option label="発注済" value="発注済" />
            <el-option label="一部受入" value="一部受入" />
            <el-option label="受入完" value="受入完" />
          </el-select>
        </div>

        <!-- リセットボタン -->
        <div class="filter-group filter-actions">
          <el-button @click="resetFilters" class="reset-btn">
            <el-icon><Refresh /></el-icon>
            リセット
          </el-button>
        </div>
      </el-form>
    </el-card>

    <!-- 操作按钮栏 -->
    <div class="action-bar">
      <div class="left-actions">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>新規注文
        </el-button>
        <el-button type="success" @click="openBatchCreateDialog">
          <el-icon><Plus /></el-icon>新規一括注文
        </el-button>
        <el-button type="primary" @click="handlePrintOrder" class="print-btn">
          <el-icon><Printer /></el-icon>注文書発行
        </el-button>
      </div>
      <div class="right-actions">
        <el-tag type="info" size="large">
          合計: {{ formatNumber(totalQuantity) }} 個 / {{ formatCurrency(totalAmount) }}
        </el-tag>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        ref="tableRef"
        :data="orderList"
        v-loading="loading"
        stripe
        border
        highlight-current-row
        class="data-table"
        size="small"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column prop="orderNo" label="注文番号" width="140" align="center" fixed="left">
          <template #default="{ row }">
            <el-link type="primary" @click="viewDetail(row)">{{ row.orderNo || '-' }}</el-link>
          </template>
        </el-table-column>
        <el-table-column prop="orderDate" label="注文日" width="90" align="center">
          <template #default="{ row }">
            {{ row.orderDate || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="supplier" label="外注先" width="140" align="center">
          <template #default="{ row }">
            <el-tag
              :type="getSupplierTagType(row.supplierCd || row.supplier) || undefined"
              :effect="'plain'"
              size="small"
              class="supplier-tag"
            >
              {{ row.supplier || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="productName" label="製品名" min-width="120" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.productName || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="content"
          label="内容"
          width="100"
          align="center"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ row.content || '-' }}
          </template>
        </el-table-column>
        <el-table-column
          prop="category"
          label="区分"
          width="110"
          align="center"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            {{ row.category || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="quantity" label="数量" width="70" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.quantity) }}
          </template>
        </el-table-column>
        <el-table-column prop="unitPrice" label="単価" width="70" align="right">
          <template #default="{ row }"> {{ formatCurrency(row.unitPrice) }} </template>
        </el-table-column>
        <el-table-column prop="amount" label="金額" width="90" align="center">
          <template #default="{ row }">
            <span class="amount-cell">{{ formatCurrency(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="deliveryDate" label="納期" width="90" align="center">
          <template #default="{ row }">
            {{ row.deliveryDate || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="receivedQty" label="入庫数" width="70" align="right">
          <template #default="{ row }">
            {{ formatNumber(row.receivedQty) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状態" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row)" size="small">
              {{ getStatusLabel(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="進捗" width="100" align="center">
          <template #default="{ row }">
            <el-progress
              :percentage="
                row.quantity > 0 ? Math.round(((row.receivedQty || 0) / row.quantity) * 100) : 0
              "
              :status="(row.receivedQty || 0) >= row.quantity ? 'success' : ''"
              :stroke-width="6"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" align="center" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button type="primary" size="small" @click="editOrder(row)" :icon="Edit" />
              <el-button type="info" size="small" @click="printOrder(row)" :icon="Printer" />
              <el-button type="danger" size="small" @click="deleteOrder(row)" :icon="Delete" />
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 新建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="900px"
      destroy-on-close
      class="order-dialog batch-dialog"
      :close-on-click-modal="false"
      center
    >
      <template #header>
        <div class="dialog-header compact-header">
          <el-icon class="dialog-icon">
            <Upload />
          </el-icon>
          <span class="dialog-title">{{ dialogTitle }}</span>
        </div>
      </template>
      <div class="batch-form-container">
        <div class="batch-form compact-form">
          <el-form :model="formData" label-width="70px" class="compact-form-inner">
            <div class="form-row-inline">
              <el-form-item label="外注先" class="inline-form-item flex-item">
                <el-select
                  v-model="formData.supplierCd"
                  filterable
                  placeholder="外注先を選択"
                  class="supplier-select"
                  clearable
                >
                  <el-option
                    v-for="s in supplierOptions"
                    :key="s.value"
                    :label="s.label"
                    :value="s.value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item class="inline-form-item button-item">
                <el-button
                  type="primary"
                  class="load-btn"
                  @click="fetchProducts"
                  :loading="productLoading"
                >
                  <el-icon>
                    <Download />
                  </el-icon>
                  読込
                </el-button>
              </el-form-item>
            </div>
            <div class="form-row-inline date-row">
              <el-form-item label="注文日" class="inline-form-item">
                <el-date-picker
                  v-model="formData.orderDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="注文日を選択"
                  class="date-select"
                  @change="calculateDeliveryDate"
                />
              </el-form-item>

              <el-form-item label="納期" class="inline-form-item delivery-date-item">
                <div class="delivery-date-wrapper">
                  <el-date-picker
                    v-model="formData.deliveryDate"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="納期を選択"
                    class="date-select"
                  />
                  <div v-if="productList.length > 0" class="delivery-date-hint-text">
                    納期が正しいかご確認ください
                  </div>
                </div>
              </el-form-item>
            </div>
          </el-form>

          <div class="table-container">
            <el-table
              v-if="productList.length > 0"
              :data="productList"
              class="batch-product-table"
              :loading="productLoading"
              border
              stripe
              highlight-current-row
              max-height="420"
              :row-style="{ height: '38px' }"
              size="small"
            >
              <el-table-column
                prop="productCd"
                label="製品CD"
                width="80"
                align="center"
                fixed="left"
              />
              <el-table-column
                prop="productName"
                label="製品名"
                min-width="120"
                show-overflow-tooltip
              />
              <!-- <el-table-column
                prop="specification"
                label="規格"
                width="120"
                show-overflow-tooltip
              /> -->
              <el-table-column prop="unitPrice" label="単価" width="70" align="center">
                <template #default="{ row }">
                  {{ formatCurrency(row.unitPrice) }}
                </template>
              </el-table-column>
              <el-table-column
                prop="deliveryLocation"
                label="納入場所"
                width="140"
                align="center"
                show-overflow-tooltip
              />
              <el-table-column prop="category" label="区分" width="130" align="center" />
              <el-table-column
                prop="content"
                label="内容"
                min-width="100"
                align="center"
                show-overflow-tooltip
              />
              <el-table-column label="数量" width="120" align="center" fixed="right">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="productList[$index].quantity"
                    type="text"
                    class="quantity-input"
                    :class="
                      (() => {
                        const qty = productList[$index].quantity
                        const numQty = typeof qty === 'number' ? qty : Number(qty || 0)
                        return numQty > 0 ? 'normal-cell' : 'warning-cell'
                      })()
                    "
                    placeholder="数量"
                    :id="`quantity-input-${$index}`"
                    @keydown.enter.prevent="handleQuantityEnter($index)"
                    @input="handleQuantityChange(row, $index)"
                  />
                </template>
              </el-table-column>
            </el-table>
            <div v-else-if="productLoading" class="loading-placeholder compact-placeholder">
              <el-icon class="is-loading">
                <Loading />
              </el-icon>
              <p>データ読込中...</p>
            </div>
            <div v-else-if="!formData.supplierCd" class="empty-placeholder compact-placeholder">
              <p>外注先を選択し、製品一覧を読み込んでください</p>
            </div>
            <div v-else class="empty-placeholder compact-placeholder">
              <p>製品データがありません</p>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="dialogVisible = false" class="cancel-btn">
            <el-icon>
              <Close />
            </el-icon>
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="submitForm"
            :loading="submitLoading"
            class="register-btn"
          >
            <el-icon v-if="!submitLoading">
              <Check />
            </el-icon>
            登録する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 新規一括注文对话框 -->
    <el-dialog
      v-model="batchDialogVisible"
      title="新規一括注文"
      width="1000px"
      destroy-on-close
      class="order-dialog batch-dialog"
      :close-on-click-modal="false"
      center
    >
      <template #header>
        <div class="dialog-header compact-header">
          <el-icon class="dialog-icon">
            <Upload />
          </el-icon>
          <span class="dialog-title">新規一括注文</span>
        </div>
      </template>
      <div class="batch-form-container">
        <div class="batch-form compact-form">
          <el-form :model="batchFormData" label-width="70px" class="compact-form-inner">
            <div class="form-row-inline">
              <el-form-item label="外注先" class="inline-form-item flex-item">
                <el-select
                  v-model="batchFormData.supplierCd"
                  filterable
                  placeholder="外注先を選択"
                  class="supplier-select"
                  clearable
                >
                  <el-option
                    v-for="s in supplierOptions"
                    :key="s.value"
                    :label="s.label"
                    :value="s.value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="製品" class="inline-form-item flex-item">
                <el-select
                  v-model="batchFormData.productCd"
                  filterable
                  placeholder="製品を選択"
                  class="supplier-select"
                  clearable
                  :disabled="!batchFormData.supplierCd"
                >
                  <el-option
                    v-for="p in batchProductOptions"
                    :key="p.productCd"
                    :label="`${p.productCd} - ${p.productName}`"
                    :value="p.productCd"
                  />
                </el-select>
              </el-form-item>

              <el-form-item class="inline-form-item button-item">
                <el-button
                  type="primary"
                  class="load-btn"
                  @click="fetchBatchProducts"
                  :loading="batchProductLoading"
                >
                  <el-icon>
                    <Download />
                  </el-icon>
                  読込
                </el-button>
              </el-form-item>
            </div>
            <div class="form-row-inline date-row">
              <el-form-item label="期間" class="inline-form-item">
                <el-date-picker
                  v-model="batchFormData.dateRange"
                  type="daterange"
                  range-separator="〜"
                  start-placeholder="開始日"
                  end-placeholder="終了日"
                  value-format="YYYY-MM-DD"
                  class="date-select"
                  style="width: 100%"
                />
              </el-form-item>
            </div>
          </el-form>

          <div class="table-container">
            <el-table
              v-if="batchOrderList.length > 0"
              :data="batchOrderList"
              class="batch-product-table"
              :loading="batchProductLoading"
              border
              stripe
              highlight-current-row
              max-height="450"
              :row-style="{ height: '40px' }"
              size="small"
            >
              <el-table-column
                prop="orderDate"
                label="注文日"
                width="100"
                align="center"
                fixed="left"
              />
              <el-table-column prop="productCd" label="製品CD" width="90" align="center" />
              <el-table-column
                prop="productName"
                label="製品名"
                min-width="130"
                show-overflow-tooltip
              />
              <el-table-column prop="unitPrice" label="単価" width="80" align="center">
                <template #default="{ row }">
                  {{ formatCurrency(row.unitPrice) }}
                </template>
              </el-table-column>
              <!-- <el-table-column
                prop="deliveryLocation"
                label="納入場所"
                width="140"
                show-overflow-tooltip
              /> -->
              <!-- <el-table-column prop="category" label="区分" width="100" align="center" /> -->
              <el-table-column prop="content" label="内容" min-width="100" show-overflow-tooltip />
              <el-table-column prop="deliveryDate" label="納期" width="130" align="center">
                <template #default="{ row }">
                  <el-date-picker
                    v-model="row.deliveryDate"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="納期"
                    size="small"
                    style="width: 100%"
                  />
                </template>
              </el-table-column>
              <el-table-column label="数量" width="120" align="center" fixed="right">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="batchOrderList[$index].quantity"
                    type="text"
                    class="quantity-input"
                    :class="
                      (() => {
                        const qty = batchOrderList[$index].quantity
                        const numQty = typeof qty === 'number' ? qty : Number(qty || 0)
                        return numQty > 0 ? 'normal-cell' : 'warning-cell'
                      })()
                    "
                    placeholder="数量"
                    :id="`batch-quantity-input-${$index}`"
                    @keydown.enter.prevent="handleBatchQuantityEnter($index)"
                    @input="handleBatchQuantityChange(row, $index)"
                  />
                </template>
              </el-table-column>
            </el-table>
            <div v-else-if="batchProductLoading" class="loading-placeholder compact-placeholder">
              <el-icon class="is-loading">
                <Loading />
              </el-icon>
              <p>データ読込中...</p>
            </div>
            <div
              v-else-if="
                !batchFormData.supplierCd ||
                !batchFormData.productCd ||
                !batchFormData.dateRange ||
                batchFormData.dateRange.length !== 2
              "
              class="empty-placeholder compact-placeholder"
            >
              <p>外注先、製品、期間を選択し、読込ボタンをクリックしてください</p>
            </div>
            <div v-else class="empty-placeholder compact-placeholder">
              <p>データがありません</p>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="batchDialogVisible = false" class="cancel-btn">
            <el-icon>
              <Close />
            </el-icon>
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="submitBatchForm"
            :loading="submitLoading"
            class="register-btn"
          >
            <el-icon v-if="!submitLoading">
              <Check />
            </el-icon>
            登録する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="注文詳細" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="注文番号">{{ detailData.orderNo }}</el-descriptions-item>
        <el-descriptions-item label="注文日">{{ detailData.orderDate }}</el-descriptions-item>
        <el-descriptions-item label="外注先">{{ detailData.supplier }}</el-descriptions-item>
        <el-descriptions-item label="品番">{{ detailData.productCode }}</el-descriptions-item>
        <el-descriptions-item label="品名" :span="2">{{
          detailData.productName
        }}</el-descriptions-item>
        <el-descriptions-item label="メッキ種類">{{ detailData.platingType }}</el-descriptions-item>
        <el-descriptions-item label="数量">{{
          formatNumber(detailData.quantity)
        }}</el-descriptions-item>
        <el-descriptions-item label="単価">
          {{ formatCurrency(detailData.unitPrice) }}
        </el-descriptions-item>
        <el-descriptions-item label="金額">
          {{ formatCurrency(detailData.amount) }}
        </el-descriptions-item>
        <el-descriptions-item label="納期">{{ detailData.deliveryDate }}</el-descriptions-item>
        <el-descriptions-item label="入庫数">{{
          formatNumber(detailData.receivedQty)
        }}</el-descriptions-item>
        <el-descriptions-item label="状態">
          <el-tag :type="getStatusType(detailData as OrderItem)">{{
            getStatusLabel(detailData as OrderItem)
          }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="備考" :span="2">{{
          detailData.remarks || '-'
        }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="注文編集"
      width="720px"
      destroy-on-close
      class="order-dialog edit-dialog-compact"
      :close-on-click-modal="false"
      center
    >
      <template #header>
        <div class="dialog-header compact-header">
          <el-icon class="dialog-icon">
            <EditPen />
          </el-icon>
          <span class="dialog-title">注文編集</span>
        </div>
      </template>
      <div class="edit-form-container">
        <el-form :model="editFormData" label-width="100px" class="edit-form-compact">
          <el-row :gutter="12">
            <el-col :span="24">
              <el-form-item label="注文番号" class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.orderNo"
                  disabled
                  class="edit-input-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="注文日" required class="edit-form-item-compact">
                <el-date-picker
                  v-model="editFormData.orderDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="注文日を選択"
                  class="edit-input-compact"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="納期" class="edit-form-item-compact">
                <el-date-picker
                  v-model="editFormData.deliveryDate"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="納期を選択"
                  class="edit-input-compact"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="24">
              <el-form-item label="外注先" required class="edit-form-item-compact">
                <el-select
                  v-model="editFormData.supplierCd"
                  filterable
                  placeholder="外注先を選択"
                  class="edit-input-compact"
                  size="small"
                  style="width: 100%"
                  clearable
                >
                  <el-option
                    v-for="s in supplierOptions"
                    :key="s.value"
                    :label="s.label"
                    :value="s.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="製品CD" required class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.productCode"
                  placeholder="製品CD"
                  class="edit-input-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="製品名" required class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.productName"
                  placeholder="製品名"
                  class="edit-input-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="数量" required class="edit-form-item-compact">
                <el-input-number
                  v-model="editFormData.quantity"
                  :min="0"
                  :precision="0"
                  class="edit-input-compact"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="単価" class="edit-form-item-compact">
                <el-input-number
                  v-model="editFormData.unitPrice"
                  :min="0"
                  :precision="2"
                  class="edit-input-compact"
                  size="small"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="12">
              <el-form-item label="納入場所" class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.deliveryLocation"
                  placeholder="納入場所"
                  class="edit-input-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="区分" class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.category"
                  placeholder="区分"
                  class="edit-input-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="24">
              <el-form-item label="状態" class="edit-form-item-compact">
                <el-select
                  v-model="editFormData.status"
                  class="edit-input-compact"
                  size="small"
                  style="width: 100%"
                  disabled
                >
                  <el-option label="未発注" value="未発注" />
                  <el-option label="発注済" value="発注済" />
                  <el-option label="一部受入" value="一部受入" />
                  <el-option label="受入完" value="受入完" />
                </el-select>
                <div style="font-size: 11px; color: #909399; margin-top: 4px">
                  状態は自動計算されます
                </div>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="24">
              <el-form-item label="内容" class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.content"
                  type="textarea"
                  :rows="2"
                  placeholder="内容"
                  class="edit-textarea-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="24">
              <el-form-item label="規格" class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.specification"
                  type="textarea"
                  :rows="2"
                  placeholder="規格"
                  class="edit-textarea-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="12">
            <el-col :span="24">
              <el-form-item label="備考" class="edit-form-item-compact">
                <el-input
                  v-model="editFormData.remarks"
                  type="textarea"
                  :rows="2"
                  placeholder="備考"
                  class="edit-textarea-compact"
                  size="small"
                />
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>
      <template #footer>
        <div class="dialog-footer-compact">
          <el-button @click="editDialogVisible = false" class="cancel-btn">
            <el-icon>
              <Close />
            </el-icon>
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="submitEditForm"
            :loading="submitLoading"
            class="register-btn"
          >
            <el-icon v-if="!submitLoading">
              <Check />
            </el-icon>
            更新する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 打印确认对话框 -->
    <el-dialog
      v-model="printConfirmDialogVisible"
      width="650px"
      :close-on-click-modal="false"
      :show-close="true"
      class="print-confirm-dialog"
    >
      <template #header>
        <div class="dialog-header-with-button">
          <span class="dialog-title">注文書印刷確認</span>
          <el-button type="primary" @click="confirmPrint" class="confirm-btn-header" size="small">
            <el-icon><Printer /></el-icon>
            印刷実行
          </el-button>
        </div>
      </template>
      <div class="print-confirm-content-compact">
        <div class="form-sections-compact">
          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><User /></el-icon>
              <span class="section-title">受注先情報</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">受注先会社名</label>
                <el-input
                  v-model="printForm.recipientCompany"
                  placeholder="外注先会社名 御中"
                  class="form-input-compact"
                  size="small"
                />
              </div>
            </div>
          </div>

          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><EditPen /></el-icon>
              <span class="section-title">承認・発行情報</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">承認者</label>
                <el-select
                  v-model="printForm.approver"
                  placeholder="承認者を選択"
                  class="form-input-compact"
                  size="small"
                  clearable
                  filterable
                >
                  <el-option
                    v-for="person in personOptions"
                    :key="person"
                    :label="person"
                    :value="person"
                  />
                </el-select>
              </div>
              <div class="form-field-row">
                <label class="field-label">発行者</label>
                <el-select
                  v-model="printForm.issuer"
                  placeholder="発行者を選択"
                  class="form-input-compact"
                  size="small"
                  clearable
                  filterable
                >
                  <el-option
                    v-for="person in personOptions"
                    :key="person"
                    :label="person"
                    :value="person"
                  />
                </el-select>
              </div>
            </div>
          </div>

          <div class="form-section-compact">
            <div class="section-header-compact">
              <el-icon class="section-icon"><Box /></el-icon>
              <span class="section-title">備考・注意事項</span>
            </div>
            <div class="form-fields-compact">
              <div class="form-field-row">
                <label class="field-label">備考1</label>
                <el-input
                  v-model="printForm.note1"
                  type="textarea"
                  :rows="2"
                  placeholder="1.納品書と請求書には必ずこの注文番号をご記入下さい。"
                  class="form-textarea-compact"
                  size="small"
                />
              </div>
              <div class="form-field-row">
                <label class="field-label">備考2</label>
                <el-input
                  v-model="printForm.note2"
                  type="textarea"
                  :rows="2"
                  placeholder="2.支払期日には法定税率による消費税額及び地方消費税分を加算して支払います。"
                  class="form-textarea-compact"
                  size="small"
                />
              </div>
              <div class="form-field-row">
                <label class="field-label">備考3</label>
                <el-input
                  v-model="printForm.note3"
                  type="textarea"
                  :rows="2"
                  placeholder="3.支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年1月1日の「支払方法等について」によります。"
                  class="form-textarea-compact"
                  size="small"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Plus,
  Download,
  Edit,
  Printer,
  Delete,
  Brush,
  Box,
  EditPen,
  Check,
  Upload,
  Close,
  Loading,
  Calendar,
  OfficeBuilding,
  CircleCheck,
  ArrowLeft,
  ArrowRight,
} from '@element-plus/icons-vue'
import {
  getPlatingOrders,
  createPlatingOrder,
  updatePlatingOrder,
  deletePlatingOrder,
  getPlatingOrdersByOrderNo,
  batchOrderPlating,
  type PlatingOrder,
  getProcessProducts,
  getDestinationHolidays,
} from '@/api/outsourcing'
import { getPrintHistory, recordPrintHistory } from '@/api/shipping/printHistory'
import { getSuppliers, type OutsourcingSupplier } from '@/api/outsourcing'
import request from '@/utils/request'

// 类型定义
interface OrderItem {
  id: number
  orderNo: string
  orderDate: string
  supplier: string
  supplierId?: number
  supplierCd?: string
  productCode: string
  productName: string
  platingType: string
  quantity: number
  unitPrice: number
  amount: number
  deliveryDate: string
  receivedQty: number
  status: string
  remarks?: string
  deliveryLocation?: string
  category?: string
  content?: string
  specification?: string
}

// 产品列表项（用于批量录入）
interface ProductListItem {
  productCd: string
  productName: string
  unitPrice: number
  deliveryLocation: string
  category: string
  content: string
  specification: string
  deliveryLeadTime: number
  quantity: string | number // 允许字符串输入
}

// 数据转换：后端snake_case -> 前端camelCase
const convertOrderFromBackend = (item: any): OrderItem => {
  return {
    id: item.id,
    orderNo: item.order_no || item.orderNo,
    orderDate: item.order_date || item.orderDate,
    supplier: item.supplier_name || item.supplier || '',
    supplierId: item.supplier_id || item.supplierId,
    supplierCd: item.supplier_cd || item.supplierCd,
    productCode: item.product_cd || item.productCode,
    productName: item.product_name || item.productName,
    platingType: item.plating_type || item.platingType,
    quantity: item.quantity || 0,
    unitPrice: Number(item.unit_price || item.unitPrice || 0),
    amount: Number(item.amount || 0),
    deliveryDate: item.delivery_date || item.deliveryDate,
    receivedQty: item.received_qty || item.receivedQty || 0,
    status: item.status || 'pending',
    remarks: item.remarks || '',
    deliveryLocation: item.delivery_location || item.deliveryLocation,
    category: item.category,
    content: item.content,
    specification: item.specification,
  }
}

// 数据转换：前端camelCase -> 后端snake_case
const convertOrderToBackend = (item: Partial<OrderItem>, includeStatus = false): any => {
  const data: any = {
    supplier_cd: item.supplierCd ?? undefined,
    order_date: item.orderDate,
    product_cd: item.productCode,
    product_name: item.productName,
    plating_type: item.platingType,
    quantity: item.quantity,
    unit: '個',
    unit_price: item.unitPrice,
    delivery_date: item.deliveryDate,
    delivery_location: item.deliveryLocation,
    category: item.category,
    content: item.content,
    specification: item.specification,
    remarks: item.remarks,
    created_by: 'system', // TODO: 从用户信息获取
  }

  // 更新时包含status字段
  if (includeStatus && item.status) {
    data.status = item.status
  }

  return data
}

// 状态
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const detailVisible = ref(false)
const editDialogVisible = ref(false)
const isEdit = ref(false)
const tableRef = ref()

// ==================== 日本时区工具函数 ====================
// 获取日本时区的当前日期（优化版本，性能更好）
const getJapanDate = (): Date => {
  const now = new Date()
  // 使用 Intl.DateTimeFormat 获取日本时区时间（比 toLocaleString 更高效）
  const formatter = new Intl.DateTimeFormat('ja-JP', {
    timeZone: 'Asia/Tokyo',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
  const parts = formatter.formatToParts(now)
  const year = parseInt(parts.find((p) => p.type === 'year')?.value || '0')
  const month = parseInt(parts.find((p) => p.type === 'month')?.value || '0') - 1
  const day = parseInt(parts.find((p) => p.type === 'day')?.value || '0')
  const hour = parseInt(parts.find((p) => p.type === 'hour')?.value || '0')
  const minute = parseInt(parts.find((p) => p.type === 'minute')?.value || '0')
  const second = parseInt(parts.find((p) => p.type === 'second')?.value || '0')
  return new Date(year, month, day, hour, minute, second)
}

// 格式化日期为 YYYY-MM-DD（日本时区）
const formatDate = (date: Date): string => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 日本数字格式化（统一使用 ja-JP locale）
const formatNumber = (value: number | null | undefined): string => {
  if (value == null || isNaN(value)) return '0'
  return value.toLocaleString('ja-JP')
}

// 日本货币格式化
const formatCurrency = (value: number | null | undefined): string => {
  if (value == null || isNaN(value)) return '¥0'
  return `¥${value.toLocaleString('ja-JP')}`
}

// 日本货币格式化（带小数）
const formatCurrencyDecimal = (value: number | null | undefined): string => {
  if (value == null || isNaN(value)) return '¥0.00'
  return `¥${value.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

// 获取当天的日期范围（开始和结束都是同一天）
const getTodayDateRange = (): string[] => {
  const today = getJapanDate()
  const dateStr = formatDate(today)
  return [dateStr, dateStr]
}

// 筛选条件
const filters = reactive({
  dateRange: getTodayDateRange(),
  supplier: '',
  productName: '',
  status: '',
})

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

// 表单数据
const formRef = ref()
const formData = reactive({
  supplierCd: undefined as string | undefined,
  orderDate: '',
  deliveryDate: '', // 納期（自动计算）
  remarks: '',
})

// 编辑表单数据
const editFormData = reactive({
  id: 0,
  orderNo: '',
  orderDate: '',
  supplierCd: '',
  productCode: '',
  productName: '',
  quantity: 0,
  unitPrice: 0,
  deliveryDate: '',
  deliveryLocation: '',
  category: '',
  content: '',
  specification: '',
  status: '',
  remarks: '',
})

// 产品名称选项列表
const productNameOptions = ref<string[]>([])

// 产品列表数据（用于批量录入）
const productList = ref<ProductListItem[]>([])

// 当前选中的外注先的delivery_lead_time（用于计算納期）
const currentSupplierLeadTime = ref<number>(7)

// 产品加载状态
const productLoading = ref(false)

// 一括注文相关
const batchDialogVisible = ref(false)
const batchProductLoading = ref(false)
const batchProductOptions = ref<Array<{ productCd: string; productName: string }>>([])
const batchOrderList = ref<
  Array<{
    orderDate: string
    productCd: string
    productName: string
    unitPrice: number
    deliveryLocation: string
    category: string
    content: string
    specification: string
    deliveryDate: string
    quantity: string | number
    deliveryLeadTime: number
  }>
>([])

const batchFormData = reactive({
  supplierCd: undefined as string | undefined,
  productCd: '',
  dateRange: [] as string[],
})

// 休息日列表（用于计算納期）
const holidayDates = ref<Set<string>>(new Set())

// 打印相关
const printConfirmDialogVisible = ref(false)
const currentPrintOrderItems = ref<OrderItem[]>([]) // 当前要打印的订单数据
// 记录已打印的订单号（使用 Set 存储 orderNo）
const printedOrderNos = ref<Set<string>>(new Set())
// 承認者・発行者选项
const personOptions = ['篠田', '小森', '趙', '青山', '孫', '竹村']
const printForm = reactive({
  recipientCompany: '',
  approver: '',
  issuer: '',
  note1: '1.納品書と請求書には必ずこの注文番号をご記入下さい。',
  note2: '2.支払期日には法定税率による消費税額及び地方消費税分を加算して支払います。',
  note3:
    '3.支払期日・支払方法・検査完了期日・有償支給原材料代金の決済期日及び方法については、令和8年1月1日の「支払方法等について」によります。',
})

const formRules = {
  supplierCd: [{ required: true, message: '外注先を選択してください', trigger: 'blur' }],
  orderDate: [{ required: true, message: '注文日を選択してください', trigger: 'change' }],
}

// 详情数据
const detailData = ref<Partial<OrderItem>>({})

// 数据列表
const orderList = ref<OrderItem[]>([])

// 外注先选项（value为supplier_cd）
const supplierOptions = ref<Array<{ value: string; label: string }>>([])

// 加载外注先列表
const loadSuppliers = async () => {
  try {
    const res = await getSuppliers({ type: 'メッキ', isActive: true })
    let suppliers: any[] = []

    if (Array.isArray(res)) {
      suppliers = res
    } else if (res?.data && Array.isArray(res.data)) {
      suppliers = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      suppliers = res.data
    }

    supplierOptions.value = suppliers.map((s) => {
      const supplierCd = s.supplier_cd || s.code || ''
      const supplierName = s.supplier_name || s.name || ''
      return {
        value: supplierCd,
        label: supplierCd ? `${supplierCd} - ${supplierName}` : supplierName,
      }
    })
  } catch (error) {
    console.error('外注先取得エラー:', error)
    ElMessage.error('外注先データの取得に失敗しました')
  }
}

// 加载产品名称列表
const loadProductNames = async () => {
  try {
    const res = await request.get('/api/outsourcing/plating/receivings/products')
    if (res?.success && Array.isArray(res.data)) {
      productNameOptions.value = res.data
    } else if (Array.isArray(res)) {
      productNameOptions.value = res
    }
  } catch (error) {
    console.error('製品名一覧取得エラー:', error)
  }
}

// 计算属性
const totalQuantity = computed(() => orderList.value.reduce((sum, item) => sum + item.quantity, 0))
const totalAmount = computed(() => orderList.value.reduce((sum, item) => sum + item.amount, 0))
const dialogTitle = computed(() => (isEdit.value ? '注文編集' : '新規注文'))

// 根据订单状态计算显示状态
const calculateStatus = (row: OrderItem): string => {
  const isPrinted = printedOrderNos.value.has(row.orderNo)
  const receivedQty = row.receivedQty || 0
  const quantity = row.quantity || 0

  // 如果没有打印过，显示'未発注'
  if (!isPrinted) {
    return '未発注'
  }

  // 如果已打印过，根据入庫数判断
  if (receivedQty === 0) {
    return '発注済'
  } else if (receivedQty === quantity) {
    return '受入完'
  } else if (receivedQty > 0 && receivedQty < quantity) {
    return '一部受入'
  } else {
    return '発注済'
  }
}

// 方法
const getStatusType = (row: OrderItem): 'success' | 'info' | 'warning' | 'primary' | 'danger' => {
  const status = calculateStatus(row)
  const types: Record<string, 'success' | 'info' | 'warning' | 'primary' | 'danger'> = {
    未発注: 'info',
    発注済: 'warning',
    一部受入: 'primary',
    受入完: 'success',
  }
  return types[status] || 'info'
}

const getStatusLabel = (row: OrderItem) => {
  return calculateStatus(row)
}

// 根据外注先代码生成标签类型（用于颜色区分）
const getSupplierTagType = (
  supplierCd: string | undefined,
): 'success' | 'info' | 'warning' | 'danger' | 'primary' | undefined => {
  if (!supplierCd) return undefined

  // 使用哈希函数为不同的外注先分配颜色
  const hash = supplierCd.split('').reduce((acc, char) => {
    return char.charCodeAt(0) + ((acc << 5) - acc)
  }, 0)

  // 根据哈希值分配不同的标签类型
  const types: Array<'success' | 'info' | 'warning' | 'danger' | 'primary'> = [
    'success',
    'info',
    'warning',
    'danger',
    'primary',
  ]
  const index = Math.abs(hash) % types.length
  return types[index]
}

// 读取已打印记录，保持刷新后状态
const loadPrintedOrderNos = async () => {
  try {
    const res = await getPrintHistory({
      report_type: 'plating_order',
      page: 1,
      limit: 500,
    })

    // 兼容不同返回结构
    const extractList = (r: any): any[] => {
      if (!r) return []
      // axios封装一般返回 data
      const d = r.data ?? r
      if (Array.isArray(d)) return d
      if (Array.isArray(d.list)) return d.list
      if (d.data) {
        if (Array.isArray(d.data)) return d.data
        if (Array.isArray(d.data.list)) return d.data.list
      }
      return []
    }

    const list = extractList(res)

    const set = new Set<string>()
    list.forEach((item) => {
      if (!item?.filters) return
      try {
        const filters = typeof item.filters === 'string' ? JSON.parse(item.filters) : item.filters
        let orderNos: string[] = []
        if (Array.isArray(filters?.orderNos)) {
          orderNos = filters.orderNos
        } else if (typeof filters?.orderNo === 'string') {
          orderNos = [filters.orderNo]
        }
        orderNos.forEach((no) => {
          if (no) set.add(String(no))
        })
      } catch (e) {
        console.warn('print_history filters 解析失败', e)
      }
    })

    printedOrderNos.value = set
  } catch (error) {
    console.error('打印履历取得エラー:', error)
    // 获取失败时不阻断页面
  }
}

const handleSearch = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize,
    }

    if (filters.dateRange && filters.dateRange.length === 2) {
      params.startDate = filters.dateRange[0]
      params.endDate = filters.dateRange[1]
    }

    if (filters.supplier) {
      params.supplierCd = filters.supplier
    }

    if (filters.productName) {
      params.productName = filters.productName
    }

    // 注意：状态筛选在前端进行，因为状态是根据是否打印和入庫数计算的
    // 不向后端传递状态筛选参数

    const res = await getPlatingOrders(params)

    // レスポンス構造の確認と処理
    let responseData: any = null
    if (res?.success !== undefined) {
      responseData = res
    } else if (res?.data) {
      responseData = res
    } else if (Array.isArray(res)) {
      responseData = { success: true, data: res, total: res.length }
    }

    if (responseData?.success) {
      const data = responseData.data || []
      orderList.value = data.map(convertOrderFromBackend)

      // 如果筛选条件中有状态，需要根据计算的状态进行过滤
      if (filters.status) {
        orderList.value = orderList.value.filter((item) => {
          const status = calculateStatus(item)
          return status === filters.status
        })
        // 更新总数（筛选后的数量）
        pagination.total = orderList.value.length
      } else {
        if (responseData.total !== undefined) {
          pagination.total = responseData.total
        } else {
          pagination.total = orderList.value.length
        }
      }
    } else {
      orderList.value = []
      pagination.total = 0
    }
  } catch (error) {
    console.error('データ取得エラー:', error)
    ElMessage.error('データの取得に失敗しました')
    orderList.value = []
    pagination.total = 0
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.dateRange = getTodayDateRange()
  filters.supplier = ''
  filters.productName = ''
  filters.status = ''
  handleSearch()
}

// 日期快捷操作方法
const setDateToday = () => {
  const today = formatDate(getJapanDate())
  filters.dateRange = [today, today]
  handleSearch()
}

const setDatePrev = () => {
  if (filters.dateRange && filters.dateRange.length === 2) {
    const start = new Date(filters.dateRange[0])
    const end = new Date(filters.dateRange[1])
    start.setDate(start.getDate() - 1)
    end.setDate(end.getDate() - 1)
    filters.dateRange = [formatDate(start), formatDate(end)]
  } else {
    const yesterday = new Date(getJapanDate())
    yesterday.setDate(yesterday.getDate() - 1)
    filters.dateRange = [formatDate(yesterday), formatDate(yesterday)]
  }
  handleSearch()
}

const setDateNext = () => {
  if (filters.dateRange && filters.dateRange.length === 2) {
    const start = new Date(filters.dateRange[0])
    const end = new Date(filters.dateRange[1])
    start.setDate(start.getDate() + 1)
    end.setDate(end.getDate() + 1)
    filters.dateRange = [formatDate(start), formatDate(end)]
  } else {
    const tomorrow = new Date(getJapanDate())
    tomorrow.setDate(tomorrow.getDate() + 1)
    filters.dateRange = [formatDate(tomorrow), formatDate(tomorrow)]
  }
  handleSearch()
}

const setDateThisMonth = () => {
  const now = getJapanDate()
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0)
  filters.dateRange = [formatDate(firstDay), formatDate(lastDay)]
  handleSearch()
}

// 防抖搜索定时器
let searchTimer: ReturnType<typeof setTimeout> | null = null

// 防抖搜索函数
const debouncedSearch = () => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
  searchTimer = setTimeout(() => {
    handleSearch()
  }, 300)
}

const openCreateDialog = () => {
  isEdit.value = false
  currentEditId.value = undefined
  Object.assign(formData, {
    supplierCd: undefined,
    orderDate: new Date().toISOString().split('T')[0],
    deliveryDate: '',
    remarks: '',
  })
  // 清空产品列表
  productList.value = []
  currentSupplierLeadTime.value = 7
  productLoading.value = false
  dialogVisible.value = true
}

// 打开一括注文对话框
const openBatchCreateDialog = () => {
  Object.assign(batchFormData, {
    supplierCd: undefined,
    productCd: '',
    dateRange: [],
  })
  batchProductOptions.value = []
  batchOrderList.value = []
  batchDialogVisible.value = true
}

// 加载一括注文的产品选项
const loadBatchProductOptions = async () => {
  if (!batchFormData.supplierCd) {
    batchProductOptions.value = []
    batchFormData.productCd = ''
    return
  }

  try {
    const res = await getProcessProducts({
      processType: 'plating',
      supplierCd: batchFormData.supplierCd,
      isActive: true,
    })

    let products: any[] = []
    if (Array.isArray(res)) {
      products = res
    } else if (res?.data && Array.isArray(res.data)) {
      products = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      products = res.data
    } else if (res?.success && res?.data && Array.isArray(res.data)) {
      products = res.data
    }

    batchProductOptions.value = products
      .sort((a: any, b: any) => (a.product_name || '').localeCompare(b.product_name || ''))
      .map((p) => ({
        productCd: p.product_cd || p.productCode || '',
        productName: p.product_name || p.productName || '',
      }))
  } catch (error) {
    console.error('製品取得エラー:', error)
    ElMessage.error('製品データの取得に失敗しました')
    batchProductOptions.value = []
  }
}

// 监听外注先变化，加载产品选项
watch(
  () => batchFormData.supplierCd,
  () => {
    if (batchFormData.supplierCd) {
      loadBatchProductOptions()
    } else {
      batchProductOptions.value = []
      batchFormData.productCd = ''
    }
  },
)

// 一括注文：読込按钮处理
const fetchBatchProducts = async () => {
  if (!batchFormData.supplierCd) {
    ElMessage.warning('外注先を選択してください')
    return
  }

  if (!batchFormData.productCd) {
    ElMessage.warning('製品を選択してください')
    return
  }

  if (!batchFormData.dateRange || batchFormData.dateRange.length !== 2) {
    ElMessage.warning('期間を選択してください')
    return
  }

  batchProductLoading.value = true
  try {
    // 获取选中产品的详细信息
    const res = await getProcessProducts({
      processType: 'plating',
      supplierCd: batchFormData.supplierCd,
      isActive: true,
    })

    let products: any[] = []
    if (Array.isArray(res)) {
      products = res
    } else if (res?.data && Array.isArray(res.data)) {
      products = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      products = res.data
    } else if (res?.success && res?.data && Array.isArray(res.data)) {
      products = res.data
    }

    const selectedProduct = products.find(
      (p) => (p.product_cd || p.productCode) === batchFormData.productCd,
    )

    if (!selectedProduct) {
      ElMessage.warning('選択した製品が見つかりません')
      batchOrderList.value = []
      return
    }

    // 生成期间内的日期列表
    const startDate = new Date(batchFormData.dateRange[0])
    const endDate = new Date(batchFormData.dateRange[1])
    const dateList: string[] = []

    // 生成日期列表（包括开始和结束日期）
    const currentDate = new Date(startDate)
    while (currentDate <= endDate) {
      const dateStr = formatDate(currentDate)
      dateList.push(dateStr)
      currentDate.setDate(currentDate.getDate() + 1)
    }

    // 计算默认納期（注文日 + lead_time 工作日）
    const deliveryLeadTime = Number(
      selectedProduct.delivery_lead_time || selectedProduct.deliveryLeadTime || 7,
    )

    // 为每个日期生成一条订单记录
    batchOrderList.value = dateList.map((orderDate) => {
      // 计算納期（注文日 + lead_time 工作日）
      const deliveryDate = addBusinessDays(orderDate, deliveryLeadTime)

      return {
        orderDate,
        productCd: selectedProduct.product_cd || selectedProduct.productCode || '',
        productName: selectedProduct.product_name || selectedProduct.productName || '',
        unitPrice: Number(selectedProduct.unit_price || selectedProduct.unitPrice || 0),
        deliveryLocation:
          selectedProduct.delivery_location || selectedProduct.deliveryLocation || '',
        category: selectedProduct.category || '',
        content: selectedProduct.content || '',
        specification: selectedProduct.specification || '',
        deliveryDate,
        quantity: '',
        deliveryLeadTime,
      }
    })

    ElMessage.success(`${batchOrderList.value.length}件の注文データを生成しました`)
  } catch (error) {
    console.error('一括注文データ生成エラー:', error)
    ElMessage.error('一括注文データの生成に失敗しました')
    batchOrderList.value = []
  } finally {
    batchProductLoading.value = false
  }
}

// 一括注文：数量输入框回车处理
const handleBatchQuantityEnter = (index: number) => {
  if (index < batchOrderList.value.length - 1) {
    nextTick(() => {
      const nextInput = document.querySelector(`#batch-quantity-input-${index + 1}`) as HTMLElement
      if (nextInput) {
        nextInput.focus()
      }
    })
  }
}

// 一括注文：数量变化处理
const handleBatchQuantityChange = (row: any, index: number) => {
  const value = row.quantity
  if (value === '' || value === null || value === undefined) {
    batchOrderList.value[index].quantity = ''
    return
  }
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue) || numValue < 0) {
    batchOrderList.value[index].quantity = ''
  } else {
    batchOrderList.value[index].quantity = numValue
  }
}

// 一括注文：提交表单
const submitBatchForm = async () => {
  if (
    !batchFormData.supplierCd ||
    !batchFormData.productCd ||
    !batchFormData.dateRange ||
    batchFormData.dateRange.length !== 2
  ) {
    ElMessage.warning('外注先、製品、期間を入力してください')
    return
  }

  if (batchOrderList.value.length === 0) {
    ElMessage.warning('注文データを生成してください')
    return
  }

  // 过滤出数量>0的订单
  const validOrders = batchOrderList.value.filter((o) => {
    const quantity = typeof o.quantity === 'string' ? parseFloat(o.quantity) : o.quantity
    return !isNaN(quantity) && quantity > 0
  })

  if (validOrders.length === 0) {
    ElMessage.warning('数量を入力した注文がありません')
    return
  }

  submitLoading.value = true
  try {
    const safeValue = <T,>(value: T | null | undefined): T | undefined => {
      return value === null ? undefined : value
    }

    // 批量创建订单
    const orderDataList = validOrders.map((order) => {
      const quantity =
        typeof order.quantity === 'string' ? parseFloat(order.quantity) : order.quantity
      return {
        supplier_cd: batchFormData.supplierCd,
        order_date: order.orderDate,
        product_cd: order.productCd,
        product_name: order.productName,
        plating_type: 'メッキ',
        quantity: isNaN(quantity) ? 0 : quantity,
        unit: '個',
        unit_price: order.unitPrice,
        delivery_date: order.deliveryDate || null,
        delivery_location: safeValue(order.deliveryLocation || null),
        category: safeValue(order.category || null),
        content: safeValue(order.content || null),
        specification: safeValue(order.specification || null),
        remarks: null,
        created_by: 'system',
      }
    })

    // 批量创建订单
    for (const orderData of orderDataList) {
      await createPlatingOrder(orderData as any)
    }

    ElMessage.success(`${orderDataList.length}件の注文を登録しました`)

    // 关闭对话框并刷新列表
    batchOrderList.value = []
    batchDialogVisible.value = false
    handleSearch()
  } catch (error: any) {
    console.error('一括登録エラー:', error)
    const errorMsg = error?.response?.data?.message || error?.message || 'エラーが発生しました'
    ElMessage.error(errorMsg)
  } finally {
    submitLoading.value = false
  }
}

// 当前编辑的订单ID
const currentEditId = ref<number | undefined>(undefined)

const editOrder = async (row: OrderItem) => {
  try {
    loading.value = true
    // 通过注文番号查找所属的数据
    const res = await getPlatingOrdersByOrderNo(row.orderNo)

    let orders: any[] = []
    if (Array.isArray(res)) {
      orders = res
    } else if (res?.data && Array.isArray(res.data)) {
      orders = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      orders = res.data
    }

    if (orders.length === 0) {
      ElMessage.warning('注文データが見つかりません')
      return
    }

    // 使用第一条记录填充编辑表单（如果有多条，可以后续扩展为列表编辑）
    const order = convertOrderFromBackend(orders[0])

    Object.assign(editFormData, {
      id: order.id,
      orderNo: order.orderNo,
      orderDate: order.orderDate,
      supplierCd: order.supplierCd || '',
      productCode: order.productCode,
      productName: order.productName,
      quantity: order.quantity,
      unitPrice: order.unitPrice,
      deliveryDate: order.deliveryDate,
      deliveryLocation: order.deliveryLocation || '',
      category: order.category || '',
      content: order.content || '',
      specification: order.specification || '',
      status: order.status,
      remarks: order.remarks || '',
    })

    editDialogVisible.value = true
  } catch (error: any) {
    console.error('注文取得エラー:', error)
    ElMessage.error('注文データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

const viewDetail = (row: OrderItem) => {
  detailData.value = row
  detailVisible.value = true
}

// 加载休息日列表
const loadHolidays = async (destinationCd?: string) => {
  try {
    const res = await getDestinationHolidays(destinationCd)
    let holidays: any[] = []

    if (Array.isArray(res)) {
      holidays = res
    } else if (res?.data && Array.isArray(res.data)) {
      holidays = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      holidays = res.data
    }

    // 将休息日转换为 Set，方便快速查找
    holidayDates.value = new Set(
      holidays.map((h) => {
        const date = h.holiday_date || h.holidayDate
        return typeof date === 'string' ? date.split('T')[0] : date
      }),
    )
  } catch (error) {
    console.error('休息日取得エラー:', error)
    // 失败时不影响主流程，只是不排除休息日
    holidayDates.value = new Set()
  }
}

// 计算工作日（排除周末和休息日）
const addBusinessDays = (startDate: string, days: number): string => {
  if (!startDate || days <= 0) return ''

  const date = new Date(startDate)
  let addedDays = 0
  let currentDate = new Date(date)

  while (addedDays < days) {
    currentDate.setDate(currentDate.getDate() + 1)
    const dayOfWeek = currentDate.getDay()
    const dateStr = currentDate.toISOString().split('T')[0]

    // 排除周末（0 = 周日, 6 = 周六）
    // 排除休息日（destination_holidays 表中的日期）
    if (dayOfWeek !== 0 && dayOfWeek !== 6 && !holidayDates.value.has(dateStr)) {
      addedDays++
    }
  }

  return currentDate.toISOString().split('T')[0]
}

// 计算納期
const calculateDeliveryDate = () => {
  if (!formData.orderDate || !currentSupplierLeadTime.value) {
    formData.deliveryDate = ''
    return
  }

  formData.deliveryDate = addBusinessDays(formData.orderDate, currentSupplierLeadTime.value)
}

// 読込按钮：加载产品列表
const fetchProducts = async () => {
  if (!formData.supplierCd) {
    ElMessage.warning('外注先を選択してください')
    return
  }

  if (!formData.orderDate) {
    ElMessage.warning('注文日を選択してください')
    return
  }

  productLoading.value = true
  try {
    // 从 outsourcing_process_products 表获取该外注先的产品
    const res = await getProcessProducts({
      processType: 'plating',
      supplierCd: formData.supplierCd,
      isActive: true,
    })

    let products: any[] = []
    if (Array.isArray(res)) {
      products = res
    } else if (res?.data && Array.isArray(res.data)) {
      products = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      products = res.data
    } else if (res?.success && res?.data && Array.isArray(res.data)) {
      products = res.data
    }

    if (products.length === 0) {
      ElMessage.warning('対象製品が存在しません')
      productList.value = []
      return
    }

    // 转换为产品列表格式
    productList.value = products
      .sort((a: any, b: any) => (a.product_name || '').localeCompare(b.product_name || ''))
      .map((p) => ({
        productCd: p.product_cd || p.productCode || '',
        productName: p.product_name || p.productName || '',
        unitPrice: Number(p.unit_price || p.unitPrice || 0),
        deliveryLocation: p.delivery_location || p.deliveryLocation || '',
        category: p.category || '',
        content: p.content || '',
        specification: p.specification || '',
        deliveryLeadTime: Number(p.delivery_lead_time || p.deliveryLeadTime || 7),
        quantity: '',
      }))

    // 设置默认的delivery_lead_time（取平均值）
    if (productList.value.length > 0) {
      const leadTimes = productList.value.map((p) => p.deliveryLeadTime).filter((lt) => lt > 0)
      if (leadTimes.length > 0) {
        currentSupplierLeadTime.value = Math.round(
          leadTimes.reduce((sum, lt) => sum + lt, 0) / leadTimes.length,
        )
      }
    }

    // 重新计算納期
    calculateDeliveryDate()

    ElMessage.success(`${productList.value.length}件の製品データを取得しました`)
  } catch (error) {
    console.error('製品取得エラー:', error)
    ElMessage.error('製品データの取得に失敗しました')
    productList.value = []
  } finally {
    productLoading.value = false
  }
}

// 数量输入框回车处理
const handleQuantityEnter = (index: number) => {
  if (index < productList.value.length - 1) {
    // 移动到下一个输入框
    nextTick(() => {
      const nextInput = document.querySelector(`#quantity-input-${index + 1}`) as HTMLElement
      if (nextInput) {
        nextInput.focus()
      }
    })
  }
}

// 数量变化处理
const handleQuantityChange = (row: ProductListItem, index: number) => {
  // 确保数量是数字或空字符串
  const value = row.quantity
  if (value === '' || value === null || value === undefined) {
    productList.value[index].quantity = ''
    return
  }
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue) || numValue < 0) {
    productList.value[index].quantity = ''
  } else {
    productList.value[index].quantity = numValue
  }
}

const submitForm = async () => {
  if (!formData.supplierCd || !formData.orderDate) {
    ElMessage.warning('外注先と注文日を入力してください')
    return
  }

  if (productList.value.length === 0) {
    ElMessage.warning('製品一覧を読み込んでください')
    return
  }

  // 过滤出数量>0的产品（数量处理：空字符串、null、undefined转换为0）
  const validProducts = productList.value.filter((p) => {
    const quantity = typeof p.quantity === 'string' ? parseFloat(p.quantity) : p.quantity
    return !isNaN(quantity) && quantity > 0
  })

  if (validProducts.length === 0) {
    ElMessage.warning('数量を入力した製品がありません')
    return
  }

  submitLoading.value = true
  try {
    // 批量创建订单
    const orderDataList = validProducts.map((product) => {
      const quantity =
        typeof product.quantity === 'string' ? parseFloat(product.quantity) : product.quantity
      // 将 null 转换为 undefined 以符合类型要求
      const safeValue = <T,>(value: T | null | undefined): T | undefined => {
        return value === null ? undefined : value
      }
      return {
        supplier_cd: formData.supplierCd,
        order_date: formData.orderDate,
        product_cd: product.productCd,
        product_name: product.productName,
        plating_type: 'メッキ',
        quantity: isNaN(quantity) ? 0 : quantity,
        unit: '個',
        unit_price: product.unitPrice,
        delivery_date: formData.deliveryDate,
        delivery_location: safeValue(product.deliveryLocation || null),
        category: safeValue(product.category || null),
        content: safeValue(product.content || null),
        specification: safeValue(product.specification || null),
        remarks: safeValue(formData.remarks || null),
        created_by: 'system',
      }
    })

    // 批量创建订单
    for (const orderData of orderDataList) {
      // 使用类型断言，因为后端接收的是 snake_case 格式
      await createPlatingOrder(orderData as any)
    }

    ElMessage.success(`${orderDataList.length}件の注文を登録しました`)

    // 关闭对话框并刷新列表
    productList.value = []
    dialogVisible.value = false
    currentEditId.value = undefined
    handleSearch()
  } catch (error: any) {
    console.error('登録エラー:', error)
    const errorMsg = error?.response?.data?.message || error?.message || 'エラーが発生しました'
    ElMessage.error(errorMsg)
  } finally {
    submitLoading.value = false
  }
}

const deleteOrder = async (row: OrderItem) => {
  try {
    await ElMessageBox.confirm('この注文を削除しますか？', '確認', { type: 'warning' })

    await deletePlatingOrder(row.id)
    ElMessage.success('削除しました')
    handleSearch()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('削除エラー:', error)
      const errorMsg = error?.response?.data?.message || error?.message || '削除に失敗しました'
      ElMessage.error(errorMsg)
    }
  }
}

// 提交编辑表单
const submitEditForm = async () => {
  if (!editFormData.orderDate || !editFormData.supplierCd || !editFormData.productCode) {
    ElMessage.warning('必須項目を入力してください')
    return
  }

  submitLoading.value = true
  try {
    const safeValue = <T,>(value: T | null | undefined): T | undefined => {
      return value === null ? undefined : value
    }

    const updateData = {
      order_date: editFormData.orderDate,
      supplier_cd: editFormData.supplierCd,
      product_cd: editFormData.productCode,
      product_name: editFormData.productName,
      quantity: editFormData.quantity,
      unit_price: editFormData.unitPrice,
      delivery_date: editFormData.deliveryDate || null,
      delivery_location: safeValue(editFormData.deliveryLocation || null),
      category: safeValue(editFormData.category || null),
      content: safeValue(editFormData.content || null),
      specification: safeValue(editFormData.specification || null),
      status: editFormData.status,
      remarks: safeValue(editFormData.remarks || null),
    }

    await updatePlatingOrder(editFormData.id, updateData as any)
    ElMessage.success('注文を更新しました')
    editDialogVisible.value = false
    handleSearch()
  } catch (error: any) {
    console.error('更新エラー:', error)
    const errorMsg = error?.response?.data?.message || error?.message || '更新に失敗しました'
    ElMessage.error(errorMsg)
  } finally {
    submitLoading.value = false
  }
}

// 操作列中的打印按钮处理（单个订单）
const printOrder = async (row: OrderItem) => {
  try {
    // 通过注文番号查找所属的数据
    const res = await getPlatingOrdersByOrderNo(row.orderNo)

    let orders: any[] = []
    if (Array.isArray(res)) {
      orders = res
    } else if (res?.data && Array.isArray(res.data)) {
      orders = res.data
    } else if (res?.success && Array.isArray(res.data)) {
      orders = res.data
    }

    if (orders.length === 0) {
      ElMessage.warning('注文データが見つかりません')
      return
    }

    // 转换为 OrderItem 格式
    const orderItems = orders.map(convertOrderFromBackend).filter((item) => item.quantity > 0)

    if (orderItems.length === 0) {
      ElMessage.warning('注文データがありません')
      return
    }

    // 设置外注先信息
    if (orderItems[0].supplier) {
      printForm.recipientCompany = `${orderItems[0].supplier} 御中`
    } else {
      // 如果没有供应商名称，尝试从 supplierOptions 中查找
      const supplierCd = orderItems[0].supplierCd || row.supplierCd
      if (supplierCd) {
        const selectedSupplier = supplierOptions.value.find((s) => s.value === supplierCd)
        if (selectedSupplier) {
          const supplierName = selectedSupplier.label.includes(' - ')
            ? selectedSupplier.label.split(' - ')[1]
            : selectedSupplier.label
          printForm.recipientCompany = `${supplierName} 御中`
        }
      }
    }

    // 设置默认值
    printForm.approver = '小森' // 承認者默认'小森'
    printForm.issuer = '竹村' // 発行者默认'竹村'

    // 临时存储当前要打印的订单数据（用于 confirmPrint 函数）
    currentPrintOrderItems.value = orderItems

    // 显示打印确认对话框
    printConfirmDialogVisible.value = true
  } catch (error: any) {
    console.error('注文取得エラー:', error)
    ElMessage.error('注文データの取得に失敗しました')
  }
}

// 注文書発行处理（批量打印）
const handlePrintOrder = async () => {
  // 检查外注先下拉框里有没有数据
  if (!supplierOptions.value || supplierOptions.value.length === 0) {
    ElMessage.warning('外注先データがありません。先に外注先データを読み込んでください。')
    return
  }

  // 检查是否有选择日期
  if (!filters.dateRange || filters.dateRange.length === 0) {
    ElMessage.warning('期間を選択してください')
    return
  }

  // 检查是否有注文数据
  const orderItems = orderList.value.filter((item) => item.quantity > 0)
  if (orderItems.length === 0) {
    ElMessage.warning('注文データがありません')
    return
  }

  // 从筛选条件中获取外注先信息
  if (filters.supplier) {
    const selectedSupplier = supplierOptions.value.find((s) => s.value === filters.supplier)
    if (selectedSupplier) {
      // 提取外注先名称（去掉代码部分）
      const supplierName = selectedSupplier.label.includes(' - ')
        ? selectedSupplier.label.split(' - ')[1]
        : selectedSupplier.label
      printForm.recipientCompany = `${supplierName} 御中`
    }
  } else {
    // 如果没有筛选外注先，从注文数据中获取（取第一个）
    if (orderItems.length > 0 && orderItems[0].supplier) {
      printForm.recipientCompany = `${orderItems[0].supplier} 御中`
    }
  }

  // 设置默认值
  printForm.approver = '小森' // 承認者默认'小森'
  printForm.issuer = '竹村' // 発行者默认'竹村'

  // 存储当前要打印的订单数据
  currentPrintOrderItems.value = orderItems

  // 显示打印确认对话框
  printConfirmDialogVisible.value = true
}

// 确认打印
const confirmPrint = async () => {
  try {
    // 获取注文数据（优先使用 currentPrintOrderItems，否则使用筛选后的列表）
    const orderItems =
      currentPrintOrderItems.value.length > 0
        ? currentPrintOrderItems.value
        : orderList.value.filter((item) => item.quantity > 0)

    if (orderItems.length === 0) {
      ElMessage.warning('注文データがありません')
      return
    }

    // 记录已打印的订单号
    orderItems.forEach((item) => {
      if (item.orderNo) {
        printedOrderNos.value.add(item.orderNo)
      }
    })

    // 更新订单状态为'発注済'（ordered）
    try {
      const orderIds = orderItems
        .map((item) => item.id)
        .filter((id) => id !== undefined && id !== null) as number[]

      if (orderIds.length > 0) {
        await batchOrderPlating(orderIds)
      }
    } catch (err) {
      console.error('订单状态更新失败:', err)
      ElMessage.warning('注文状態の更新に失敗しましたが、印刷は続行します')
      // 失败时不阻断打印流程
    }

    // 保存打印履历（不中断主流程）
    try {
      const filtersPayload = {
        dateRange: filters.dateRange,
        supplier: filters.supplier,
        productName: filters.productName,
        status: filters.status,
        orderNos: orderItems.map((o) => o.orderNo).filter(Boolean),
      }

      await recordPrintHistory({
        report_type: 'plating_order',
        report_title: '外注メッキ注文書',
        filters: filtersPayload,
        record_count: orderItems.length,
        status: '成功',
      })
    } catch (err) {
      console.error('打印履历保存失败:', err)
      // 失败时不阻断打印流程
    }

    // 显示加载状态
    ElMessage.info('印刷プレビューを生成中...')

    // 生成打印内容
    const printContent = generatePrintHtml(orderItems)
    const printWindow = window.open('', '_blank')
    if (printWindow) {
      printWindow.document.write(`
        <html>
        <head>
          <title>注文書</title>
          <meta charset="UTF-8">
          <style>
            body {
              font-family: 'Meiryo', 'Yu Gothic', sans-serif;
              margin: 0.5cm;
              font-size: 10pt;
              line-height: 1.4;
              background-color: #ffffff;
              color: #000000;
            }
          .delivery-meta {
            display: flex;
            justify-content: space-between;
            margin: 6mm 0 4mm;
            font-size: 18pt;
            font-weight: 600;
            color: #2c3e50;
          }
          .delivery-meta-left,
          .delivery-meta-right {
            background: #f8f9fa;
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
          }
          .order-note {
            margin: 3mm 0 2mm;
            font-size: 11pt;
            font-weight: 600;
            color: #2c3e50;
          }
            .order-sheet {
              width: 100%;
              margin: 0 auto;
              position: relative;
              min-height: 287mm; /* A4高度297mm - 上下边距10mm */
              height: 287mm;
              box-sizing: border-box;
            }
            .header {
              margin-bottom: 1mm;
              position: relative;
              display: flex;
              flex-direction: column;
              gap: 4mm;
            }
            .issued-info {
              text-align: left;
              font-size: 13pt;
              font-weight: 600;
              margin-bottom: 1mm;
              color: #2c3e50;
            }
          .title {
              text-align: center;
              font-size: 30pt;
              font-weight: bold;
              margin: 1mm 0;
              color: #000000;
              text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
              letter-spacing: 2px;
            }
            .recipient-block {
              margin-top: 4mm;
              width: 100%;
            }
            .recipient-block div {
              margin-bottom: 0;
              font-size: 26pt;
              font-weight: bold;
              color: #000000;
              width: 100%;
            }
            .sender-block {
              text-align: right;
              margin-bottom: 1mm;
            }
            .sender-block div {
              margin-bottom: 2mm;
              font-size: 10pt;
              color: #000000;
            }
            .approval-box {
              border: 2px solid #34495e;
              width: 120px;
              margin-left: auto;
              text-align: center;
              margin-top: 1mm;
              border-collapse: collapse;
              border-radius: 4px;
              box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .approval-box table {
              width: 100%;
              border-collapse: collapse;
              margin: 0;
            }
            .approval-box td {
              border: 1px solid #34495e;
              padding: 1mm;
              text-align: center;
              font-size: 8pt;
              width: 50%;
              background-color: #f8f9fa;
              font-weight: 500;
            }
            .delivery-info {
              margin: 5mm 0;
              display: flex;
              justify-content: space-between;
            }
            .delivery-info div {
              font-size: 13pt;
              font-weight: bold;
              color: #000000;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin: 2mm 0;
              box-shadow: 0 2px 8px rgba(0,0,0,0.1);
              border-radius: 6px;
              overflow: hidden;
            }
            th, td {
              border: 1px solid #dee2e6;
              padding: 2.4mm 3.6mm; /* 行高+20% */
              text-align: left;
              font-size: 10.5pt;
            }
            th {
              background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
              text-align: center;
              font-weight: bold;
              color: #000000;
              border-bottom: 2px solid #dee2e6;
            }
            .text-center {
              text-align: center;
            }
            .text-right {
              text-align: right;
            }
            .summary-row {
              display: flex;
              justify-content: flex-end;
              margin-top: 4mm;
              margin-bottom: 12mm;
              gap: 8mm;
              padding: 4mm 0;
              border-top: 2px solid #dee2e6;
              background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
              border-radius: 6px;
              padding: 4mm 8mm;
            }

            .order-sheet-content {
              flex: 1;
              display: flex;
              flex-direction: column;
            }
            .summary-item {
              font-weight: bold;
              font-size: 11pt;
              color: #2c3e50;
              padding: 2mm 4mm;
              background-color: #ffffff;
              border-radius: 4px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.1);
              border: 1px solid #dee2e6;
            }
            .notes {
              font-size: 9pt;
              line-height: 1.6;
              position: absolute;
              bottom: 0.5cm;
              left: 0.5cm;
              right: 0.5cm;
              background-color: #f8f9fa;
              padding: 4mm 6mm;
              border-radius: 6px;
              border-left: 4px solid #6c757d;
              box-shadow: 0 2px 4px rgba(0,0,0,0.1);
              page-break-inside: avoid;
            }
            .notes p {
              margin: 2mm 0;
              color: #495057;
              font-weight: 400;
            }
            .notes p:first-child {
              margin-top: 0;
            }
            .notes p:last-child {
              margin-bottom: 0;
            }
            .page-break-after {
              page-break-after: always;
            }
            .order-sheet {
              page-break-inside: avoid;
            }
            @page {
              size: A4;
              margin: 0.5cm;
            }
            @media print {
              @page {
                size: A4;
                margin: 0.5cm;
              }
              body {
                margin: 0;
                padding: 0;
              }
            }
          </style>
        </head>
        <body>${printContent}</body>
        </html>
      `)
      printWindow.document.close()

      // 等待页面加载完成后打印并关闭
      printWindow.onload = function () {
        printWindow.print()
        // 打印完成后延迟关闭窗口
        setTimeout(function () {
          printWindow.close()
        }, 1000)
      }
    }
  } catch (error) {
    console.error('印刷エラー:', error)
    ElMessage.error('印刷中にエラーが発生しました')
  }

  // 关闭对话框并清空临时数据
  printConfirmDialogVisible.value = false
  currentPrintOrderItems.value = []
}

// 生成打印HTML内容（按外注先和注文日分组分页）
const generatePrintHtml = (orderItems: OrderItem[]) => {
  // 打印用的格式化函数（在模板字符串中使用）
  const fmtNum = (val: number | null | undefined) => {
    if (val == null || isNaN(val)) return '0'
    return val.toLocaleString('ja-JP')
  }
  const fmtCurrency = (val: number | null | undefined) => {
    if (val == null || isNaN(val)) return '¥0.00'
    return `¥${val.toLocaleString('ja-JP', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  // 使用日本时区格式化日期时间
  const now = getJapanDate()
  const issuedDateTime = now.toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })

  // 按照外注先和注文日进行分组
  const groupedOrders = new Map<string, OrderItem[]>()

  orderItems.forEach((item) => {
    const supplier = item.supplier || item.supplierCd || '未指定'
    const orderDate = item.orderDate || '未指定'
    const groupKey = `${supplier}_${orderDate}`

    if (!groupedOrders.has(groupKey)) {
      groupedOrders.set(groupKey, [])
    }
    groupedOrders.get(groupKey)!.push(item)
  })

  // 生成每个分组的打印页面
  let pagesHtml = ''
  const groupKeys = Array.from(groupedOrders.keys()).sort()

  groupKeys.forEach((groupKey, index) => {
    const items = groupedOrders.get(groupKey)!
    const [supplier, orderDate] = groupKey.split('_')

    // 按照製品名进行排序（使用日本locale排序）
    const sortedItems = [...items].sort((a, b) => {
      const nameA = a.productName || ''
      const nameB = b.productName || ''
      return nameA.localeCompare(nameB, 'ja-JP', { numeric: true, sensitivity: 'base' })
    })

    // 计算该分组的总计
    const totalQuantity = sortedItems.reduce((sum, item) => sum + (item.quantity || 0), 0)

    // 获取该分组的外注先名称（用于显示）
    let recipientCompany = printForm.recipientCompany || '外注先会社名 御中'
    if (supplier !== '未指定') {
      // 尝试从 supplierOptions 中查找外注先名称
      const supplierOption = supplierOptions.value.find((s) => s.value === supplier)
      if (supplierOption) {
        const supplierName = supplierOption.label.includes(' - ')
          ? supplierOption.label.split(' - ')[1]
          : supplierOption.label
        recipientCompany = `${supplierName} 御中`
      } else if (sortedItems[0]?.supplier) {
        recipientCompany = `${sortedItems[0].supplier} 御中`
      }
    }

    // 获取该分组的注文日（格式化显示）
    let orderDateDisplay = orderDate
    if (orderDate !== '未指定' && sortedItems.length > 0 && sortedItems[0].orderDate) {
      // 格式化注文日为日本格式 YYYY年MM月DD日
      const date = new Date(sortedItems[0].orderDate)
      if (!isNaN(date.getTime())) {
        const year = date.getFullYear()
        const month = date.getMonth() + 1
        const day = date.getDate()
        orderDateDisplay = `${year}年${month}月${day}日`
      }
    }

    // 获取该分组的納入日和納品場所
    const deliveryDateDisplay =
      sortedItems.length > 0 ? sortedItems[0].deliveryDate || '未指定' : '未指定'
    const deliveryLocationDisplay =
      sortedItems.length > 0 ? sortedItems[0].deliveryLocation || '未指定' : '未指定'

    // 生成表格行
    let tableRowsHtml = ''
    sortedItems.forEach((row) => {
      tableRowsHtml += `
        <tr>
          <td class="text-center">${row.orderNo || ''}</td>
          <td class="text-center">${row.productName || ''}</td>
          <td class="text-center">${row.content || ''}</td>
          <td class="text-right">${fmtCurrency(row.unitPrice)}</td>
          <td class="text-center">${fmtNum(row.quantity)}</td>
          <td class="text-center">本</td>
          <td class="text-center">${row.category || ''}</td>
        </tr>
      `
    })

    // 生成单个页面HTML（最后一个页面不添加分页符）
    const pageBreakClass = index < groupKeys.length - 1 ? 'page-break-after' : ''

    pagesHtml += `
      <div class="order-sheet ${pageBreakClass}">
        <div class="issued-info">注文日: ${orderDateDisplay}</div>

        <div class="title">注 文 書</div>

        <div class="header">
          <div class="recipient-block">
            <div>${recipientCompany}</div>
          </div>

          <div class="sender-block">
            <div>日鉄物産荒井オートモーティブ(株)     </div>
            <div>〒496-0902 愛知県愛西市須依町2189  </div>
            <div>TEL<0567>28-4171</div>
            <div>FAX<0567>26-2281</div>
            <div class="approval-box">
              <table>
                <tr>
                  <td>承認</td>
                  <td>発行</td>
                </tr>
                <tr>
                  <td>${printForm.approver || ''}</td>
                  <td>${printForm.issuer || ''}</td>
                </tr>
              </table>
            </div>
          </div>
        </div>

        <div class="delivery-meta">
          <div class="delivery-meta-left">納入日: ${deliveryDateDisplay || '未指定'}</div>
          <div class="delivery-meta-right">納品場所: ${deliveryLocationDisplay || '未指定'}</div>
        </div>

        <div class="order-note">＊下記のとおり注文いたします。</div>

        <table>
          <thead>
            <tr>
              <th width="25%">注文番号</th>
              <th width="15%">製品名</th>
              <th width="15%">内容</th>
              <th width="10%">単価(円)</th>
              <th width="10%">注文数</th>
              <th width="6%">単位</th>
              <th width="19%">区分</th>
            </tr>
          </thead>
          <tbody>
            ${tableRowsHtml}
          </tbody>
        </table>

        <div class="summary-row">
          <div class="summary-item">総注文数  ${fmtNum(totalQuantity)} 本</div>
        </div>

        <div class="notes">
          <p>${printForm.note1}</p>
          <p>${printForm.note2}</p>
          <p>${printForm.note3}</p>
        </div>
      </div>
    `
  })

  return pagesHtml
}

// 页面初始化标志
const isInitialized = ref(false)

// 监听筛选条件变化，自动执行搜索（初始化后生效）
watch(
  () => [filters.dateRange, filters.supplier, filters.productName, filters.status],
  () => {
    // 只有在初始化完成后才自动触发搜索
    if (isInitialized.value) {
      debouncedSearch()
    }
  },
  { deep: true },
)

onMounted(async () => {
  // 确保筛选条件已初始化（默认使用今天的日期范围）
  if (!filters.dateRange || filters.dateRange.length !== 2) {
    filters.dateRange = getTodayDateRange()
  }

  // 加载基础数据
  await loadSuppliers()
  await loadProductNames()
  await loadPrintedOrderNos()
  // 加载休息日列表（不指定 destination_cd，获取所有休息日）
  await loadHolidays()

  // 使用当前筛选条件加载数据
  await handleSearch()

  // 标记初始化完成，之后筛选条件变化会自动触发搜索
  isInitialized.value = true
})
</script>

<style scoped>
.outsourcing-order-page {
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #4ecdc4 0%, #44b09e 100%);
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 12px;
  color: white;
  box-shadow: 0 3px 15px rgba(78, 205, 196, 0.25);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.title-icon {
  width: 40px;
  height: 40px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.title-text {
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.title-badge {
  background: rgba(255, 255, 255, 0.25);
  padding: 3px 10px;
  border-radius: 16px;
  font-size: 13px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  font-size: 12px;
  opacity: 0.9;
}

/* ==================== 検索条件区域样式 ==================== */
.filter-card {
  margin-bottom: 10px;
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(102, 126, 234, 0.08);
  border: 1px solid rgba(102, 126, 234, 0.12);
  background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
}

.filter-card :deep(.el-card__body) {
  padding: 12px 16px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  font-size: 12px;
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.date-filter-container {
  display: flex;
  align-items: center;
  gap: 6px;
}

.date-picker {
  width: 220px;
}

.date-picker :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
  transition: all 0.2s;
}

.date-picker :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.date-quick-btns {
  display: flex;
  gap: 2px;
}

.quick-btn {
  padding: 6px 8px;
  font-size: 12px;
  border-radius: 4px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  background: white;
  color: #667eea;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: transparent;
  transform: translateY(-1px);
}

.quick-btn :deep(.el-icon) {
  font-size: 12px;
}

.today-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: white;
  font-weight: 600;
}

.today-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.month-btn {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
}

.supplier-select {
  width: 208px;
}

.supplier-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
}

.supplier-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.product-select {
  width: 180px;
}

.product-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
}

.product-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.status-select {
  width: 100px;
}

.status-select :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2) inset;
}

.status-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #667eea inset;
}

.filter-actions {
  margin-left: auto;
}

.reset-btn {
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 6px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  background: white;
  color: #667eea;
  transition: all 0.2s;
}

.reset-btn:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: #667eea;
}

.reset-btn :deep(.el-icon) {
  margin-right: 4px;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 10px 14px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.left-actions {
  display: flex;
  gap: 8px;
}

.right-actions {
  display: flex;
  align-items: center;
}

.right-actions .el-tag {
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 6px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  color: #0369a1;
  box-shadow: 0 1px 3px rgba(3, 105, 161, 0.1);
}

/* 按钮颜色区分 */
.left-actions .el-button--primary:first-child {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.3);
}

.left-actions .el-button--primary:first-child:hover {
  background: linear-gradient(135deg, #337ecc 0%, #2b6cb0 100%);
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.4);
  transform: translateY(-1px);
}

.left-actions .el-button--success {
  background: linear-gradient(135deg, #67c23a 0%, #529b2e 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(103, 194, 58, 0.3);
}

.left-actions .el-button--success:hover {
  background: linear-gradient(135deg, #529b2e 0%, #458521 100%);
  box-shadow: 0 4px 10px rgba(103, 194, 58, 0.4);
  transform: translateY(-1px);
}

.print-btn {
  background: linear-gradient(135deg, #e6a23c 0%, #cf9236 100%) !important;
  border: none !important;
  box-shadow: 0 2px 6px rgba(230, 162, 60, 0.3) !important;
}

.print-btn:hover {
  background: linear-gradient(135deg, #cf9236 0%, #b8822f 100%) !important;
  box-shadow: 0 4px 10px rgba(230, 162, 60, 0.4) !important;
  transform: translateY(-1px);
}

.btn-badge {
  margin-left: 6px;
  background: rgba(255, 255, 255, 0.3);
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.table-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.data-table {
  border-radius: 8px;
}

.data-table :deep(.el-table__header th) {
  font-weight: 600;
  padding: 6px 0;
  height: 36px;
  font-size: 12px;
  background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f5 100%);
}

.data-table :deep(.el-table__body td) {
  padding: 6px 0;
  height: 36px;
  font-size: 12px;
}

.data-table :deep(.el-table__body tr) {
  height: 36px;
}

.data-table :deep(.el-table__body tr:hover) {
  background-color: #f8f9fa;
}

.data-table :deep(.el-table .cell) {
  padding: 0 8px;
  line-height: 1.4;
}

.data-table :deep(.el-link) {
  font-size: 12px;
  font-weight: 500;
}

/* 操作列按钮颜色区分 */
.data-table :deep(.el-button-group .el-button--primary) {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border: none;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.3);
}

.data-table :deep(.el-button-group .el-button--primary:hover) {
  background: linear-gradient(135deg, #337ecc 0%, #2b6cb0 100%);
  box-shadow: 0 2px 5px rgba(64, 158, 255, 0.4);
}

.data-table :deep(.el-button-group .el-button--info) {
  background: linear-gradient(135deg, #909399 0%, #767a82 100%);
  border: none;
  box-shadow: 0 1px 3px rgba(144, 147, 153, 0.3);
}

.data-table :deep(.el-button-group .el-button--info:hover) {
  background: linear-gradient(135deg, #767a82 0%, #5d6066 100%);
  box-shadow: 0 2px 5px rgba(144, 147, 153, 0.4);
}

.data-table :deep(.el-button-group .el-button--danger) {
  background: linear-gradient(135deg, #f56c6c 0%, #dd6161 100%);
  border: none;
  box-shadow: 0 1px 3px rgba(245, 108, 108, 0.3);
}

.data-table :deep(.el-button-group .el-button--danger:hover) {
  background: linear-gradient(135deg, #dd6161 0%, #c45656 100%);
  box-shadow: 0 2px 5px rgba(245, 108, 108, 0.4);
}

.amount-cell {
  font-weight: 600;
  color: #e6a23c;
}

/* 外注先标签样式 */
.supplier-tag {
  font-weight: 500;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
}

.pagination-wrapper {
  padding: 12px 14px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #ebeef5;
}

.order-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.order-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #4ecdc4 0%, #44b09e 100%);
  color: white;
  margin: 0;
  padding: 12px 16px;
  border-bottom: none;
}

.order-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.order-dialog :deep(.el-dialog__headerbtn) {
  top: 12px;
  right: 16px;
}

.order-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px;
}

.order-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}

.order-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #f5f7fa;
}

.batch-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.15);
}

.batch-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #4ecdc4 0%, #44b09e 100%);
  color: white;
  margin: 0;
  padding: 12px 20px;
  border-bottom: none;
}

.compact-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dialog-icon {
  font-size: 18px;
}

.dialog-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.order-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #f5f7fa;
}

.dialog-content {
  padding: 20px;
  max-height: 70vh;
  overflow-y: auto;
}

.dialog-content::-webkit-scrollbar {
  width: 6px;
}

.dialog-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.dialog-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.compact-form {
  background: white;
  border-radius: 8px;
  padding: 16px;
}

.form-section {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.form-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 2px solid #4ecdc4;
}

.section-icon {
  color: #4ecdc4;
  font-size: 16px;
}

.compact-item :deep(.el-form-item) {
  margin-bottom: 12px;
}

.compact-item :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 500;
  color: #606266;
  padding: 0 0 0 0;
  line-height: 32px;
}

.compact-item :deep(.el-form-item__content) {
  line-height: 32px;
}

.compact-item :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  transition: all 0.2s;
}

.compact-item :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.compact-item :deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px #4ecdc4 inset;
}

.compact-item :deep(.el-select .el-input__wrapper) {
  border-radius: 6px;
}

.compact-item :deep(.el-date-editor .el-input__wrapper) {
  border-radius: 6px;
}

.full-width {
  width: 100%;
}

.full-width-select {
  width: 100%;
}

.product-select :deep(.el-input__wrapper) {
  border-radius: 6px;
}

.product-option-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.product-code {
  font-weight: 500;
  color: #303133;
}

.product-name {
  font-size: 12px;
  color: #909399;
  margin-left: 12px;
}

.lead-time-hint {
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
}

.product-count {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
  margin-left: 8px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.product-list-table {
  margin-top: 12px;
}

.product-list-table :deep(.el-table) {
  border-radius: 6px;
}

.product-list-table :deep(.el-table th) {
  background: #f5f7fa;
  font-weight: 600;
  padding: 8px 0;
  height: 36px;
}

.batch-product-table :deep(.el-table__body-wrapper) {
  font-size: 12px;
}

.batch-product-table :deep(.el-table td) {
  padding: 5px 0;
  height: 38px;
}

.batch-product-table :deep(.el-table th) {
  padding: 6px 0;
  height: 34px;
  background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f5 100%);
  font-weight: 600;
  font-size: 12px;
}

.batch-product-table :deep(.el-table .cell) {
  padding: 0 6px;
  line-height: 1.3;
}

.batch-product-table :deep(.el-table__body tr:hover) {
  background-color: #f8f9fa;
}

.batch-product-table :deep(.quantity-input) {
  height: 26px;
}

.batch-product-table :deep(.quantity-input .el-input__wrapper) {
  padding: 0 6px;
  min-height: 26px;
  border-radius: 4px;
  transition: all 0.2s;
}

.batch-product-table :deep(.quantity-input .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #409eff inset;
}

.amount-display :deep(.el-input__inner) {
  font-weight: 600;
  color: #e6a23c;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  background: white;
  border-top: 1px solid #ebeef5;
}

.dialog-footer .el-button {
  min-width: 100px;
  border-radius: 6px;
  font-weight: 500;
}

.dialog-footer .el-button--primary {
  background: linear-gradient(135deg, #4ecdc4 0%, #44b09e 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(78, 205, 196, 0.3);
}

.dialog-footer .el-button--primary:hover {
  background: linear-gradient(135deg, #44b09e 0%, #3a9d8f 100%);
  box-shadow: 0 4px 12px rgba(78, 205, 196, 0.4);
}

/* 批量登録窗体样式 */
.batch-form-container {
  padding: 0;
}

.batch-form {
  padding: 10px 14px;
  background: #ffffff;
  border-radius: 8px;
}

.compact-form-inner {
  margin-bottom: 0;
}

.form-row-inline {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.form-row-inline.date-row {
  margin-bottom: 0;
  padding-top: 6px;
  border-top: 1px solid #f0f0f0;
}

.inline-form-item {
  margin-bottom: 0;
  flex: 0 0 auto;
}

.inline-form-item :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 500;
  color: #606266;
  padding: 0 6px 0 0;
  line-height: 30px;
}

.inline-form-item :deep(.el-form-item__content) {
  line-height: 30px;
  padding-left: 6px;
}

.inline-form-item.flex-item {
  flex: 1 1 auto;
  min-width: 200px;
}

.inline-form-item.button-item {
  flex: 0 0 auto;
  margin-left: auto;
}

.delivery-date-item {
  position: relative;
}

.delivery-date-wrapper {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
}

.delivery-date-hint-text {
  color: #f56565;
  font-size: 10px;
  line-height: 1.2;
  margin-top: 2px;
  padding-left: 2px;
}

.supplier-select,
.date-select {
  width: 100%;
}

.supplier-select :deep(.el-input__wrapper),
.date-select :deep(.el-input__wrapper) {
  border-radius: 5px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  transition: all 0.2s;
  padding: 3px 10px;
  min-height: 30px;
}

.supplier-select :deep(.el-input__inner),
.date-select :deep(.el-input__inner) {
  padding: 0 4px;
}

.supplier-select :deep(.el-input__wrapper:hover),
.date-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.supplier-select :deep(.el-input.is-focus .el-input__wrapper),
.date-select :deep(.el-input.is-focus .el-input__wrapper) {
  box-shadow: 0 0 0 1px #4ecdc4 inset;
}

.load-btn {
  white-space: nowrap;
  border-radius: 5px;
  padding: 6px 14px;
  font-weight: 500;
  font-size: 13px;
  box-shadow: 0 2px 4px rgba(78, 205, 196, 0.2);
  transition: all 0.2s;
  height: 30px;
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border: none;
}

.load-btn:hover {
  background: linear-gradient(135deg, #337ecc 0%, #2b6cb0 100%);
  box-shadow: 0 3px 6px rgba(64, 158, 255, 0.3);
  transform: translateY(-1px);
}

.load-btn:hover {
  box-shadow: 0 4px 8px rgba(78, 205, 196, 0.3);
  transform: translateY(-1px);
}

.table-container {
  margin-top: 10px;
}

.dialog-footer-compact {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 14px;
  background: #fafbfc;
  border-top: 1px solid #ebeef5;
}

.cancel-btn,
.register-btn {
  min-width: 90px;
  border-radius: 5px;
  font-weight: 500;
  padding: 6px 16px;
  transition: all 0.2s;
  height: 32px;
  font-size: 13px;
}

.cancel-btn {
  border: 1px solid #dcdfe6;
  background: white;
}

.cancel-btn:hover {
  border-color: #c0c4cc;
  background: #f5f7fa;
}

.register-btn {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border: none;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.25);
}

.register-btn:hover {
  background: linear-gradient(135deg, #337ecc 0%, #2b6cb0 100%);
  box-shadow: 0 4px 10px rgba(64, 158, 255, 0.35);
  transform: translateY(-1px);
}

.register-btn:active {
  transform: translateY(0);
}

.loading-placeholder,
.empty-placeholder {
  padding: 20px 16px;
  text-align: center;
  color: #909399;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #d1d5db;
}

.compact-placeholder {
  padding: 18px 12px;
}

.compact-placeholder p {
  margin: 10px 0 0;
  font-size: 13px;
  color: #909399;
}

.loading-placeholder .el-icon {
  font-size: 24px;
  margin-bottom: 10px;
  color: #409eff;
}

.batch-product-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.batch-product-table :deep(.el-table__header) {
  background: #f8f9fa;
}

.batch-product-table :deep(.el-table__header th) {
  background: transparent;
  color: #374151;
  font-weight: 600;
  font-size: 12px;
  padding: 6px 8px;
  border-bottom: 1px solid #e5e7eb;
  line-height: 1.4;
}

.batch-product-table :deep(.el-table__body td) {
  padding: 6px 8px;
  font-size: 13px;
  line-height: 1.4;
}

.batch-product-table :deep(.el-table__body tr:hover) {
  background-color: rgba(78, 205, 196, 0.04);
}

.quantity-input {
  width: 100%;
  text-align: center;
}

.quantity-input :deep(.el-input__wrapper) {
  border-radius: 6px;
  text-align: center;
  padding: 2px 8px;
  min-height: 28px;
  transition: all 0.2s;
}

.quantity-input :deep(.el-input__inner) {
  text-align: center;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  height: 24px;
}

.warning-cell :deep(.el-input__wrapper) {
  background-color: #fef2f2;
  border-color: #fca5a5;
}

.normal-cell :deep(.el-input__wrapper) {
  background-color: #f0fdf4;
  border-color: #86efac;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1400px) {
  .filter-group:not(.filter-group-date) {
    width: 160px;
  }

  .filter-group-supplier {
    width: 192px !important; /* 160px * 1.2 = 192px (增加20%) */
  }

  .filter-group-date {
    min-width: 200px;
  }

  .date-range-group .date-picker-input {
    width: 132px;
  }
}

@media (max-width: 1200px) {
  .filter-row {
    gap: 12px;
  }

  .filter-group:not(.filter-group-date) {
    width: 150px;
  }

  .filter-group-supplier {
    width: 180px !important; /* 150px * 1.2 = 180px (增加20%) */
  }

  .filter-group-date {
    min-width: 200px;
  }

  .date-range-group {
    flex-wrap: wrap;
  }

  .date-range-group .date-picker-input {
    width: 100%;
    min-width: 120px;
  }
}

@media (max-width: 992px) {
  .filter-card :deep(.el-card__body) {
    padding: 12px;
  }

  .filter-row {
    flex-wrap: wrap;
    gap: 12px;
  }

  .filter-group {
    width: 100%;
    min-width: 100%;
  }

  .filter-group-date {
    min-width: 100%;
  }

  .date-range-group {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }

  .date-range-group .date-picker-input {
    width: 100%;
  }

  .date-quick-buttons {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 992px) {
  .outsourcing-order-page {
    padding: 10px;
  }

  .page-header {
    padding: 12px 14px;
  }

  .title {
    font-size: 18px;
  }

  .action-bar {
    flex-direction: column;
    gap: 10px;
    padding: 8px 12px;
  }

  .left-actions {
    flex-wrap: wrap;
    justify-content: flex-start;
    width: 100%;
  }

  .right-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .filter-card :deep(.el-card__body) {
    padding: 10px 12px;
  }

  .data-table :deep(.el-table__header th),
  .data-table :deep(.el-table__body td) {
    padding: 4px 0;
    font-size: 11px;
  }

  .data-table :deep(.el-table .cell) {
    padding: 0 4px;
  }
}

@media (max-width: 768px) {
  .outsourcing-order-page {
    padding: 8px;
  }

  .page-header {
    padding: 10px 12px;
    margin-bottom: 10px;
  }

  .title {
    font-size: 16px;
    gap: 8px;
  }

  .title-icon {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }

  .subtitle {
    font-size: 11px;
  }

  .filter-card {
    margin-bottom: 10px;
  }

  .filter-card :deep(.el-card__header) {
    padding: 10px 12px;
  }

  .filter-card :deep(.el-card__body) {
    padding: 12px;
  }

  .filter-form {
    gap: 12px;
  }

  .filter-row {
    flex-direction: column;
    gap: 12px;
  }

  .filter-group {
    width: 100%;
  }

  .date-quick-buttons {
    width: 100%;
  }

  .date-btn {
    flex: 1 1 auto;
    min-width: calc(25% - 5px);
  }

  .action-bar {
    padding: 8px 10px;
  }

  .left-actions {
    flex-direction: column;
    width: 100%;
  }

  .left-actions .el-button {
    width: 100%;
    justify-content: center;
  }

  .right-actions {
    width: 100%;
  }

  .data-table :deep(.el-table__header th),
  .data-table :deep(.el-table__body td) {
    padding: 3px 0;
    font-size: 10px;
  }

  .data-table :deep(.el-table .cell) {
    padding: 0 3px;
    line-height: 1.2;
  }

  /* 隐藏部分列在小屏幕上 */
  .data-table :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }

  /* 对话框响应式 */
  .order-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 5vh auto;
  }

  .batch-dialog :deep(.el-dialog) {
    width: 95% !important;
  }
}

@media (max-width: 576px) {
  .outsourcing-order-page {
    padding: 6px;
  }

  .page-header {
    padding: 8px 10px;
  }

  .title {
    font-size: 14px;
  }

  .title-icon {
    width: 32px;
    height: 32px;
    font-size: 16px;
  }

  .date-quick-buttons {
    flex-wrap: wrap;
  }

  .date-quick-buttons .el-button {
    flex: 1 1 auto;
    min-width: calc(50% - 4px);
  }

  .pagination-wrapper {
    padding: 8px 10px;
  }

  .pagination-wrapper :deep(.el-pagination) {
    justify-content: center;
  }

  .pagination-wrapper :deep(.el-pagination .el-pagination__sizes),
  .pagination-wrapper :deep(.el-pagination .el-pagination__jump) {
    display: none;
  }
}

/* 打印按钮样式 */
.print-btn {
  padding: 10px 16px;
  border-radius: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.print-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(78, 205, 196, 0.4);
}

/* 打印确认对话框样式 */
.print-confirm-dialog {
  border-radius: 12px;
  overflow: hidden;
}

.print-confirm-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.print-confirm-dialog :deep(.el-dialog__header) {
  padding: 10px 14px;
  background: linear-gradient(135deg, #4ecdc4 0%, #44b09e 100%);
  color: rgb(8, 8, 8);
  border-bottom: none;
}

.dialog-header-with-button {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.dialog-title {
  font-size: 14px;
  font-weight: 600;
  color: rgb(10, 10, 10);
}

.confirm-btn-header {
  border-radius: 5px;
  padding: 5px 12px;
  font-weight: 600;
  font-size: 11px;
  background: rgba(23, 241, 158, 0.589);
  border: 1px solid rgba(8, 7, 7, 0.774);
  color: rgb(7, 7, 7);
  transition: all 0.2s ease;
  backdrop-filter: blur(10px);
  margin-left: 200px;
}

.confirm-btn-header:hover {
  background: rgba(210, 230, 103, 0.3);
  border-color: rgba(5, 180, 28, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.confirm-btn-header :deep(.el-icon) {
  margin-right: 4px;
  font-size: 12px;
}

.print-confirm-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 14px;
}

.print-confirm-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 16px;
}

.print-confirm-dialog :deep(.el-dialog__body) {
  padding: 0;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.print-confirm-dialog :deep(.el-dialog__footer) {
  padding: 20px 24px;
  background-color: #f8f9fa;
  border-radius: 0 0 12px 12px;
}

/* 打印确认对话框 - 紧凑精美样式 */
.print-confirm-content-compact {
  padding: 10px 14px;
}

.form-sections-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-section-compact {
  background: white;
  border-radius: 5px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: all 0.2s ease;
}

.form-section-compact:hover {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
  border-color: #4ecdc4;
}

.section-header-compact {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e5e7eb;
  font-weight: 600;
  color: #334155;
  font-size: 11px;
  gap: 5px;
}

.section-icon {
  color: #4ecdc4;
  font-size: 13px;
  flex-shrink: 0;
}

.section-title {
  font-weight: 600;
  letter-spacing: 0.2px;
}

.form-fields-compact {
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-field-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-field-row .field-label {
  min-width: 95px;
  font-size: 11px;
  font-weight: 500;
  color: #475569;
  flex-shrink: 0;
}

.form-input-compact,
.form-textarea-compact {
  flex: 1;
}

.form-input-compact :deep(.el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #d1d5db;
  padding: 2px 7px;
  min-height: 26px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.03);
}

.form-input-compact :deep(.el-input__wrapper:hover) {
  border-color: #9ca3af;
}

.form-input-compact :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #4ecdc4;
  box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.1);
}

.form-input-compact :deep(.el-input__inner) {
  font-size: 11px;
  padding: 0;
  height: auto;
  line-height: 1.3;
}

.form-input-compact :deep(.el-select .el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #d1d5db;
  padding: 2px 7px;
  min-height: 26px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.03);
}

.form-input-compact :deep(.el-select .el-input__wrapper:hover) {
  border-color: #9ca3af;
}

.form-input-compact :deep(.el-select.is-focus .el-input__wrapper) {
  border-color: #4ecdc4;
  box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.1);
}

.form-textarea-compact :deep(.el-textarea__inner) {
  border-radius: 4px;
  border: 1px solid #d1d5db;
  padding: 4px 7px;
  font-size: 10px;
  line-height: 1.3;
  transition: all 0.2s ease;
  resize: vertical;
  min-height: 40px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.03);
}

.form-textarea-compact :deep(.el-textarea__inner:hover) {
  border-color: #9ca3af;
}

.form-textarea-compact :deep(.el-textarea__inner:focus) {
  border-color: #4ecdc4;
  box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.1);
}

/* 编辑对话框 - 紧凑精美样式 */
.edit-form-container {
  padding: 12px 16px;
  background: #fafbfc;
}

.edit-form-compact {
  margin: 0;
}

.edit-form-compact :deep(.el-form-item) {
  margin-bottom: 10px;
}

.edit-form-item-compact {
  margin-bottom: 10px;
}

.edit-form-item-compact :deep(.el-form-item__label) {
  font-size: 12px;
  font-weight: 500;
  color: #606266;
  padding: 0 8px 0 0;
  line-height: 28px;
  height: 28px;
}

.edit-form-item-compact :deep(.el-form-item__content) {
  line-height: 28px;
}

.edit-input-compact :deep(.el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  padding: 2px 8px;
  min-height: 28px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.02);
}

.edit-input-compact :deep(.el-input__wrapper:hover) {
  border-color: #c0c4cc;
}

.edit-input-compact :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: #4ecdc4;
  box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.1);
}

.edit-input-compact :deep(.el-input__inner) {
  font-size: 12px;
  padding: 0;
  height: 24px;
  line-height: 24px;
}

.edit-input-compact :deep(.el-input.is-disabled .el-input__wrapper) {
  background-color: #f5f7fa;
  border-color: #e4e7ed;
  color: #606266;
}

.edit-input-compact :deep(.el-date-editor) {
  width: 100%;
}

.edit-input-compact :deep(.el-date-editor .el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  padding: 2px 8px;
  min-height: 28px;
}

.edit-input-compact :deep(.el-select .el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  padding: 2px 8px;
  min-height: 28px;
}

.edit-input-compact :deep(.el-input-number) {
  width: 100%;
}

.edit-input-compact :deep(.el-input-number .el-input__wrapper) {
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  padding: 2px 8px;
  min-height: 28px;
}

.edit-textarea-compact :deep(.el-textarea__inner) {
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  padding: 4px 8px;
  font-size: 12px;
  line-height: 1.4;
  transition: all 0.2s ease;
  resize: vertical;
  min-height: 50px;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.02);
}

.edit-textarea-compact :deep(.el-textarea__inner:hover) {
  border-color: #c0c4cc;
}

.edit-textarea-compact :deep(.el-textarea__inner:focus) {
  border-color: #4ecdc4;
  box-shadow: 0 0 0 2px rgba(78, 205, 196, 0.1);
}

.order-dialog :deep(.el-dialog__body) {
  padding: 0;
  background: #fafbfc;
}

.edit-dialog-compact :deep(.el-dialog) {
  border-radius: 8px;
  overflow: hidden;
}

.edit-dialog-compact :deep(.el-dialog__header) {
  padding: 10px 16px;
  background: linear-gradient(135deg, #4ecdc4 0%, #44b09e 100%);
  color: white;
  margin: 0;
  border-bottom: none;
}

.edit-dialog-compact :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 15px;
}

.edit-dialog-compact :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 16px;
}

.edit-dialog-compact :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
  font-size: 18px;
}

.edit-dialog-compact :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: rgba(255, 255, 255, 0.8);
}
</style>
