<template>
  <div class="standard-costing">
    <div class="page-hero">
      <div class="hero-text">
        <h2>標準原価計算</h2>
        <p>原価標準の設定（DM・DL・OH）、月次実績に基づく標準許容算定と七項目差異の統合管理</p>
      </div>
      <div class="hero-nav">
        <router-link to="/erp/costing/actual" class="nav-chip">実際原価</router-link>
        <router-link to="/erp/costing/variance" class="nav-chip accent">差異分析</router-link>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="main-tabs" @tab-change="onTabChange">
      <el-tab-pane label="標準原価バージョン" name="versions">
        <div class="toolbar">
          <el-button type="primary" @click="openVersionDialog()">
            <el-icon><Plus /></el-icon> 新規バージョン
          </el-button>
          <el-button @click="loadVersions"><el-icon><Refresh /></el-icon> 更新</el-button>
        </div>
        <el-card shadow="never">
          <el-table v-loading="loadingVersions" :data="versions" stripe border>
            <el-table-column prop="code" label="コード" width="140" />
            <el-table-column prop="fiscal_year" label="会計年度" width="100" align="center" />
            <el-table-column prop="status" label="状態" width="100">
              <template #default="{ row }">
                <el-tag :type="row.status === 'active' ? 'success' : row.status === 'draft' ? 'warning' : 'info'">
                  {{ row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="effective_from" label="適用開始" width="120" />
            <el-table-column prop="effective_to" label="適用終了" width="120" />
            <el-table-column prop="remarks" label="備考" min-width="160" show-overflow-tooltip />
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openVersionDialog(row)">編集</el-button>
                <el-button type="danger" link size="small" @click="onDeleteVersion(row)">削除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="製品標準原価" name="products">
        <el-card class="filter-card" shadow="never">
          <el-form :inline="true">
            <el-form-item label="バージョン" required>
              <el-select
                v-model="productFilters.version_id"
                placeholder="選択"
                style="width: 220px"
                filterable
                @change="onVersionForProductsChange"
              >
                <el-option
                  v-for="v in versions"
                  :key="v.id"
                  :label="`${v.code} (${v.fiscal_year})`"
                  :value="v.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="製品名">
              <el-select
                v-model="productFilters.product_cd"
                class="product-name-select"
                filterable
                remote
                clearable
                reserve-keyword
                placeholder="製品名で検索して選択"
                :remote-method="searchProductFilter"
                :loading="loadingProductFilter"
                @clear="onClearProductFilter"
              >
                <el-option
                  v-for="p in productFilterOptions"
                  :key="p.product_cd"
                  :label="productFilterOptionLabel(p)"
                  :value="p.product_cd"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadProductStandards"><el-icon><Search /></el-icon> 検索</el-button>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :disabled="!productFilters.version_id" @click="openProductDialog()">
                <el-icon><Plus /></el-icon> 新規登録
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
        <el-card shadow="never">
          <el-table v-loading="loadingProducts" :data="productList" stripe border>
            <el-table-column prop="product_cd" label="品番" width="120" fixed />
            <el-table-column prop="product_name" label="品名" min-width="160" show-overflow-tooltip />
            <el-table-column label="直接材料" width="120" align="right">
              <template #default="{ row }">¥{{ money(row.material_cost_std) }}</template>
            </el-table-column>
            <el-table-column label="直接労務" width="120" align="right">
              <template #default="{ row }">¥{{ money(row.labor_cost_std) }}</template>
            </el-table-column>
            <el-table-column label="製造間接" width="120" align="right">
              <template #default="{ row }">¥{{ money(row.overhead_cost_std) }}</template>
            </el-table-column>
            <el-table-column label="標準原価（単位）" width="140" align="right">
              <template #default="{ row }"><strong>¥{{ money(row.total_cost_std) }}</strong></template>
            </el-table-column>
            <el-table-column prop="source" label="ソース" width="90" />
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="openProductDialog(row)">編集</el-button>
                <el-button type="danger" link size="small" @click="onDeleteProduct(row)">削除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="productPagination.page"
              v-model:page-size="productPagination.pageSize"
              :total="productPagination.total"
              :page-sizes="[20, 50, 100]"
              layout="total, sizes, prev, pager, next"
              background
              @current-change="loadProductStandards"
              @size-change="loadProductStandards"
            />
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="月次実績・差異" name="periods">
        <el-row :gutter="16">
          <el-col :span="6">
            <el-card shadow="never" class="period-list-card">
              <template #header>
                <span>会計期間（月）</span>
                <el-button type="primary" size="small" class="ml8" @click="openPeriodDialog()">新規</el-button>
              </template>
              <el-scrollbar max-height="420px">
                <div
                  v-for="p in periods"
                  :key="p.id"
                  class="period-item"
                  :class="{ active: selectedPeriod?.id === p.id }"
                  @click="selectPeriod(p)"
                >
                  <div class="period-ym">{{ p.year_month }}</div>
                  <el-tag size="small" :type="p.status === 'closed' ? 'info' : 'success'">{{ p.status }}</el-tag>
                </div>
                <el-empty v-if="!periods.length" description="期間がありません" :image-size="64" />
              </el-scrollbar>
            </el-card>
          </el-col>
          <el-col :span="18">
            <template v-if="selectedPeriod">
              <div class="toolbar">
                <span class="period-title">品目別：{{ selectedPeriod.year_month }}</span>
                <el-button type="primary" :disabled="!selectedPeriod" @click="openPeriodLineDialog()">
                  <el-icon><Plus /></el-icon> 品目行を追加
                </el-button>
                <el-button @click="loadPeriodProducts"><el-icon><Refresh /></el-icon> 更新</el-button>
              </div>
              <el-card shadow="never">
                <el-table v-loading="loadingPeriodProducts" :data="periodProducts" stripe border size="small">
                  <el-table-column prop="product_cd" label="品番" width="110" fixed />
                  <el-table-column prop="product_name" label="品名" min-width="120" show-overflow-tooltip />
                  <el-table-column prop="finished_good_qty" label="完成" width="72" align="right" />
                  <el-table-column prop="wip_equivalent_qty" label="仕掛約当" width="88" align="right" />
                  <el-table-column label="許容材料" width="100" align="right">
                    <template #default="{ row }">¥{{ money(row.standard_material_allowed) }}</template>
                  </el-table-column>
                  <el-table-column label="許容労務" width="100" align="right">
                    <template #default="{ row }">¥{{ money(row.standard_labor_allowed) }}</template>
                  </el-table-column>
                  <el-table-column label="許容間接" width="100" align="right">
                    <template #default="{ row }">¥{{ money(row.standard_overhead_allowed) }}</template>
                  </el-table-column>
                  <el-table-column label="実際材料" width="100" align="right">
                    <template #default="{ row }">{{ row.actual_material_cost != null ? `¥${money(row.actual_material_cost)}` : '—' }}</template>
                  </el-table-column>
                  <el-table-column label="差異計(材料)" width="108" align="right">
                    <template #default="{ row }">
                      <span v-if="row.variance_material_total != null" :class="varClass(row.variance_material_total)">
                        {{ signedMoney(row.variance_material_total) }}
                      </span>
                      <span v-else>—</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="200" fixed="right">
                    <template #default="{ row }">
                      <el-button type="primary" link size="small" @click="openPeriodLineDialog(row)">編集</el-button>
                      <el-button type="warning" link size="small" @click="onRecalcLine(row)">再計算</el-button>
                      <el-button type="danger" link size="small" @click="onDeletePeriodLine(row)">削除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </el-card>
            </template>
            <el-empty v-else description="左から会計期間を選択してください" />
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>

    <!-- バージョンダイアログ -->
    <el-dialog v-model="versionDialogVisible" :title="versionForm.id ? 'バージョン編集' : 'バージョン新規'" width="520px" destroy-on-close @closed="resetVersionForm">
      <el-form :model="versionForm" label-width="120px">
        <el-form-item label="コード" required>
          <el-input v-model="versionForm.code" placeholder="例: FY2026-A" />
        </el-form-item>
        <el-form-item label="会計年度" required>
          <el-input-number v-model="versionForm.fiscal_year" :min="2000" :max="2100" />
        </el-form-item>
        <el-form-item label="状態">
          <el-select v-model="versionForm.status">
            <el-option label="draft" value="draft" />
            <el-option label="active" value="active" />
            <el-option label="archived" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="適用開始" required>
          <el-date-picker v-model="versionForm.effective_from" type="date" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="適用終了">
          <el-date-picker v-model="versionForm.effective_to" type="date" value-format="YYYY-MM-DD" clearable />
        </el-form-item>
        <el-form-item label="備考">
          <el-input v-model="versionForm.remarks" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="versionDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="saveVersion">保存</el-button>
      </template>
    </el-dialog>

    <!-- 製品標準原価ダイアログ -->
    <el-dialog
      v-model="productDialogVisible"
      class="product-std-dialog"
      :title="productForm.headerId ? `標準原価編集 · ${productForm.product_cd}` : '標準原価 新規登録'"
      width="900px"
      destroy-on-close
      top="3vh"
      append-to-body
      @closed="resetProductForm"
    >
      <div class="pd-shell">
        <div class="pd-head">
          <div class="pd-head-row">
            <div class="pd-field pd-field-product">
              <label class="pd-field-label">製品<span class="req">*</span></label>
              <el-select
                v-if="!productForm.headerId"
                v-model="productForm.product_cd"
                class="pd-product-select"
                filterable
                remote
                clearable
                reserve-keyword
                :remote-method="searchProducts"
                :loading="loadingMasterProducts"
                placeholder="製品名・コードで検索"
                @change="onProductCdChange"
              >
                <el-option
                  v-for="p in masterProductOptions"
                  :key="p.product_cd"
                  :label="productFilterOptionLabel(p)"
                  :value="p.product_cd"
                />
              </el-select>
              <div v-else class="pd-product-readonly">
                <span class="pd-pname">{{ productForm.product_name || '—' }}</span>
                <el-tag size="small" type="info" effect="plain">{{ productForm.product_cd }}</el-tag>
              </div>
            </div>
            <div class="pd-field pd-field-src">
              <label class="pd-field-label">ソース</label>
              <el-select v-model="productForm.source" size="default" class="pd-src-select">
                <el-option label="manual" value="manual" />
                <el-option label="rollup" value="rollup" />
                <el-option label="import" value="import" />
              </el-select>
            </div>
          </div>
          <p class="pd-hint">
            <el-icon class="pd-hint-icon"><InfoFilled /></el-icon>
            明細から自動集計。明細が空のときは「単位標準」タブで直接入力できます。
          </p>
        </div>

        <el-tabs v-model="productInnerTab" class="pd-tabs">
        <el-tab-pane label="直接材料" name="mat">
          <div class="pd-pane-actions">
            <el-button size="small" type="primary" plain @click="addMatLine"><el-icon><Plus /></el-icon> 行追加</el-button>
          </div>
          <div class="pd-table-scroll">
          <el-table :data="productForm.material_lines" border size="small" class="pd-table">
            <el-table-column label="#" width="50">
              <template #default="{ $index }">{{ $index + 1 }}</template>
            </el-table-column>
            <el-table-column label="材料CD" width="110">
              <template #default="{ row }"><el-input v-model="row.material_cd" /></template>
            </el-table-column>
            <el-table-column label="材料名" min-width="120">
              <template #default="{ row }"><el-input v-model="row.material_name" /></template>
            </el-table-column>
            <el-table-column label="数量/台" width="100">
              <template #default="{ row }"><el-input-number v-model="row.qty_per_unit" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="スクラップ%" width="100">
              <template #default="{ row }"><el-input-number v-model="row.scrap_pct" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="標準単価" width="110">
              <template #default="{ row }"><el-input-number v-model="row.standard_unit_price" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="金額(任意)" width="100">
              <template #default="{ row }"><el-input-number v-model="row.amount" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column width="70" fixed="right">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="productForm.material_lines.splice($index, 1)">削除</el-button>
              </template>
            </el-table-column>
          </el-table>
          </div>
        </el-tab-pane>
        <el-tab-pane label="直接労務" name="lab">
          <div class="pd-pane-actions">
            <el-button size="small" type="primary" plain @click="addLabLine"><el-icon><Plus /></el-icon> 行追加</el-button>
          </div>
          <div class="pd-table-scroll">
          <el-table :data="productForm.labor_lines" border size="small" class="pd-table">
            <el-table-column label="工程CD" width="100">
              <template #default="{ row }"><el-input v-model="row.process_cd" /></template>
            </el-table-column>
            <el-table-column label="工程名" min-width="120">
              <template #default="{ row }"><el-input v-model="row.process_name" /></template>
            </el-table-column>
            <el-table-column label="標準H" width="90">
              <template #default="{ row }"><el-input-number v-model="row.std_hours" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="段取H" width="90">
              <template #default="{ row }"><el-input-number v-model="row.setup_hours" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="賃率/H" width="100">
              <template #default="{ row }"><el-input-number v-model="row.labor_rate_per_hour" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="金額(任意)" width="100">
              <template #default="{ row }"><el-input-number v-model="row.amount" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column width="70" fixed="right">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="productForm.labor_lines.splice($index, 1)">削除</el-button>
              </template>
            </el-table-column>
          </el-table>
          </div>
        </el-tab-pane>
        <el-tab-pane label="製造間接" name="oh">
          <div class="pd-pane-actions">
            <el-button size="small" type="primary" plain @click="addOhLine"><el-icon><Plus /></el-icon> 行追加</el-button>
          </div>
          <div class="pd-table-scroll">
          <el-table :data="productForm.overhead_lines" border size="small" class="pd-table">
            <el-table-column label="ｺｽﾄｾﾝﾀｰ" width="110">
              <template #default="{ row }"><el-input v-model="row.cost_center_cd" /></template>
            </el-table-column>
            <el-table-column label="基準" width="130">
              <template #default="{ row }">
                <el-select v-model="row.allocation_basis" size="small">
                  <el-option label="machine_hours" value="machine_hours" />
                  <el-option label="labor_hours" value="labor_hours" />
                  <el-option label="direct_labor_cost" value="direct_labor_cost" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column label="基準量/台" width="100">
              <template #default="{ row }"><el-input-number v-model="row.basis_qty_per_unit" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="間接率" width="100">
              <template #default="{ row }"><el-input-number v-model="row.overhead_rate" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column label="金額(任意)" width="100">
              <template #default="{ row }"><el-input-number v-model="row.amount" :controls="false" class="wfull" /></template>
            </el-table-column>
            <el-table-column width="70" fixed="right">
              <template #default="{ $index }">
                <el-button type="danger" link size="small" @click="productForm.overhead_lines.splice($index, 1)">削除</el-button>
              </template>
            </el-table-column>
          </el-table>
          </div>
        </el-tab-pane>
        <el-tab-pane label="単位標準" name="hdr">
          <div class="pd-hdr-grid">
            <div class="pd-hdr-item">
              <span class="pd-hdr-k">直接材料</span>
              <el-input-number v-model="productForm.material_cost_std" :min="0" :precision="2" controls-position="right" class="pd-num" />
            </div>
            <div class="pd-hdr-item">
              <span class="pd-hdr-k">直接労務</span>
              <el-input-number v-model="productForm.labor_cost_std" :min="0" :precision="2" controls-position="right" class="pd-num" />
            </div>
            <div class="pd-hdr-item">
              <span class="pd-hdr-k">製造間接</span>
              <el-input-number v-model="productForm.overhead_cost_std" :min="0" :precision="2" controls-position="right" class="pd-num" />
            </div>
          </div>
          <p class="pd-hdr-note">円／単位。明細がある場合は明細集計が優先されます。</p>
        </el-tab-pane>
      </el-tabs>
      </div>

      <template #footer>
        <div class="pd-footer">
          <el-button @click="productDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" :loading="savingProduct" @click="saveProduct">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 会計期間新規 -->
    <el-dialog v-model="periodDialogVisible" title="会計期間（月）新規" width="400px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="年月" required>
          <el-date-picker v-model="newPeriodMonth" type="month" value-format="YYYY-MM" placeholder="YYYY-MM" />
        </el-form-item>
        <el-form-item label="備考">
          <el-input v-model="newPeriodNotes" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="periodDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" @click="saveNewPeriod">作成</el-button>
      </template>
    </el-dialog>

    <!-- 月次品目行 -->
    <el-dialog
      v-model="periodLineDialogVisible"
      :title="periodLineForm.lineId ? '月次品目 編集' : '月次品目 追加'"
      width="720px"
      destroy-on-close
    >
      <el-form label-width="140px">
        <el-form-item label="品番" required>
          <el-select
            v-model="periodLineForm.product_cd"
            filterable
            remote
            :remote-method="searchProducts"
            :loading="loadingMasterProducts"
            placeholder="検索"
            style="width: 100%"
            :disabled="!!periodLineForm.lineId"
            @change="onPeriodProductChange"
          >
            <el-option v-for="p in masterProductOptions" :key="p.product_cd" :label="`${p.product_cd} ${p.product_name}`" :value="p.product_cd" />
          </el-select>
        </el-form-item>
        <el-form-item label="完成数量">
          <el-input-number v-model="periodLineForm.finished_good_qty" :min="0" />
        </el-form-item>
        <el-form-item label="仕掛約当">
          <el-input-number v-model="periodLineForm.wip_equivalent_qty" :min="0" />
        </el-form-item>
        <el-form-item label="実際材料費">
          <el-input-number v-model="periodLineForm.actual_material_cost" :precision="2" />
        </el-form-item>
        <el-form-item label="実際労務費">
          <el-input-number v-model="periodLineForm.actual_labor_cost" :precision="2" />
        </el-form-item>
        <el-form-item label="実際間接費">
          <el-input-number v-model="periodLineForm.actual_overhead_cost" :precision="2" />
        </el-form-item>
        <el-divider>差異分解（実際−標準許容との整合を確認）</el-divider>
        <el-form-item label="材料価格差異">
          <el-input-number v-model="periodLineForm.variance_material_price" :precision="2" />
        </el-form-item>
        <el-form-item label="材料数量差異">
          <el-input-number v-model="periodLineForm.variance_material_qty" :precision="2" />
        </el-form-item>
        <el-form-item label="賃率差異">
          <el-input-number v-model="periodLineForm.variance_labor_rate" :precision="2" />
        </el-form-item>
        <el-form-item label="作業時間差異">
          <el-input-number v-model="periodLineForm.variance_labor_efficiency" :precision="2" />
        </el-form-item>
        <el-form-item label="間接予算差異">
          <el-input-number v-model="periodLineForm.variance_moh_budget" :precision="2" />
        </el-form-item>
        <el-form-item label="操業度差異">
          <el-input-number v-model="periodLineForm.variance_moh_capacity" :precision="2" />
        </el-form-item>
        <el-form-item label="間接能率差異">
          <el-input-number v-model="periodLineForm.variance_moh_efficiency" :precision="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="periodLineDialogVisible = false">キャンセル</el-button>
        <el-button type="primary" :loading="savingPeriodLine" @click="savePeriodLine">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, InfoFilled } from '@element-plus/icons-vue'
import {
  fetchStandardCostVersions,
  createStandardCostVersion,
  updateStandardCostVersion,
  deleteStandardCostVersion,
  fetchProductStandards,
  getProductStandard,
  createProductStandard,
  updateProductStandard,
  deleteProductStandard,
  fetchCostPeriods,
  createCostPeriod,
  fetchPeriodProducts,
  createPeriodProduct,
  updatePeriodProduct,
  deletePeriodProduct,
  recalculatePeriodProduct,
  type CostStandardVersion,
  type StandardCostListItem,
  type CostAccountingPeriod,
  type CostPeriodProductLine,
} from '@/api/erp/standardCost'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'

const activeTab = ref('products')

const loadingVersions = ref(false)
const versions = ref<CostStandardVersion[]>([])

const loadingProducts = ref(false)
const productList = ref<StandardCostListItem[]>([])
const productFilters = reactive({ version_id: undefined as number | undefined, product_cd: '' })
const productPagination = reactive({ page: 1, pageSize: 20, total: 0 })

const periods = ref<CostAccountingPeriod[]>([])
const selectedPeriod = ref<CostAccountingPeriod | null>(null)
const loadingPeriodProducts = ref(false)
const periodProducts = ref<CostPeriodProductLine[]>([])

const versionDialogVisible = ref(false)
const versionForm = reactive({
  id: 0,
  code: '',
  fiscal_year: new Date().getFullYear(),
  status: 'draft',
  effective_from: '',
  effective_to: '' as string | null,
  remarks: '',
})

const productDialogVisible = ref(false)
const productInnerTab = ref('mat')
const savingProduct = ref(false)
const productForm = reactive({
  headerId: 0,
  version_id: 0,
  product_cd: '',
  product_name: '' as string | null,
  source: 'manual',
  material_lines: [] as Record<string, unknown>[],
  labor_lines: [] as Record<string, unknown>[],
  overhead_lines: [] as Record<string, unknown>[],
  material_cost_std: undefined as number | undefined,
  labor_cost_std: undefined as number | undefined,
  overhead_cost_std: undefined as number | undefined,
})

const masterProductOptions = ref<Product[]>([])
const loadingMasterProducts = ref(false)

/** 製品標準原価タブの製品名フィルター用 */
const productFilterOptions = ref<Product[]>([])
const loadingProductFilter = ref(false)

function productFilterOptionLabel(p: Product) {
  const name = (p.product_name || '').trim() || '—'
  return `${name} · ${p.product_cd}`
}

async function searchProductFilter(q: string) {
  const keyword = (q || '').trim()
  if (!keyword) {
    productFilterOptions.value = []
    return
  }
  loadingProductFilter.value = true
  try {
    const res = await getProductList({ keyword, pageSize: 80, status: 'active' })
    productFilterOptions.value = res.data?.list ?? res.list ?? []
  } catch {
    productFilterOptions.value = []
  } finally {
    loadingProductFilter.value = false
  }
}

function onClearProductFilter() {
  productFilters.product_cd = ''
  productFilterOptions.value = []
}

const periodDialogVisible = ref(false)
const newPeriodMonth = ref('')
const newPeriodNotes = ref('')

const periodLineDialogVisible = ref(false)
const savingPeriodLine = ref(false)
const periodLineForm = reactive({
  lineId: 0,
  product_cd: '',
  product_name: '' as string | null,
  finished_good_qty: 0,
  wip_equivalent_qty: 0,
  actual_material_cost: undefined as number | undefined,
  actual_labor_cost: undefined as number | undefined,
  actual_overhead_cost: undefined as number | undefined,
  variance_material_price: 0,
  variance_material_qty: 0,
  variance_labor_rate: 0,
  variance_labor_efficiency: 0,
  variance_moh_budget: 0,
  variance_moh_capacity: 0,
  variance_moh_efficiency: 0,
})

function money(v: number | null | undefined) {
  const n = Number(v ?? 0)
  return Number.isFinite(n) ? n.toLocaleString('ja-JP', { maximumFractionDigits: 2 }) : '0'
}

function signedMoney(v: number) {
  const n = Number(v)
  const s = n >= 0 ? '+' : ''
  return `${s}¥${money(Math.abs(n))}`
}

function varClass(v: number) {
  return v <= 0 ? 'var-fav' : 'var-unfav'
}

async function loadVersions() {
  loadingVersions.value = true
  try {
    versions.value = await fetchStandardCostVersions()
    if (!productFilters.version_id && versions.value.length) {
      const active = versions.value.find((x) => x.status === 'active')
      productFilters.version_id = (active || versions.value[0]).id
    }
  } catch {
    versions.value = []
    ElMessage.error('標準原価バージョンの取得に失敗しました（マイグレーション未適用の可能性）')
  } finally {
    loadingVersions.value = false
  }
}

function onVersionForProductsChange() {
  productPagination.page = 1
  productFilters.product_cd = ''
  productFilterOptions.value = []
  loadProductStandards()
}

async function loadProductStandards() {
  if (!productFilters.version_id) {
    productList.value = []
    return
  }
  loadingProducts.value = true
  try {
    const res = await fetchProductStandards({
      version_id: productFilters.version_id,
      product_cd: productFilters.product_cd || undefined,
      page: productPagination.page,
      page_size: productPagination.pageSize,
    })
    productList.value = res.items
    productPagination.total = res.total
    // リモート select の表示用：フィルタ後の行からラベル候補を補完
    if (productFilters.product_cd) {
      const hit = res.items.find((r) => r.product_cd === productFilters.product_cd)
      if (hit && !productFilterOptions.value.some((p) => p.product_cd === hit.product_cd)) {
        productFilterOptions.value = [
          { product_cd: hit.product_cd, product_name: hit.product_name || '' } as Product,
          ...productFilterOptions.value,
        ]
      }
    }
  } catch {
    productList.value = []
    ElMessage.error('製品標準原価の取得に失敗しました')
  } finally {
    loadingProducts.value = false
  }
}

function openVersionDialog(row?: CostStandardVersion) {
  if (row) {
    versionForm.id = row.id
    versionForm.code = row.code
    versionForm.fiscal_year = row.fiscal_year
    versionForm.status = row.status
    versionForm.effective_from = row.effective_from?.slice(0, 10) || ''
    versionForm.effective_to = row.effective_to?.slice(0, 10) || null
    versionForm.remarks = row.remarks || ''
  } else {
    resetVersionForm()
    versionForm.fiscal_year = new Date().getFullYear()
    versionForm.effective_from = `${new Date().getFullYear()}-04-01`
  }
  versionDialogVisible.value = true
}

function resetVersionForm() {
  versionForm.id = 0
  versionForm.code = ''
  versionForm.fiscal_year = new Date().getFullYear()
  versionForm.status = 'draft'
  versionForm.effective_from = ''
  versionForm.effective_to = null
  versionForm.remarks = ''
}

async function saveVersion() {
  if (!versionForm.code || !versionForm.effective_from) {
    ElMessage.warning('コードと適用開始日は必須です')
    return
  }
  try {
    if (versionForm.id) {
      await updateStandardCostVersion(versionForm.id, {
        code: versionForm.code,
        fiscal_year: versionForm.fiscal_year,
        status: versionForm.status,
        effective_from: versionForm.effective_from,
        effective_to: versionForm.effective_to,
        remarks: versionForm.remarks || null,
      })
      ElMessage.success('更新しました')
    } else {
      await createStandardCostVersion({
        code: versionForm.code,
        fiscal_year: versionForm.fiscal_year,
        status: versionForm.status,
        effective_from: versionForm.effective_from,
        effective_to: versionForm.effective_to || undefined,
        remarks: versionForm.remarks || undefined,
      })
      ElMessage.success('作成しました')
    }
    versionDialogVisible.value = false
    await loadVersions()
  } catch {
    /* interceptor */
  }
}

async function onDeleteVersion(row: CostStandardVersion) {
  try {
    await ElMessageBox.confirm(`バージョン「${row.code}」を削除しますか？紐づく標準原価も削除されます。`, '確認', {
      type: 'warning',
    })
    await deleteStandardCostVersion(row.id)
    ElMessage.success('削除しました')
    await loadVersions()
  } catch {
    /* cancel */
  }
}

function emptyMatLine(no: number) {
  return {
    line_no: no,
    material_cd: '',
    material_name: '',
    qty_per_unit: 0,
    scrap_pct: 0,
    standard_unit_price: 0,
    amount: 0,
  }
}
function emptyLabLine(no: number) {
  return {
    line_no: no,
    process_cd: '',
    process_name: '',
    std_hours: 0,
    setup_hours: 0,
    labor_rate_per_hour: 0,
    amount: 0,
  }
}
function emptyOhLine(no: number) {
  return {
    line_no: no,
    cost_center_cd: '',
    allocation_basis: 'machine_hours',
    basis_qty_per_unit: 0,
    overhead_rate: 0,
    amount: 0,
  }
}

function addMatLine() {
  productForm.material_lines.push(emptyMatLine(productForm.material_lines.length + 1))
}
function addLabLine() {
  productForm.labor_lines.push(emptyLabLine(productForm.labor_lines.length + 1))
}
function addOhLine() {
  productForm.overhead_lines.push(emptyOhLine(productForm.overhead_lines.length + 1))
}

async function searchProducts(q: string) {
  if (!q || q.length < 1) {
    masterProductOptions.value = []
    return
  }
  loadingMasterProducts.value = true
  try {
    const res = await getProductList({ keyword: q, pageSize: 50, status: 'active' })
    const list = res.data?.list ?? res.list ?? []
    masterProductOptions.value = list
  } catch {
    masterProductOptions.value = []
  } finally {
    loadingMasterProducts.value = false
  }
}

function resetProductForm() {
  productForm.headerId = 0
  productForm.version_id = productFilters.version_id || 0
  productForm.product_cd = ''
  productForm.product_name = ''
  productForm.source = 'manual'
  productForm.material_lines = []
  productForm.labor_lines = []
  productForm.overhead_lines = []
  productForm.material_cost_std = undefined
  productForm.labor_cost_std = undefined
  productForm.overhead_cost_std = undefined
  productInnerTab.value = 'mat'
}

async function openProductDialog(row?: StandardCostListItem) {
  if (!productFilters.version_id) {
    ElMessage.warning('先にバージョンを選択してください')
    return
  }
  resetProductForm()
  productForm.version_id = productFilters.version_id
  if (row) {
    try {
      const d = await getProductStandard(row.id)
      productForm.headerId = d.id
      productForm.version_id = d.version_id
      productForm.product_cd = d.product_cd
      productForm.product_name = d.product_name || ''
      productForm.source = d.source || 'manual'
      productForm.material_cost_std = d.material_cost_std
      productForm.labor_cost_std = d.labor_cost_std
      productForm.overhead_cost_std = d.overhead_cost_std
      productForm.material_lines = (d.material_lines || []).map((x, i) => ({
        line_no: x.line_no ?? i + 1,
        material_cd: x.material_cd,
        material_name: x.material_name,
        qty_per_unit: Number(x.qty_per_unit),
        scrap_pct: Number(x.scrap_pct),
        standard_unit_price: Number(x.standard_unit_price),
        amount: Number(x.amount),
      }))
      productForm.labor_lines = (d.labor_lines || []).map((x, i) => ({
        line_no: x.line_no ?? i + 1,
        process_cd: x.process_cd,
        process_name: x.process_name,
        std_hours: Number(x.std_hours),
        setup_hours: Number(x.setup_hours),
        labor_rate_per_hour: Number(x.labor_rate_per_hour),
        amount: Number(x.amount),
      }))
      productForm.overhead_lines = (d.overhead_lines || []).map((x, i) => ({
        line_no: x.line_no ?? i + 1,
        cost_center_cd: x.cost_center_cd,
        allocation_basis: x.allocation_basis,
        basis_qty_per_unit: Number(x.basis_qty_per_unit),
        overhead_rate: Number(x.overhead_rate),
        amount: Number(x.amount),
      }))
      masterProductOptions.value = [{ product_cd: d.product_cd, product_name: d.product_name || '' } as Product]
    } catch {
      return
    }
  }
  productDialogVisible.value = true
}

function onProductCdChange(cd: string) {
  const p = masterProductOptions.value.find((x) => x.product_cd === cd)
  productForm.product_name = p?.product_name || ''
}

async function saveProduct() {
  if (!productForm.version_id || !productForm.product_cd) {
    ElMessage.warning('バージョンと品番は必須です')
    return
  }
  savingProduct.value = true
  try {
    const payload = {
      version_id: productForm.version_id,
      product_cd: productForm.product_cd,
      product_name: productForm.product_name || undefined,
      source: productForm.source,
      material_lines: productForm.material_lines,
      labor_lines: productForm.labor_lines,
      overhead_lines: productForm.overhead_lines,
      material_cost_std: productForm.material_cost_std ?? null,
      labor_cost_std: productForm.labor_cost_std ?? null,
      overhead_cost_std: productForm.overhead_cost_std ?? null,
    }
    if (productForm.headerId) {
      await updateProductStandard(productForm.headerId, payload)
      ElMessage.success('更新しました')
    } else {
      await createProductStandard(payload)
      ElMessage.success('登録しました')
    }
    productDialogVisible.value = false
    await loadProductStandards()
  } catch {
    /* */
  } finally {
    savingProduct.value = false
  }
}

async function onDeleteProduct(row: StandardCostListItem) {
  try {
    await ElMessageBox.confirm(`品番 ${row.product_cd} の標準原価を削除しますか？`, '確認', { type: 'warning' })
    await deleteProductStandard(row.id)
    ElMessage.success('削除しました')
    await loadProductStandards()
  } catch {
    /* */
  }
}

async function loadPeriods() {
  try {
    periods.value = await fetchCostPeriods()
  } catch {
    periods.value = []
  }
}

function selectPeriod(p: CostAccountingPeriod) {
  selectedPeriod.value = p
  loadPeriodProducts()
}

async function loadPeriodProducts() {
  if (!selectedPeriod.value) return
  loadingPeriodProducts.value = true
  try {
    periodProducts.value = await fetchPeriodProducts(selectedPeriod.value.id)
  } catch {
    periodProducts.value = []
    ElMessage.error('月次データの取得に失敗しました')
  } finally {
    loadingPeriodProducts.value = false
  }
}

function openPeriodDialog() {
  newPeriodMonth.value = ''
  newPeriodNotes.value = ''
  periodDialogVisible.value = true
}

async function saveNewPeriod() {
  if (!newPeriodMonth.value) {
    ElMessage.warning('年月を選択してください')
    return
  }
  try {
    const p = await createCostPeriod({ year_month: newPeriodMonth.value, notes: newPeriodNotes.value || undefined })
    ElMessage.success('作成しました')
    periodDialogVisible.value = false
    await loadPeriods()
    selectedPeriod.value = p
    await loadPeriodProducts()
  } catch {
    /* */
  }
}

function resetPeriodLineForm() {
  periodLineForm.lineId = 0
  periodLineForm.product_cd = ''
  periodLineForm.product_name = ''
  periodLineForm.finished_good_qty = 0
  periodLineForm.wip_equivalent_qty = 0
  periodLineForm.actual_material_cost = undefined
  periodLineForm.actual_labor_cost = undefined
  periodLineForm.actual_overhead_cost = undefined
  periodLineForm.variance_material_price = 0
  periodLineForm.variance_material_qty = 0
  periodLineForm.variance_labor_rate = 0
  periodLineForm.variance_labor_efficiency = 0
  periodLineForm.variance_moh_budget = 0
  periodLineForm.variance_moh_capacity = 0
  periodLineForm.variance_moh_efficiency = 0
}

function openPeriodLineDialog(row?: CostPeriodProductLine) {
  resetPeriodLineForm()
  if (row) {
    periodLineForm.lineId = row.id
    periodLineForm.product_cd = row.product_cd
    periodLineForm.product_name = row.product_name || ''
    periodLineForm.finished_good_qty = row.finished_good_qty
    periodLineForm.wip_equivalent_qty = row.wip_equivalent_qty
    periodLineForm.actual_material_cost = row.actual_material_cost ?? undefined
    periodLineForm.actual_labor_cost = row.actual_labor_cost ?? undefined
    periodLineForm.actual_overhead_cost = row.actual_overhead_cost ?? undefined
    periodLineForm.variance_material_price = row.variance_material_price
    periodLineForm.variance_material_qty = row.variance_material_qty
    periodLineForm.variance_labor_rate = row.variance_labor_rate
    periodLineForm.variance_labor_efficiency = row.variance_labor_efficiency
    periodLineForm.variance_moh_budget = row.variance_moh_budget
    periodLineForm.variance_moh_capacity = row.variance_moh_capacity
    periodLineForm.variance_moh_efficiency = row.variance_moh_efficiency
    masterProductOptions.value = [{ product_cd: row.product_cd, product_name: row.product_name || '' } as Product]
  }
  periodLineDialogVisible.value = true
}

function onPeriodProductChange(cd: string) {
  const p = masterProductOptions.value.find((x) => x.product_cd === cd)
  periodLineForm.product_name = p?.product_name || ''
}

async function savePeriodLine() {
  if (!selectedPeriod.value || !periodLineForm.product_cd) {
    ElMessage.warning('品番は必須です')
    return
  }
  savingPeriodLine.value = true
  try {
    const body = {
      product_cd: periodLineForm.product_cd,
      product_name: periodLineForm.product_name || undefined,
      finished_good_qty: periodLineForm.finished_good_qty,
      wip_equivalent_qty: periodLineForm.wip_equivalent_qty,
      actual_material_cost: periodLineForm.actual_material_cost ?? null,
      actual_labor_cost: periodLineForm.actual_labor_cost ?? null,
      actual_overhead_cost: periodLineForm.actual_overhead_cost ?? null,
      variance_material_price: periodLineForm.variance_material_price,
      variance_material_qty: periodLineForm.variance_material_qty,
      variance_labor_rate: periodLineForm.variance_labor_rate,
      variance_labor_efficiency: periodLineForm.variance_labor_efficiency,
      variance_moh_budget: periodLineForm.variance_moh_budget,
      variance_moh_capacity: periodLineForm.variance_moh_capacity,
      variance_moh_efficiency: periodLineForm.variance_moh_efficiency,
    }
    if (periodLineForm.lineId) {
      await updatePeriodProduct(selectedPeriod.value.id, periodLineForm.lineId, body)
      ElMessage.success('更新しました')
    } else {
      await createPeriodProduct(selectedPeriod.value.id, body)
      ElMessage.success('追加しました（標準許容を自動計算しました）')
    }
    periodLineDialogVisible.value = false
    await loadPeriodProducts()
  } catch {
    /* */
  } finally {
    savingPeriodLine.value = false
  }
}

async function onRecalcLine(row: CostPeriodProductLine) {
  if (!selectedPeriod.value) return
  try {
    await recalculatePeriodProduct(selectedPeriod.value.id, row.id)
    ElMessage.success('標準許容を再計算しました')
    await loadPeriodProducts()
  } catch {
    /* */
  }
}

async function onDeletePeriodLine(row: CostPeriodProductLine) {
  if (!selectedPeriod.value) return
  try {
    await ElMessageBox.confirm(`品番 ${row.product_cd} の行を削除しますか？`, '確認', { type: 'warning' })
    await deletePeriodProduct(selectedPeriod.value.id, row.id)
    ElMessage.success('削除しました')
    await loadPeriodProducts()
  } catch {
    /* */
  }
}

function onTabChange(name: string | number) {
  if (name === 'versions') loadVersions()
  if (name === 'products') {
    loadVersions().then(() => loadProductStandards())
  }
  if (name === 'periods') loadPeriods()
}

onMounted(async () => {
  await loadVersions()
  await loadProductStandards()
})
</script>

<style scoped>
.standard-costing { padding: 16px 20px; }

.page-hero {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px; margin-bottom: 14px; border-radius: 12px;
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  color: #1a3e2a;
}
.hero-text h2 { margin: 0 0 4px; font-size: 20px; font-weight: 700; }
.hero-text p { margin: 0; font-size: 13px; opacity: .75; }
.hero-nav { display: flex; gap: 8px; flex-shrink: 0; }
.nav-chip {
  padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600;
  background: rgba(255,255,255,.35); color: #1a3e2a; text-decoration: none; transition: background .2s;
}
.nav-chip:hover { background: rgba(255,255,255,.55); }
.nav-chip.accent { background: rgba(255,255,255,.88); }
.nav-chip.accent:hover { background: #fff; }

.main-tabs { margin-top: 4px; }
.main-tabs :deep(.el-tabs__header) { margin-bottom: 12px; }

.filter-card { margin-bottom: 12px; }
.filter-card :deep(.el-card__body) { padding: 12px 16px; }
.filter-card :deep(.el-form-item) { margin-bottom: 0; }

.toolbar {
  margin-bottom: 12px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
}
.pagination-wrapper { margin-top: 12px; display: flex; justify-content: flex-end; }

.mb8 { margin-bottom: 8px; }
.mb12 { margin-bottom: 12px; }
.ml8 { margin-left: 8px; }
.wfull { width: 100%; }

.period-list-card :deep(.el-card__header) {
  display: flex; align-items: center; justify-content: space-between; padding: 12px 14px;
}
.period-list-card :deep(.el-card__body) { padding: 10px; }
.period-item {
  padding: 9px 12px; border-radius: 8px; cursor: pointer;
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 5px; border: 1px solid #ebeef5; transition: all .15s;
}
.period-item:hover { background: #f5f7fa; border-color: #d9ecff; }
.period-item.active { border-color: #409eff; background: #ecf5ff; box-shadow: 0 0 0 2px rgba(64,158,255,.12); }
.period-ym { font-weight: 600; font-size: 14px; }
.period-title { font-weight: 600; margin-right: auto; font-size: 14px; }
.var-fav { color: #67c23a; font-weight: 600; }
.var-unfav { color: #f56c6c; font-weight: 600; }

:deep(.el-card) { border-radius: 10px; }
:deep(.el-card__body) { padding: 14px; }
:deep(.el-table th .cell) { font-size: 12px; }

.product-name-select { width: min(320px, 100%); }

/* 標準原価 製品ダイアログ */
.product-std-dialog :deep(.el-dialog__header) {
  padding: 12px 18px 10px;
  margin-right: 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, #fafbfc 0%, #fff 100%);
}
.product-std-dialog :deep(.el-dialog__title) {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #303133;
}
.product-std-dialog :deep(.el-dialog__body) {
  padding: 10px 16px 8px;
}
.product-std-dialog :deep(.el-dialog__footer) {
  padding: 0;
  border-top: none;
}

.pd-shell {
  margin-top: 2px;
}
.pd-head {
  margin-bottom: 8px;
  padding: 10px 12px;
  border-radius: 10px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
}
.pd-head-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 12px 16px;
}
.pd-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.pd-field-label {
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.pd-field-label .req {
  color: #f56c6c;
  margin-left: 2px;
}
.pd-field-product {
  flex: 1;
  min-width: 200px;
}
.pd-product-select {
  width: 100%;
  max-width: 420px;
}
.pd-field-src {
  flex: 0 0 auto;
}
.pd-src-select {
  width: 130px;
}
.pd-product-readonly {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 32px;
  padding: 4px 0;
}
.pd-pname {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}
.pd-hint {
  margin: 8px 0 0;
  padding: 6px 10px;
  font-size: 12px;
  line-height: 1.45;
  color: #64748b;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
  border: 1px dashed #cbd5e1;
  display: flex;
  align-items: flex-start;
  gap: 6px;
}
.pd-hint-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: #3b82f6;
}

.pd-tabs :deep(.el-tabs__header) {
  margin: 0 0 6px;
}
.pd-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
}
.pd-tabs :deep(.el-tabs__item) {
  font-size: 13px;
  height: 34px;
  line-height: 34px;
  padding: 0 12px;
}
.pd-tabs :deep(.el-tabs__content) {
  padding-top: 4px;
}
.pd-pane-actions {
  margin-bottom: 6px;
}
.pd-table-scroll {
  max-height: min(38vh, 300px);
  overflow: auto;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
}
.pd-table :deep(.el-table__cell) {
  padding: 4px 0;
}
.pd-table :deep(th.el-table__cell) {
  padding: 6px 0;
  font-size: 12px;
}

.pd-hdr-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px 12px;
  padding: 4px 0 6px;
}
.pd-hdr-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}
.pd-hdr-k {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
}
.pd-num {
  width: 100%;
}
.pd-hdr-note {
  margin: 6px 0 0;
  font-size: 11px;
  color: #94a3b8;
}

.pd-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 16px 14px;
  border-top: 1px solid var(--el-border-color-lighter);
  background: #fafafa;
}

@media (max-width: 640px) {
  .pd-hdr-grid {
    grid-template-columns: 1fr;
  }
}
</style>
