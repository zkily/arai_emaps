<template>
  <div class="cutting-instruction-container">
    <div class="page-header">
      <div class="header-left">
        <div class="header-title">
          <!-- <span class="page-header-badge">生産指示</span> -->
          <h1>切断・面取指示管理</h1>
          <p class="header-desc">ロット一覧・切断指示・面取指示・カンバン発行を一括管理</p>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" size="small" class="done-list-btn done-list-btn--cutting" @click="openCuttingDoneDialog">切断済リスト</el-button>
        <el-button type="success" size="small" class="done-list-btn done-list-btn--chamfering" @click="openChamferingDoneDialog">面取済リスト</el-button>
      </div>
    </div>

    <!-- 上部：生産ロット 50% + 右侧 50% -->
    <div class="plan-row">
      <div class="plan-section plan-section-left">
        <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div class="section-title">
              <el-icon size="18"><Calendar /></el-icon>
              <span class="section-title-label">生産ロット一覧</span>
              <el-button
                type="default"
                size="small"
                class="title-toolbar-btn title-toolbar-btn--data"
                @click="openDataManagementDialog"
              >
                データ管理
              </el-button>
              <el-button
                type="default"
                size="small"
                class="title-toolbar-btn title-toolbar-btn--sync"
                :loading="syncLengthsFromProductsLoading"
                @click="syncLengthsFromProducts"
              >
                <el-icon class="title-toolbar-sync-icon"><Refresh /></el-icon>
                寸法マスタ同期
              </el-button>
            </div>
          </div>
        </template>

        <div class="search-section">
          <el-form :model="planSearchForm" inline size="small" class="compact-form">
            <el-form-item label="設備" class="compact-form-item">
              <el-select
                v-model="planSearchForm.equipment"
                placeholder="設備を選択"
                clearable
                popper-class="equipment-select-dropdown"
                style="width: 120px"
                @change="onPlanEquipmentChange"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.machine_name"
                  :label="machine.machine_name"
                  :value="machine.machine_name"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="製品" class="compact-form-item">
              <el-select
                v-model="planSearchForm.product_name"
                placeholder="全部"
                clearable
                filterable
                popper-class="equipment-select-dropdown"
                style="width: 140px"
                @change="onPlanProductOrMaterialFilterChange"
              >
                <el-option label="（全部）" value="" />
                <el-option
                  v-for="name in planProductNameOptions"
                  :key="name"
                  :label="name"
                  :value="name"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="材料" class="compact-form-item">
              <el-select
                v-model="planSearchForm.material_name"
                placeholder="全部"
                clearable
                filterable
                popper-class="equipment-select-dropdown"
                style="width: 140px"
                @change="onPlanProductOrMaterialFilterChange"
              >
                <el-option label="（全部）" value="" />
                <el-option
                  v-for="name in planMaterialNameOptions"
                  :key="name"
                  :label="name"
                  :value="name"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="small" @click="openNewRecordDialog(false)">+ 新規追加</el-button>
              <el-button type="default" size="small" class="btn-trial-add" @click="openNewRecordDialog(true)">試作追加</el-button>
            </el-form-item>
          </el-form>
        </div>

        <div
          v-loading="planLoading"
          class="plan-batch-table-wrap"
          :class="{ 'drop-zone-active': dragOverZone === 'batchList' }"
          @drop="onDropBatchList"
          @dragover="onDragOver($event, 'batchList')"
          @dragenter="onDragEnter('batchList')"
          @dragleave="onDragLeave('batchList')"
        >
          <div v-if="dragOverZone === 'batchList'" class="plan-batch-drop-hint">ここにドロップで切断指示をロットへ戻す</div>
          <div v-show="planListForTable.length > 0" class="plan-batch-table-inner">
            <div class="plan-batch-thead">
              <div class="plan-batch-tr">
                <div class="plan-batch-th">開始日</div>
                <div class="plan-batch-th">ライン</div>
                <div class="plan-batch-th">順位</div>
                <div class="plan-batch-th">製品名</div>
                <div class="plan-batch-th">計画数</div>
                <div class="plan-batch-th">原材料</div>
                <div class="plan-batch-th">ロット数</div>
                <div class="plan-batch-th">No</div>
                <div class="plan-batch-th">生産数</div>
                <div class="plan-batch-th">材料区分</div>
                <div class="plan-batch-th">材料使用数</div>
                <div class="plan-batch-th plan-batch-th-actions">操作</div>
              </div>
            </div>
            <div class="plan-batch-tbody">
              <div
                v-for="(row, idx) in planListForTable"
                :key="row.id ?? `plan-${idx}`"
                class="plan-batch-tr plan-batch-data-row"
                :class="[getPlanBatchPriorityClass(row.priority_order), { 'plan-batch-row-selected': selectedProductCd === row.product_cd }]"
                draggable="true"
                :data-plan-index="String((planPagination.currentPage - 1) * planPagination.pageSize + idx)"
                @click.stop="onPlanCardClick(row)"
                @dblclick.stop="openPlanEditDialog(row)"
                @dragstart="onPlanCardDragStart($event, row)"
                @dragend="onPlanCardDragEnd"
              >
                <div class="plan-batch-td">{{ formatDateOnly(String(row.start_date ?? '')) || '-' }}</div>
                <div class="plan-batch-td">{{ row.production_line ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.priority_order ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.product_name || row.product_cd || '-' }}</div>
                <div class="plan-batch-td">{{ row.planned_quantity ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.material_name ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.production_lot_size ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.lot_number ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.actual_production_quantity ?? '-' }}</div>
                <div class="plan-batch-td">
                  <el-switch
                    :model-value="(row as { use_material_stock_sub?: number }).use_material_stock_sub === 1 ? 1 : 0"
                    :active-value="1"
                    :inactive-value="0"
                    size="small"
                    @change="val => saveDataManagementCell(row, 'use_material_stock_sub', val)"
                  />
                </div>
                <div class="plan-batch-td" @dblclick.stop="onDblClickUsageCount(row)">
                  {{ formatUsageCountDisplay(row as { usage_count?: number | null }) }}
                </div>
                <div class="plan-batch-td plan-batch-td-actions">
                  <el-button
                    type="primary"
                    link
                    size="small"
                    title="複製"
                    :loading="planBatchActionLoading === row.id"
                    @click.stop="copyPlanBatch(row)"
                  >
                    <el-icon><DocumentCopy /></el-icon>
                  </el-button>
                  <el-button
                    type="danger"
                    link
                    size="small"
                    title="削除"
                    :loading="planBatchActionLoading === row.id"
                    @click.stop="deletePlanBatch(row)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          <div v-if="!planListForTable.length && !planLoading" class="plan-batch-empty">データなし</div>
        </div>

        <div class="pagination-wrap">
          <el-pagination
            v-model:current-page="planPagination.currentPage"
            v-model:page-size="planPagination.pageSize"
            :page-sizes="[10, 20, 50]"
            :total="planListFiltered.length"
            size="small"
            layout="total, sizes, prev, pager, next"
            @size-change="handlePlanSizeChange"
            @current-change="handlePlanCurrentChange"
          />
        </div>
      </el-card>
      </div>
      <div class="plan-section-right right-panel">
        <!-- 上：製品情報（products 表・点击批次卡片时取得） -->
        <div class="right-panel-top">
          <div class="right-panel-title">製品情報</div>
          <div v-if="!selectedProductCd" class="right-panel-placeholder">一覧で製品をクリック</div>
          <div v-else v-loading="productDetailLoading" class="product-detail-body">
            <template v-if="productDetail">
              <ul class="product-detail-list">
                <li class="product-detail-list-item"><span class="detail-label">製品CD</span><span class="detail-value">{{ productDetail.product_cd ?? '-' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">製品名</span><span class="detail-value">{{ productDetail.product_name ?? '-' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">生産ロット</span><span class="detail-value">{{ productDetail.lot_size ?? '-' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">材料</span><span class="detail-value">{{ productDetail.material_name ?? productDetail.material_cd ?? '-' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">取数</span><span class="detail-value">{{ productDetail.take_count ?? '-' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">切断長</span><span class="detail-value">{{ productDetail.cut_length ?? '-' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">面取長</span><span class="detail-value">{{ (productDetail.chamfer_length != null && Number(productDetail.chamfer_length) !== 0) ? productDetail.chamfer_length : '--' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">展開長</span><span class="detail-value">{{ (productDetail.developed_length != null && Number(productDetail.developed_length) !== 0) ? productDetail.developed_length : '--' }}</span></li>
                <li class="product-detail-list-item"><span class="detail-label">端材長</span><span class="detail-value">{{ productDetail.scrap_length ?? '-' }}</span></li>
              </ul>
            </template>
            <div v-else-if="!productDetailLoading" class="right-panel-placeholder">該当製品なし</div>
          </div>
        </div>
        <!-- 下：設備能率（設備名に「切断」を含む行のみ） -->
        <div class="right-panel-bottom">
          <div class="right-panel-title">設備能率（切断）</div>
          <div v-if="!selectedProductCd" class="right-panel-placeholder">一覧で製品をクリック</div>
          <div v-else v-loading="equipmentEfficiencyLoading" class="equipment-efficiency-body">
            <el-table v-if="equipmentEfficiencyListFiltered.length" :data="equipmentEfficiencyListFiltered" size="small" max-height="220" class="efficiency-table">
              <el-table-column prop="machines_name" label="設備名" min-width="100" show-overflow-tooltip />
              <el-table-column prop="efficiency_rate" label="能率" width="80" align="right">
                <template #default="{ row }">{{ row.efficiency_rate != null ? Number(row.efficiency_rate) : '-' }}</template>
              </el-table-column>
            </el-table>
            <div v-else-if="!equipmentEfficiencyLoading" class="right-panel-placeholder">該当データなし（設備名に「切断」を含むもののみ表示）</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 下部：第1行＝切断指示（左）| 切断指示（右）、第2行＝面取指示 | カンバン発行 -->
    <div class="instruction-section">
      <!-- 第1行：今日 | 翌日（6:4） -->
      <div class="instruction-row instruction-two-cols instruction-cols-6-4">
        <div class="instruction-col cutting-management-section">
          <div class="cutting-mgmt-header">
            <div class="cutting-mgmt-header-left">
              <span class="cutting-mgmt-title">切断指示-今日</span>
              <div class="cutting-mgmt-date-wrap">
                <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftDateToday(-1)" />
                <el-date-picker
                  v-model="selectedDateToday"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="生産日"
                  size="small"
                  class="cutting-mgmt-date-picker"
                  @change="loadCuttingManagement"
                />
                <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftDateToday(1)" />
              </div>
              <div class="cutting-mgmt-machine-btns">
                <el-button
                  v-for="m in cuttingMachineOptionsFiltered"
                  :key="m.machine_name"
                  size="small"
                  :type="cuttingMachineFilter === m.machine_name ? 'primary' : 'default'"
                  @click="cuttingMachineFilter = m.machine_name; loadCuttingManagement()"
                >
                  {{ m.machine_name }}
                </el-button>
              </div>
            </div>
            <div class="cutting-mgmt-header-right cutting-mgmt-header-actions">
              <el-button type="default" size="small" :loading="printCuttingPlanLoading" @click="printCuttingPlanList">計画印刷</el-button>
              <el-button type="primary" size="small" :loading="issueCuttingInstructionSheetLoading" @click="issueCuttingInstructionSheet">指示書発行</el-button>
              <el-button type="success" size="small" :loading="confirmCuttingActualLoading" @click="confirmCuttingActual">実績確定</el-button>
            </div>
          </div>
          <div v-loading="cuttingManagementLoading" class="cutting-mgmt-table-wrap">
            <div class="cutting-mgmt-h-scroll">
            <div class="cutting-mgmt-table-inner">
              <div class="cutting-mgmt-thead">
                <div class="cutting-mgmt-tr">
                  <div class="cutting-mgmt-th">CD</div>
                  <div class="cutting-mgmt-th">ライン</div>
                  <div class="cutting-mgmt-th">生産日</div>
                  <div class="cutting-mgmt-th">切断機</div>
                  <div class="cutting-mgmt-th">製品名</div>
                  <div class="cutting-mgmt-th">原材料</div>
                  <div class="cutting-mgmt-th">生産数</div>
                  <div class="cutting-mgmt-th">不良</div>
                  <div class="cutting-mgmt-th">完了</div>
                  <div class="cutting-mgmt-th">生産順</div>
                  <div class="cutting-mgmt-th">生産時間</div>
                  <div class="cutting-mgmt-th">備考</div>
                  <div class="cutting-mgmt-th cutting-mgmt-th-actions">操作</div>
                </div>
              </div>
              <div
                class="cutting-mgmt-tbody-drop-zone"
                :class="{ 'drop-zone-active': dragOverZone === 'cuttingManagement' }"
                @drop="onDropCuttingManagement"
                @dragover="onDragOver($event, 'cuttingManagement')"
                @dragenter="onDragEnter('cuttingManagement')"
                @dragleave="onDragLeave('cuttingManagement')"
              >
                <div class="cutting-mgmt-drop-hint" v-if="dragOverZone === 'cuttingManagement'">ここにドロップでロットを切断指示へ移行</div>
                <div class="cutting-mgmt-tbody">
                <div
                  class="cutting-mgmt-drop-edge"
                  @drop.prevent="onDropCuttingRowToEdge($event, 'first', 'today')"
                  @dragover="onDragoverCuttingRow($event)"
                />
                <div
                  v-for="(row, idx) in cuttingManagementList"
                  :key="row.id ?? `cutting-${idx}`"
                  class="cutting-mgmt-tr cutting-mgmt-data-row"
                  draggable="true"
                  @dragstart="onCuttingCardDragStart($event, row)"
                  @dragend="onCuttingCardDragEnd"
                  @drop.prevent="onDropCuttingRowForReorder($event, row)"
                  @dragover="onDragoverCuttingRow($event)"
                  @dblclick.stop="openCuttingEditDialog(row)"
                >
                  <div class="cutting-mgmt-td">{{ row.cd ?? row.management_code ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_line ?? '-' }}</div>
                  <div
                    class="cutting-mgmt-td cutting-mgmt-td-production-day"
                    :class="{ 'is-editing-production-day': editingProductionDayId === row.id }"
                    @dblclick.stop="startEditProductionDay(row)"
                  >
                    <template v-if="editingProductionDayId === row.id">
                      <span class="production-day-editor">
                        <el-button type="default" size="small" circle title="前日" @click.stop="editingProductionDayValue = shiftDate(editingProductionDayValue, -1); saveProductionDay(row, editingProductionDayValue)">
                          <el-icon><ArrowLeft /></el-icon>
                        </el-button>
                        <el-date-picker
                          v-model="editingProductionDayValue"
                          type="date"
                          value-format="YYYY-MM-DD"
                          size="small"
                          class="production-day-picker-inline"
                          @change="(v: string) => v && saveProductionDay(row, v)"
                        />
                        <el-button type="default" size="small" circle title="翌日" @click.stop="editingProductionDayValue = shiftDate(editingProductionDayValue, 1); saveProductionDay(row, editingProductionDayValue)">
                          <el-icon><ArrowRight /></el-icon>
                        </el-button>
                        <el-button type="danger" link size="small" title="キャンセル（Esc）" @click.stop="cancelEditProductionDay">×</el-button>
                      </span>
                    </template>
                    <template v-else>{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
                  </div>
                  <div class="cutting-mgmt-td">{{ row.cutting_machine ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.product_name ?? row.product_cd ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.material_name ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.actual_production_quantity ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.defect_qty ?? '-' }}</div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-switch">
                    <el-switch
                      :model-value="!!row.production_completed_check"
                      :loading="cuttingCompletedLoading === (row.id ?? 0)"
                      size="small"
                      @click.stop
                      @change="toggleCuttingCompleted(row)"
                    />
                  </div>
                  <div class="cutting-mgmt-td">{{ row.production_sequence ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_time ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.remarks ?? '-' }}</div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-actions">
                    <el-button
                      v-if="(row.actual_production_quantity ?? 0) > 0"
                      type="warning"
                      link
                      size="small"
                      title="未完了分を翌日へ順延"
                      @click.stop="openSplitToNextDayDialog(row)"
                    >
                      <el-icon><DArrowRight /></el-icon>
                    </el-button>
                    <el-button type="primary" link size="small" title="複製" @click.stop="duplicateCuttingRow(row)">
                      <el-icon><DocumentCopy /></el-icon>
                    </el-button>
                    <el-button type="danger" link size="small" title="削除" @click.stop="deleteCuttingRow(row)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                <div
                  class="cutting-mgmt-drop-edge cutting-mgmt-drop-edge--last"
                  @drop.prevent="onDropCuttingRowToEdge($event, 'last', 'today')"
                  @dragover="onDragoverCuttingRow($event)"
                />
              </div>
              </div>
            </div>
            </div>
            <div v-if="cuttingManagementList.length" class="cutting-mgmt-tfoot-wrap">
              <div class="cutting-mgmt-tfoot cutting-mgmt-tfoot-summary">
                <span class="cutting-mgmt-tfoot-item">生産数合計：{{ cuttingTodayTotal.quantity }}</span>
                <span class="cutting-mgmt-tfoot-item">不良合計：{{ cuttingTodayTotal.defect }}</span>
                <span class="cutting-mgmt-tfoot-item">生産時間合計：{{ cuttingTodayTotal.time ?? '-' }}</span>
                <span class="cutting-mgmt-tfoot-item usage-count-item">使用材料数：{{ cuttingTodayUsageSummary.totalCount }} 束</span>
              </div>
            </div>
            <div v-if="!cuttingManagementList.length && !cuttingManagementLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
        <div class="instruction-col cutting-management-section cutting-management-section-right">
          <div class="cutting-mgmt-header">
            <span class="cutting-mgmt-title">切断指示-翌日</span>
            <div class="cutting-mgmt-date-wrap">
              <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftDateTomorrow(-1)" />
              <el-date-picker
                v-model="selectedDateTomorrow"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="生産日"
                size="small"
                class="cutting-mgmt-date-picker"
                @change="loadCuttingManagement"
              />
              <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftDateTomorrow(1)" />
            </div>
          </div>
          <div v-loading="cuttingManagementLoading" class="cutting-mgmt-table-wrap">
            <div class="cutting-mgmt-h-scroll">
            <div class="cutting-mgmt-table-inner cutting-mgmt-table-inner--tomorrow">
              <div class="cutting-mgmt-thead">
                <div class="cutting-mgmt-tr">
                  <div class="cutting-mgmt-th">CD</div>
                  <div class="cutting-mgmt-th">生産日</div>
                  <div class="cutting-mgmt-th">切断機</div>
                  <div class="cutting-mgmt-th">製品名</div>
                  <div class="cutting-mgmt-th">生産数</div>
                  <div class="cutting-mgmt-th">不良</div>
                  <div class="cutting-mgmt-th">生産順</div>
                  <div class="cutting-mgmt-th">生産時間</div>
                </div>
              </div>
              <div
                class="cutting-mgmt-tbody-drop-zone"
                :class="{ 'drop-zone-active': dragOverZone === 'cuttingManagement' }"
                @drop="onDropCuttingManagement"
                @dragover="onDragOver($event, 'cuttingManagement')"
                @dragenter="onDragEnter('cuttingManagement')"
                @dragleave="onDragLeave('cuttingManagement')"
              >
                <div class="cutting-mgmt-drop-hint" v-if="dragOverZone === 'cuttingManagement'">ここにドロップでロットを切断指示へ移行</div>
                <div class="cutting-mgmt-tbody">
                <div
                  class="cutting-mgmt-drop-edge"
                  @drop.prevent="onDropCuttingRowToEdge($event, 'first', 'tomorrow')"
                  @dragover="onDragoverCuttingRow($event)"
                />
                <div
                  v-for="(row, idx) in cuttingManagementListTomorrow"
                  :key="'r-' + (row.id ?? `cutting-${idx}`)"
                  class="cutting-mgmt-tr cutting-mgmt-data-row"
                  draggable="true"
                  @dragstart="onCuttingCardDragStart($event, row)"
                  @dragend="onCuttingCardDragEnd"
                  @drop.prevent="onDropCuttingRowForReorder($event, row)"
                  @dragover="onDragoverCuttingRow($event)"
                  @dblclick.stop="openCuttingEditDialog(row)"
                >
                  <div class="cutting-mgmt-td">{{ row.cd ?? row.management_code ?? '-' }}</div>
                  <div
                    class="cutting-mgmt-td cutting-mgmt-td-production-day"
                    :class="{ 'is-editing-production-day': editingProductionDayId === row.id }"
                    @dblclick.stop="startEditProductionDay(row)"
                  >
                    <template v-if="editingProductionDayId === row.id">
                      <span class="production-day-editor">
                        <el-button type="default" size="small" circle title="前日" @click.stop="editingProductionDayValue = shiftDate(editingProductionDayValue, -1); saveProductionDay(row, editingProductionDayValue)">
                          <el-icon><ArrowLeft /></el-icon>
                        </el-button>
                        <el-date-picker
                          v-model="editingProductionDayValue"
                          type="date"
                          value-format="YYYY-MM-DD"
                          size="small"
                          class="production-day-picker-inline"
                          @change="(v: string) => v && saveProductionDay(row, v)"
                        />
                        <el-button type="default" size="small" circle title="翌日" @click.stop="editingProductionDayValue = shiftDate(editingProductionDayValue, 1); saveProductionDay(row, editingProductionDayValue)">
                          <el-icon><ArrowRight /></el-icon>
                        </el-button>
                        <el-button type="danger" link size="small" title="キャンセル（Esc）" @click.stop="cancelEditProductionDay">×</el-button>
                      </span>
                    </template>
                    <template v-else>{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
                  </div>
                  <div class="cutting-mgmt-td">{{ row.cutting_machine ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.product_name ?? row.product_cd ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.actual_production_quantity ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.defect_qty ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_sequence ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_time ?? '-' }}</div>
                </div>
                <div
                  class="cutting-mgmt-drop-edge cutting-mgmt-drop-edge--last"
                  @drop.prevent="onDropCuttingRowToEdge($event, 'last', 'tomorrow')"
                  @dragover="onDragoverCuttingRow($event)"
                />
              </div>
              </div>
            </div>
            </div>
            <div v-if="cuttingManagementListTomorrow.length" class="cutting-mgmt-tfoot-wrap cutting-mgmt-tfoot-wrap--tomorrow">
              <div class="cutting-mgmt-tfoot cutting-mgmt-tfoot-summary">
                <span class="cutting-mgmt-tfoot-item">生産数合計：{{ cuttingTomorrowTotal.quantity }}</span>
                <span class="cutting-mgmt-tfoot-item">不良合計：{{ cuttingTomorrowTotal.defect }}</span>
                <span class="cutting-mgmt-tfoot-item">生産時間合計：{{ cuttingTomorrowTotal.time ?? '-' }}</span>
                <span class="cutting-mgmt-tfoot-item usage-count-item">使用材料数（新増）：{{ cuttingTomorrowUsageSummary.totalCount }} 束</span>
              </div>
            </div>
            <div v-if="!cuttingManagementListTomorrow.length && !cuttingManagementLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
      </div>

      <!-- 材料別使用数汇总行（切断指示-今日/翌日の下・独立日付筛选） -->
      <div class="instruction-row instruction-two-cols instruction-cols-6-4 usage-summary-row">
        <!-- 今日：材料別使用数汇总表（独立日付筛选） -->
        <div class="instruction-col usage-summary-col">
          <div class="usage-summary-wrap">
            <div class="usage-summary-title-row usage-summary-title-row--with-date">
              <span class="usage-summary-title">使用材料数（材料別）- 今日</span>
              <div class="cutting-mgmt-date-wrap usage-summary-date-wrap">
                <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftUsageSummaryDateToday(-1)" />
                <el-date-picker
                  v-model="usageSummaryDateToday"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="生産日"
                  size="small"
                  class="cutting-mgmt-date-picker"
                  @change="loadUsageSummaryCuttingList"
                />
                <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftUsageSummaryDateToday(1)" />
              </div>
              <div class="usage-summary-title-actions">
                <el-button type="warning" size="small" :loading="usageReflectionLoading" @click="confirmUsageReflection">使用数反映</el-button>
                <el-button type="info" size="small" @click="openSpecifiedDateDialog">指定日材料数</el-button>
              </div>
            </div>
            <div v-loading="usageSummaryCuttingLoading" class="usage-summary-table-wrap">
              <table v-if="usageSummaryCuttingList.length" class="usage-summary-table usage-summary-table--list">
                <thead>
                  <tr>
                    <th>製品名</th>
                    <th>原材料</th>
                    <th>管理コード</th>
                    <th>在庫区分</th>
                    <th>材料使用数</th>
                    <th>使用材料</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in usageSummaryCuttingList" :key="row.id ?? `usage-${idx}`">
                    <td>{{ row.product_name ?? '-' }}</td>
                    <td>{{ row.material_name ?? '-' }}</td>
                    <td :class="{ 'usage-mgmt-empty': !row.management_code || !String(row.management_code).trim() }">{{ row.management_code?.trim() || '-' }}</td>
                    <td class="usage-summary-stock-td">
                      <el-switch
                        :model-value="(row as { use_material_stock_sub?: number }).use_material_stock_sub === 1 ? 1 : 0"
                        :active-value="1"
                        :inactive-value="0"
                        size="small"
                        @change="onChangeUsageSummaryStock(row, $event)"
                      />
                    </td>
                    <td class="usage-summary-usage-td" @dblclick.stop="onDblClickUsageSummaryUsageCount(row)">
                      {{ formatUsageCountDisplay(row as { usage_count?: number | null }) }}
                    </td>
                    <td>
                      <span v-if="(row as { use_material_stock_sub?: number }).use_material_stock_sub === 1" class="usage-sub-manual-tag">サブ・手動</span>
                      <span v-else :class="{ 'usage-reflected-tag': isUsageRowReflected(row), 'usage-not-reflected-tag': !isUsageRowReflected(row) }">
                        {{ isUsageRowReflected(row) ? '反映済' : '未反映' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else-if="!usageSummaryCuttingLoading" class="usage-summary-empty">該当日のデータがありません</div>
            </div>
            <div v-if="usageSummaryCuttingList.length" class="usage-summary-footer">
              <span class="usage-summary-footer-item">合计件数：{{ usageSummaryTodayCounts.total }}</span>
              <span class="usage-summary-footer-item usage-summary-footer--reflected">反映済：{{ usageSummaryTodayCounts.reflected }}</span>
              <span class="usage-summary-footer-item usage-summary-footer--not-reflected">未反映：{{ usageSummaryTodayCounts.notReflected }}</span>
            </div>
          </div>
        </div>
        <!-- 翌日：使用材料数（材料別）- 翌日（独立日付筛选） -->
        <div class="instruction-col usage-summary-col">
          <div class="usage-summary-wrap usage-summary-wrap--tomorrow">
            <div class="usage-summary-title-row usage-summary-title-row--with-date">
              <span class="usage-summary-title">使用材料数（材料別）- 翌日</span>
              <div class="cutting-mgmt-date-wrap usage-summary-date-wrap">
                <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftUsageSummaryDateTomorrow(-1)" />
                <el-date-picker
                  v-model="usageSummaryDateTomorrow"
                  type="date"
                  value-format="YYYY-MM-DD"
                  placeholder="生産日"
                  size="small"
                  class="cutting-mgmt-date-picker"
                  @change="loadUsageSummaryCuttingListTomorrow"
                />
                <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftUsageSummaryDateTomorrow(1)" />
              </div>
            </div>
            <div v-loading="usageSummaryCuttingLoadingTomorrow" class="usage-summary-table-wrap">
              <table v-if="usageSummaryCuttingListTomorrow.length" class="usage-summary-table usage-summary-table--list">
                <thead>
                  <tr>
                    <th>製品名</th>
                    <th>原材料</th>
                    <th>管理コード</th>
                    <th>在庫区分</th>
                    <th>材料使用数</th>
                    <th>使用材料</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in usageSummaryCuttingListTomorrow" :key="'tm-' + (row.id ?? idx)">
                    <td>{{ row.product_name ?? '-' }}</td>
                    <td>{{ row.material_name ?? '-' }}</td>
                    <td :class="{ 'usage-mgmt-empty': !row.management_code || !String(row.management_code).trim() }">{{ row.management_code?.trim() || '-' }}</td>
                    <td class="usage-summary-stock-td">
                      <el-switch
                        :model-value="(row as { use_material_stock_sub?: number }).use_material_stock_sub === 1 ? 1 : 0"
                        :active-value="1"
                        :inactive-value="0"
                        size="small"
                        @change="onChangeUsageSummaryStock(row, $event)"
                      />
                    </td>
                    <td class="usage-summary-usage-td" @dblclick.stop="onDblClickUsageSummaryUsageCount(row)">
                      {{ formatUsageCountDisplay(row as { usage_count?: number | null }) }}
                    </td>
                    <td>
                      <span v-if="(row as { use_material_stock_sub?: number }).use_material_stock_sub === 1" class="usage-sub-manual-tag">サブ・手動</span>
                      <span v-else :class="{ 'usage-reflected-tag': isUsageRowReflected(row), 'usage-not-reflected-tag': !isUsageRowReflected(row) }">
                        {{ isUsageRowReflected(row) ? '反映済' : '未反映' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-else-if="!usageSummaryCuttingLoadingTomorrow" class="usage-summary-empty">該当日のデータがありません</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 面取ロット一覧（面取指示の上）：レイアウト・幅は生産ロット一覧と同様、右に製品情報・設備能率 -->
      <div class="plan-row chamfering-plan-row">
        <div class="plan-section plan-section-left">
          <div class="chamfering-batch-section-card">
            <div class="cutting-mgmt-header">
              <span class="cutting-mgmt-title">面取ロット一覧</span>
              <div class="cutting-mgmt-header-right">
                <el-button type="primary" size="small" @click="openChamferingPlanNewDialog">新規追加</el-button>
              </div>
            </div>
            <div
              v-loading="chamferingBatchLoading"
              class="plan-batch-table-wrap chamfering-batch-table-wrap"
              :class="{ 'drop-zone-active': dragOverZone === 'chamferingBatchList' }"
              @drop="onDropChamferingBatchList"
              @dragover="onDragOverChamfering($event, 'chamferingBatchList')"
              @dragenter="onDragEnterChamfering('chamferingBatchList')"
              @dragleave="onDragLeaveChamfering('chamferingBatchList')"
            >
              <div v-if="dragOverZone === 'chamferingBatchList'" class="plan-batch-drop-hint">ここにドロップで面取指示をロットへ戻す</div>
              <div v-show="chamferingBatchList.length > 0" class="plan-batch-table-inner">
                <div class="plan-batch-thead">
                  <div class="plan-batch-tr">
                    <div class="plan-batch-th">CD</div>
                    <div class="plan-batch-th">生産月</div>
                    <div class="plan-batch-th">ライン</div>
                    <div class="plan-batch-th">製品名</div>
                    <div class="plan-batch-th">原材料</div>
                    <div class="plan-batch-th">生産数</div>
                    <div class="plan-batch-th">ロット数</div>
                    <div class="plan-batch-th">ロットNo</div>
                    <div class="plan-batch-th">SW</div>
                    <div class="plan-batch-th plan-batch-th-actions">操作</div>
                  </div>
                </div>
                <div class="plan-batch-tbody">
                  <div
                    v-for="(row, idx) in chamferingBatchListSorted"
                    :key="row.id ?? `cb-${idx}`"
                    class="plan-batch-tr plan-batch-data-row"
                    :class="{ 'plan-batch-row-selected': selectedChamferingProductCd === (row.product_cd ?? '') }"
                    draggable="true"
                    @click.stop="onChamferingBatchRowClick(row)"
                    @dblclick.stop="openChamferingPlanEditDialog(row)"
                    @dragstart="onChamferingBatchDragStart($event, row)"
                    @dragend="onChamferingDragEnd"
                  >
                    <div class="plan-batch-td">{{ (row.cd ?? (row.management_code ? String(row.management_code).slice(-5) : '')) || '-' }}</div>
                    <div class="plan-batch-td">{{ formatDateOnly(String(row.production_month ?? '')) || '-' }}</div>
                    <div class="plan-batch-td">{{ row.production_line ?? '-' }}</div>
                    <div class="plan-batch-td">{{ row.product_name || row.product_cd || '-' }}</div>
                    <div class="plan-batch-td">{{ row.material_name ?? '-' }}</div>
                    <div class="plan-batch-td">{{ row.actual_production_quantity ?? '-' }}</div>
                    <div class="plan-batch-td">{{ row.production_lot_size ?? '-' }}</div>
                    <div class="plan-batch-td">{{ row.lot_number ?? '-' }}</div>
                    <div class="plan-batch-td" @click.stop>
                      <el-switch
                        :model-value="!!row.has_sw_process"
                        size="small"
                        :loading="chamferingSwLoading === row.id"
                        @change="(v: string | number | boolean) => updateChamferingPlanSw(row, !!v)"
                      />
                    </div>
                    <div class="plan-batch-td plan-batch-td-actions">
                      <el-button
                        type="primary"
                        link
                        size="small"
                        title="複製"
                        :loading="chamferingBatchActionLoading === row.id"
                        @click.stop="copyChamferingPlan(row)"
                      >
                        <el-icon><DocumentCopy /></el-icon>
                      </el-button>
                      <el-button
                        type="danger"
                        link
                        size="small"
                        title="削除"
                        :loading="chamferingBatchActionLoading === row.id"
                        @click.stop="deleteChamferingPlan(row)"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="!chamferingBatchList.length && !chamferingBatchLoading" class="plan-batch-empty">データなし</div>
            </div>
          </div>
        </div>
        <div class="plan-section-right right-panel chamfering-right-panel">
          <div class="right-panel-top">
            <div class="right-panel-title">製品情報</div>
            <div v-if="!selectedChamferingProductCd" class="right-panel-placeholder">一覧で製品をクリック</div>
            <div v-else v-loading="chamferingProductDetailLoading" class="product-detail-body">
              <template v-if="chamferingProductDetail">
                <ul class="product-detail-list product-detail-list--chamfering">
                  <li class="product-detail-list-item"><span class="detail-label">製品CD</span><span class="detail-value">{{ chamferingProductDetail.product_cd ?? '-' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">製品名</span><span class="detail-value">{{ chamferingProductDetail.product_name ?? '-' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">生産ロット</span><span class="detail-value">{{ chamferingProductDetail.lot_size ?? '-' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">材料</span><span class="detail-value">{{ chamferingProductDetail.material_name ?? chamferingProductDetail.material_cd ?? '-' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">取数</span><span class="detail-value">{{ chamferingProductDetail.take_count ?? '-' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">切断長</span><span class="detail-value">{{ chamferingProductDetail.cut_length ?? '-' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">面取長</span><span class="detail-value">{{ (chamferingProductDetail.chamfer_length != null && Number(chamferingProductDetail.chamfer_length) !== 0) ? chamferingProductDetail.chamfer_length : '--' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">展開長</span><span class="detail-value">{{ (chamferingProductDetail.developed_length != null && Number(chamferingProductDetail.developed_length) !== 0) ? chamferingProductDetail.developed_length : '--' }}</span></li>
                  <li class="product-detail-list-item"><span class="detail-label">端材長</span><span class="detail-value">{{ chamferingProductDetail.scrap_length ?? '-' }}</span></li>
                </ul>
              </template>
              <div v-else-if="!chamferingProductDetailLoading" class="right-panel-placeholder">該当製品なし</div>
            </div>
          </div>
          <div class="right-panel-bottom">
            <div class="right-panel-title">設備能率（面取）</div>
            <div v-if="!selectedChamferingProductCd" class="right-panel-placeholder">一覧で製品をクリック</div>
            <div v-else v-loading="chamferingEquipmentEfficiencyLoading" class="equipment-efficiency-body">
              <el-table v-if="chamferingEquipmentEfficiencyListFiltered.length" :data="chamferingEquipmentEfficiencyListFiltered" size="small" max-height="220" class="efficiency-table">
                <el-table-column prop="machines_name" label="設備名" min-width="100" show-overflow-tooltip />
                <el-table-column prop="efficiency_rate" label="能率" width="80" align="right">
                  <template #default="{ row }">{{ row.efficiency_rate != null ? Number(row.efficiency_rate) : '-' }}</template>
                </el-table-column>
              </el-table>
              <div v-else-if="!chamferingEquipmentEfficiencyLoading" class="right-panel-placeholder">該当データなし（設備名に「面取」を含むもののみ表示）</div>
            </div>
          </div>
        </div>
      </div>
      <!-- 第2行：面取指示-今日 | 面取指示-翌日（同切断指示 6:4 + 日期筛选） -->
      <div class="instruction-row instruction-two-cols instruction-cols-6-4">
        <div class="instruction-col chamfering-management-section">
          <div class="cutting-mgmt-header chamfering-mgmt-header-two-rows">
            <div class="chamfering-mgmt-header-row1">
              <div class="cutting-mgmt-header-left">
                <span class="cutting-mgmt-title">面取指示-今日</span>
                <div class="cutting-mgmt-date-wrap">
                  <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftChamferingDateToday(-1)" />
                  <el-date-picker
                    v-model="selectedChamferingDateToday"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="生産日"
                    size="small"
                    class="cutting-mgmt-date-picker"
                    @change="loadChamferingManagement"
                  />
                  <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftChamferingDateToday(1)" />
                </div>
              </div>
              <div class="cutting-mgmt-header-right chamfering-mgmt-header-actions">
                <el-button type="default" size="small" @click="openChamferingNewDialog">新規追加</el-button>
                <el-button type="default" size="small" :loading="printChamferingPlanLoading" @click="printChamferingPlanList">計画印刷</el-button>
                <el-button type="primary" size="small" :loading="issueChamferingInstructionSheetLoading" @click="issueChamferingInstructionSheet">指示書発行</el-button>
                <el-button type="success" size="small" :loading="confirmChamferingActualLoading" @click="confirmChamferingActual">実績確定</el-button>
              </div>
            </div>
            <div class="chamfering-mgmt-header-row2">
              <div class="cutting-mgmt-machine-btns chamfering-machine-btns">
                <el-button
                  size="small"
                  :type="!selectedChamferingMachineFilter ? 'primary' : 'default'"
                  @click="selectedChamferingMachineFilter = ''; loadChamferingManagement()"
                >
                  全部
                </el-button>
                <el-button
                  v-for="m in chamferingMachineOptions"
                  :key="m.machine_name"
                  size="small"
                  :type="selectedChamferingMachineFilter === m.machine_name ? 'primary' : 'default'"
                  @click="selectedChamferingMachineFilter = m.machine_name; loadChamferingManagement()"
                >
                  {{ m.machine_name }}
                </el-button>
              </div>
            </div>
          </div>
          <div
            v-loading="chamferingManagementLoading"
            class="cutting-mgmt-table-wrap chamfering-mgmt-drop-wrap"
            :class="{ 'drop-zone-active': dragOverZone === 'chamferingManagement' }"
            @drop="onDropChamferingManagement"
            @dragover="onDragOverChamfering($event, 'chamferingManagement')"
            @dragenter="onDragEnterChamfering('chamferingManagement')"
            @dragleave="onDragLeaveChamfering('chamferingManagement')"
          >
            <div v-if="dragOverZone === 'chamferingManagement'" class="cutting-mgmt-drop-hint">ここにドロップで面取ロットを面取指示へ移行</div>
            <div class="cutting-mgmt-table-inner">
              <div class="cutting-mgmt-thead">
                <div class="cutting-mgmt-tr">
                  <div class="cutting-mgmt-th">CD</div>
                  <div class="cutting-mgmt-th">ライン</div>
                  <div class="cutting-mgmt-th">生産日</div>
                  <div class="cutting-mgmt-th">面取機</div>
                  <div class="cutting-mgmt-th">製品名</div>
                  <div class="cutting-mgmt-th">原材料</div>
                  <div class="cutting-mgmt-th">生産数</div>
                  <div class="cutting-mgmt-th">不良</div>
                  <div class="cutting-mgmt-th">完了</div>
                  <div class="cutting-mgmt-th">カ無</div>
                  <div class="cutting-mgmt-th">生産順</div>
                  <div class="cutting-mgmt-th">生産時間</div>
                  <div class="cutting-mgmt-th cutting-mgmt-th-actions">操作</div>
                </div>
              </div>
              <div class="cutting-mgmt-tbody">
                <div
                  class="cutting-mgmt-drop-edge"
                  @drop.prevent="onDropChamferingRowToEdge($event, 'first', 'today')"
                  @dragover="onDragoverChamferingRow($event)"
                />
                <div
                  v-for="(row, idx) in chamferingManagementListToday"
                  :key="row.id ?? `cham-today-${idx}`"
                  class="cutting-mgmt-tr cutting-mgmt-data-row"
                  draggable="true"
                  @dblclick.stop="openChamferingEditDialog(row)"
                  @dragstart="onChamferingManagementDragStart($event, row)"
                  @dragend="onChamferingDragEnd"
                  @drop.prevent="onDropChamferingRowForReorder($event, row)"
                  @dragover="onDragoverChamferingRow($event)"
                >
                  <div class="cutting-mgmt-td">{{ row.cd ?? row.management_code ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_line ?? '-' }}</div>
                  <div
                    class="cutting-mgmt-td cutting-mgmt-td-production-day"
                    :class="{ 'is-editing-production-day': editingChamferingProductionDayId === row.id }"
                    @dblclick.stop="startEditChamferingProductionDay(row)"
                  >
                    <template v-if="editingChamferingProductionDayId === row.id">
                      <span class="production-day-editor">
                        <el-button type="default" size="small" circle title="前日" @click.stop="editingChamferingProductionDayValue = shiftDate(editingChamferingProductionDayValue, -1); saveChamferingProductionDay(row, editingChamferingProductionDayValue)">
                          <el-icon><ArrowLeft /></el-icon>
                        </el-button>
                        <el-date-picker
                          v-model="editingChamferingProductionDayValue"
                          type="date"
                          value-format="YYYY-MM-DD"
                          size="small"
                          class="production-day-picker-inline"
                          @change="(v: string) => v && saveChamferingProductionDay(row, v)"
                        />
                        <el-button type="default" size="small" circle title="翌日" @click.stop="editingChamferingProductionDayValue = shiftDate(editingChamferingProductionDayValue, 1); saveChamferingProductionDay(row, editingChamferingProductionDayValue)">
                          <el-icon><ArrowRight /></el-icon>
                        </el-button>
                        <el-button type="info" link size="small" title="キャンセル（Esc）" @click.stop="cancelEditChamferingProductionDay">×</el-button>
                      </span>
                    </template>
                    <template v-else>{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
                  </div>
                  <div class="cutting-mgmt-td">{{ row.chamfering_machine ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.product_name ?? row.product_cd ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.material_name ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.actual_production_quantity ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.defect_qty ?? '-' }}</div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-switch">
                    <el-switch
                      :model-value="!!row.production_completed_check"
                      :loading="chamferingCompletedLoading === (row.id ?? 0)"
                      size="small"
                      @click.stop
                      @change="toggleChamferingCompleted(row)"
                    />
                  </div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-switch">
                    <el-switch
                      :model-value="!!row.no_count"
                      :loading="chamferingNoCountLoading === (row.id ?? 0)"
                      size="small"
                      @click.stop
                      @change="toggleChamferingNoCount(row)"
                    />
                  </div>
                  <div class="cutting-mgmt-td">{{ row.production_sequence ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_time ?? '-' }}</div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-actions">
                    <el-button
                      v-if="(row.actual_production_quantity ?? 0) > 0"
                      type="warning"
                      link
                      size="small"
                      title="未完了分を翌日へ順延"
                      @click.stop="openChamferingSplitDialog(row)"
                    >
                      <el-icon><DArrowRight /></el-icon>
                    </el-button>
                    <el-button type="primary" link size="small" title="複製" @click.stop="duplicateChamferingRow(row)">
                      <el-icon><DocumentCopy /></el-icon>
                    </el-button>
                    <el-button type="danger" link size="small" title="削除" @click.stop="deleteChamferingRow(row)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
                <div
                  class="cutting-mgmt-drop-edge cutting-mgmt-drop-edge--last"
                  @drop.prevent="onDropChamferingRowToEdge($event, 'last', 'today')"
                  @dragover="onDragoverChamferingRow($event)"
                />
              </div>
            </div>
            <div v-if="chamferingManagementListToday.length" class="cutting-mgmt-tfoot-wrap">
              <div class="cutting-mgmt-tfoot cutting-mgmt-tfoot-summary">
                <span class="cutting-mgmt-tfoot-item">生産数合計：{{ chamferingTodayTotal.quantity }}</span>
                <span class="cutting-mgmt-tfoot-item">不良合計：{{ chamferingTodayTotal.defect }}</span>
                <span class="cutting-mgmt-tfoot-item">生産時間合計：{{ chamferingTodayTotal.time ?? '-' }}</span>
              </div>
            </div>
            <div v-if="!chamferingManagementListToday.length && !chamferingManagementLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
        <div class="instruction-col chamfering-management-section cutting-management-section-right">
          <div class="cutting-mgmt-header">
            <span class="cutting-mgmt-title">面取指示-翌日</span>
            <div class="cutting-mgmt-date-wrap">
              <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftChamferingDateTomorrow(-1)" />
              <el-date-picker
                v-model="selectedChamferingDateTomorrow"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="生産日"
                size="small"
                class="cutting-mgmt-date-picker"
                @change="loadChamferingManagement"
              />
              <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftChamferingDateTomorrow(1)" />
            </div>
          </div>
          <div
            v-loading="chamferingManagementLoading"
            class="cutting-mgmt-table-wrap chamfering-mgmt-drop-wrap"
            :class="{ 'drop-zone-active': dragOverZone === 'chamferingManagement' }"
            @drop="onDropChamferingManagement"
            @dragover="onDragOverChamfering($event, 'chamferingManagement')"
            @dragenter="onDragEnterChamfering('chamferingManagement')"
            @dragleave="onDragLeaveChamfering('chamferingManagement')"
          >
            <div v-if="dragOverZone === 'chamferingManagement'" class="cutting-mgmt-drop-hint">ここにドロップで面取ロットを面取指示へ移行</div>
            <div class="cutting-mgmt-table-inner cutting-mgmt-table-inner--tomorrow cutting-mgmt-table-inner--chamfering-tomorrow">
              <div class="cutting-mgmt-thead">
                <div class="cutting-mgmt-tr">
                  <div class="cutting-mgmt-th">CD</div>
                  <div class="cutting-mgmt-th">生産日</div>
                  <div class="cutting-mgmt-th">面取機</div>
                  <div class="cutting-mgmt-th">製品名</div>
                  <div class="cutting-mgmt-th">生産数</div>
                  <div class="cutting-mgmt-th">不良</div>
                  <div class="cutting-mgmt-th">生産順</div>
                  <div class="cutting-mgmt-th">生産時間</div>
                </div>
              </div>
              <div class="cutting-mgmt-tbody">
                <div
                  class="cutting-mgmt-drop-edge"
                  @drop.prevent="onDropChamferingRowToEdge($event, 'first', 'tomorrow')"
                  @dragover="onDragoverChamferingRow($event)"
                />
                <div
                  v-for="(row, idx) in chamferingManagementListTomorrow"
                  :key="row.id ?? `cham-tomorrow-${idx}`"
                  class="cutting-mgmt-tr cutting-mgmt-data-row"
                  draggable="true"
                  @dragstart="onChamferingManagementDragStart($event, row)"
                  @dragend="onChamferingDragEnd"
                  @drop.prevent="onDropChamferingRowForReorder($event, row)"
                  @dragover="onDragoverChamferingRow($event)"
                >
                  <div class="cutting-mgmt-td">{{ row.cd ?? row.management_code ?? '-' }}</div>
                  <div
                    class="cutting-mgmt-td cutting-mgmt-td-production-day"
                    :class="{ 'is-editing-production-day': editingChamferingProductionDayId === row.id }"
                    @dblclick.stop="startEditChamferingProductionDay(row)"
                  >
                    <template v-if="editingChamferingProductionDayId === row.id">
                      <span class="production-day-editor">
                        <el-button type="default" size="small" circle title="前日" @click.stop="editingChamferingProductionDayValue = shiftDate(editingChamferingProductionDayValue, -1); saveChamferingProductionDay(row, editingChamferingProductionDayValue)">
                          <el-icon><ArrowLeft /></el-icon>
                        </el-button>
                        <el-date-picker
                          v-model="editingChamferingProductionDayValue"
                          type="date"
                          value-format="YYYY-MM-DD"
                          size="small"
                          class="production-day-picker-inline"
                          @change="(v: string) => v && saveChamferingProductionDay(row, v)"
                        />
                        <el-button type="default" size="small" circle title="翌日" @click.stop="editingChamferingProductionDayValue = shiftDate(editingChamferingProductionDayValue, 1); saveChamferingProductionDay(row, editingChamferingProductionDayValue)">
                          <el-icon><ArrowRight /></el-icon>
                        </el-button>
                        <el-button type="info" link size="small" title="キャンセル（Esc）" @click.stop="cancelEditChamferingProductionDay">×</el-button>
                      </span>
                    </template>
                    <template v-else>{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
                  </div>
                  <div class="cutting-mgmt-td">{{ row.chamfering_machine ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.product_name ?? row.product_cd ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.actual_production_quantity ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.defect_qty ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_sequence ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.production_time ?? '-' }}</div>
                </div>
                <div
                  class="cutting-mgmt-drop-edge cutting-mgmt-drop-edge--last"
                  @drop.prevent="onDropChamferingRowToEdge($event, 'last', 'tomorrow')"
                  @dragover="onDragoverChamferingRow($event)"
                />
              </div>
            </div>
            <div v-if="chamferingManagementListTomorrow.length" class="cutting-mgmt-tfoot-wrap cutting-mgmt-tfoot-wrap--tomorrow">
              <div class="cutting-mgmt-tfoot cutting-mgmt-tfoot-summary">
                <span class="cutting-mgmt-tfoot-item">生産数合計：{{ chamferingTomorrowTotal.quantity }}</span>
                <span class="cutting-mgmt-tfoot-item">不良合計：{{ chamferingTomorrowTotal.defect }}</span>
                <span class="cutting-mgmt-tfoot-item">生産時間合計：{{ chamferingTomorrowTotal.time ?? '-' }}</span>
              </div>
            </div>
            <div v-if="!chamferingManagementListTomorrow.length && !chamferingManagementLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
      </div>
      <!-- 第3行：カンバン発行 -->
      <div class="instruction-row instruction-two-cols">
        <div class="instruction-col kanban-issuance-section instruction-col-full">
          <div class="cutting-mgmt-header">
            <span class="cutting-mgmt-title">カンバン発行</span>
            <div class="cutting-mgmt-date-wrap">
              <el-button
                size="small"
                circle
                title="前日"
                @click="shiftKanbanFilterDay(-1)"
              >
                ‹
              </el-button>
              <el-date-picker
                v-model="kanbanFilterProductionDay"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="生産日"
                size="small"
                clearable
                class="kanban-filter-date"
                style="width: 130px;"
                @change="loadKanbanIssuance"
              />
              <el-button
                size="small"
                plain
                class="mt-today-btn"
                @click="setKanbanFilterToday"
              >
                今日
              </el-button>
              <el-button
                size="small"
                circle
                title="翌日"
                @click="shiftKanbanFilterDay(1)"
              >
                ›
              </el-button>
              <el-select
                v-model="kanbanFilterStatus"
                placeholder="状態"
                clearable
                size="small"
                class="kanban-filter-status"
                style="width: 110px; margin-left: 8px;"
                @change="loadKanbanIssuance"
              >
                <el-option label="（全部）" value="" />
                <el-option label="待発行" value="pending" />
                <el-option label="発行済" value="issued" />
                <el-option label="完了" value="completed" />
              </el-select>
              <el-select
                v-model="kanbanFilterProductName"
                placeholder="製品名"
                clearable
                filterable
                size="small"
                class="kanban-filter-product"
                style="width: 160px; margin-left: 8px;"
                @change="loadKanbanIssuance"
              >
                <el-option label="（全部）" value="" />
                <el-option
                  v-for="name in kanbanIssuanceProductNameOptions"
                  :key="name"
                  :label="name"
                  :value="name"
                />
              </el-select>
              <el-button type="primary" size="small" :loading="kanbanBatchIssueLoading" @click="batchIssueKanban">一括発行</el-button>
              <el-button type="default" size="small" :loading="kanbanSyncProductionDayLoading" @click="syncKanbanProductionDay">更新</el-button>
            </div>
          </div>
          <div v-loading="kanbanIssuanceLoading" class="cutting-mgmt-table-wrap">
            <el-table
              :data="kanbanIssuanceListPaged"
              size="small"
              class="cutting-mgmt-table"
              max-height="260"
              stripe
              row-key="id"
              @selection-change="kanbanIssuanceSelection = $event"
              @select-all="onKanbanSelectAll"
              @row-dblclick="openKanbanEdit"
            >
              <el-table-column type="selection" width="40" align="center" :selectable="(row) => row.status === 'pending' || row.status === 'issued'" />
              <el-table-column prop="status" label="状態" width="76" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.status === 'pending'" type="warning" size="small">待発行</el-tag>
                  <el-tag v-else-if="row.status === 'issued'" size="small">発行済</el-tag>
                  <el-tag v-else-if="row.status === 'completed'" type="success" size="small">完了</el-tag>
                  <span v-else>{{ row.status }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="issue_date" label="発行日" width="92" align="center" />
              <el-table-column prop="production_day" label="生産日" width="110" align="center">
                <template #default="{ row }">{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
              </el-table-column>
              <el-table-column prop="product_name" label="製品名" min-width="140" show-overflow-tooltip />
              <el-table-column prop="production_line" label="ライン" width="70" align="center" show-overflow-tooltip />
              <el-table-column prop="cutting_machine" label="切断機" width="90" align="center" show-overflow-tooltip />
              <el-table-column prop="management_code" label="管理コード" min-width="120" show-overflow-tooltip />
              <el-table-column prop="lot_number" label="ロットNo." width="90" show-overflow-tooltip />
              <el-table-column prop="actual_production_quantity" label="ロット本数" width="84" align="right" />
              <el-table-column label="操作" width="110" align="center" fixed="right">
                <template #default="{ row }">
                  <el-button
                    v-if="row.status === 'pending'"
                    type="primary"
                    link
                    size="small"
                    :loading="kanbanIssuePendingLoading === row.id"
                    @click="issuePendingKanban(row.id!)"
                  >
                    発行
                  </el-button>
                  <el-button
                    v-else-if="row.status === 'issued'"
                    type="warning"
                    link
                    size="small"
                    :loading="kanbanReissueLoading === row.id"
                    @click="reissueKanban(row.id!)"
                  >
                    再発行
                  </el-button>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
            <el-pagination
              v-if="kanbanIssuanceList.length > 0"
              v-model:current-page="kanbanPage"
              v-model:page-size="kanbanPageSize"
              :total="kanbanIssuanceList.length"
              :page-sizes="[30, 50, 100, 200]"
              layout="total, sizes, prev, pager, next"
              size="small"
              class="kanban-pagination"
            />
            <div v-if="!kanbanIssuanceList.length && !kanbanIssuanceLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
      </div>
    </div>

    <!-- カンバン発行：双击编辑弹窗 -->
    <el-dialog
      v-model="kanbanEditDialogVisible"
      title="カンバン発行 編集"
      width="720px"
      :close-on-click-modal="false"
      class="kanban-edit-dialog"
      @close="kanbanEditRow = null"
    >
      <el-form :model="kanbanEditForm" label-width="120px" label-position="left" class="kanban-edit-form">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="製品CD">
              <el-input v-model="kanbanEditForm.product_cd" size="small" clearable placeholder="製品CD" />
            </el-form-item>
            <el-form-item label="製品名">
              <el-input v-model="kanbanEditForm.product_name" size="small" clearable placeholder="製品名" />
            </el-form-item>
            <el-form-item label="ライン">
              <el-input v-model="kanbanEditForm.production_line" size="small" clearable placeholder="ライン" />
            </el-form-item>
            <el-form-item label="切断機">
              <el-input v-model="kanbanEditForm.cutting_machine" size="small" clearable placeholder="切断機" />
            </el-form-item>
            <el-form-item label="原材料">
              <el-input v-model="kanbanEditForm.material_name" size="small" clearable placeholder="原材料" />
            </el-form-item>
            <el-form-item label="規格">
              <el-input v-model="kanbanEditForm.standard_specification" size="small" clearable placeholder="規格" />
            </el-form-item>
            <el-form-item label="管理コード">
              <el-input v-model="kanbanEditForm.management_code" size="small" clearable placeholder="管理コード" />
            </el-form-item>
            <el-form-item label="成型期間（開始）">
              <el-date-picker
                v-model="kanbanEditForm.start_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="開始日"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="成型期間（終了）">
              <el-date-picker
                v-model="kanbanEditForm.end_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="終了日"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="計画数">
              <el-input-number v-model="kanbanEditForm.planned_quantity" :min="0" controls-position="right" size="small" style="width: 100%" />
            </el-form-item>
            <el-form-item label="成型ロット">
              <el-input-number v-model="kanbanEditForm.production_lot_size" :min="0" controls-position="right" size="small" style="width: 100%" />
            </el-form-item>
            <el-form-item label="ロット本数">
              <el-input-number v-model="kanbanEditForm.actual_production_quantity" :min="0" controls-position="right" size="small" style="width: 100%" />
            </el-form-item>
            <el-form-item label="取数">
              <el-input-number v-model="kanbanEditForm.take_count" :min="0" controls-position="right" size="small" style="width: 100%" />
            </el-form-item>
            <el-form-item label="切断長">
              <el-input-number v-model="kanbanEditForm.cutting_length" :min="0" :precision="2" controls-position="right" size="small" style="width: 100%" />
            </el-form-item>
            <el-form-item label="面取長">
              <el-input-number v-model="kanbanEditForm.chamfering_length" :min="0" :precision="2" controls-position="right" size="small" style="width: 100%" />
            </el-form-item>
            <el-form-item label="展開長">
              <el-input-number v-model="kanbanEditForm.developed_length" :min="0" :precision="2" controls-position="right" size="small" style="width: 100%" />
            </el-form-item>
            <el-form-item label="面取工程">
              <el-checkbox v-model="kanbanEditForm.has_chamfering_process">あり</el-checkbox>
            </el-form-item>
            <el-form-item label="ロットNo.">
              <el-input v-model="kanbanEditForm.lot_number" size="small" clearable placeholder="ロットNo." />
            </el-form-item>
            <el-form-item label="生産日">
              <el-date-picker
                v-model="kanbanEditForm.production_day"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="生産日"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button size="small" @click="kanbanEditDialogVisible = false">取消</el-button>
        <el-button type="primary" size="small" :loading="kanbanEditSubmitting" @click="saveKanbanEdit">保存</el-button>
      </template>
    </el-dialog>

    <!-- 実績確定：结果汇总弹窗 -->
    <el-dialog
      v-model="confirmActualResultVisible"
      width="420px"
      :show-close="true"
      class="confirm-actual-result-dialog"
      align-center
    >
      <template #header>
        <div class="confirm-actual-result-header">
          <el-icon class="confirm-actual-result-icon"><CircleCheck /></el-icon>
          <span class="confirm-actual-result-title">実績確定 結果</span>
        </div>
      </template>
      <div class="confirm-actual-result-body">
        <div class="confirm-actual-result-cards">
          <div class="confirm-actual-result-card">
            <span class="confirm-actual-result-card-label">登録件数</span>
            <span class="confirm-actual-result-card-value">{{ confirmActualResultCount }} 件</span>
          </div>
          <div class="confirm-actual-result-card confirm-actual-result-card--highlight">
            <span class="confirm-actual-result-card-label">数量合計（生産数）</span>
            <span class="confirm-actual-result-card-value">{{ confirmActualResultTotalQty.toLocaleString() }} 本</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="confirm-actual-result-footer">
          <el-button type="primary" size="default" @click="confirmActualResultVisible = false">閉じる</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ロット→切断：生産日・切断機指定ダイアログ -->
    <el-dialog
      v-model="moveToCuttingDialogVisible"
      width="440px"
      :close-on-click-modal="false"
      class="mt-dialog"
      @close="pendingBatchRow = null"
    >
      <template #header>
        <div class="mt-dialog-header mt-dialog-header--cutting">
          <div class="mt-dialog-title-wrap">
            <span class="mt-dialog-title">切断指示の登録</span>
            <span class="mt-dialog-subtitle">生産日と切断機を指定してロットを移行します</span>
          </div>
        </div>
      </template>
      <div class="mt-dialog-body">
        <div class="mt-field-row">
          <div class="mt-field-label">生産日</div>
          <div class="mt-date-control">
            <el-button size="small" circle @click="moveToCuttingForm.production_day = shiftDate(moveToCuttingForm.production_day || getTodayString(), -1)">
              <el-icon><ArrowLeft/></el-icon>
            </el-button>
            <el-date-picker
              v-model="moveToCuttingForm.production_day"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="生産日を選択"
              size="small"
              class="mt-date-picker"
            />
            <el-button size="small" circle @click="moveToCuttingForm.production_day = shiftDate(moveToCuttingForm.production_day || getTodayString(), 1)">
              <el-icon><ArrowRight/></el-icon>
            </el-button>
            <el-button size="small" plain class="mt-today-btn" @click="moveToCuttingForm.production_day = getTodayString()">今日</el-button>
          </div>
        </div>
        <div class="mt-field-row mt-machine-row">
          <div class="mt-field-label">切断機</div>
          <div class="mt-machine-grid">
            <el-button
              v-for="m in cuttingMachineOptionsFiltered"
              :key="m.machine_name"
              size="small"
              :type="moveToCuttingForm.cutting_machine === m.machine_name ? 'primary' : 'default'"
              class="mt-machine-btn"
              @click="moveToCuttingForm.cutting_machine = m.machine_name"
            >
              {{ m.machine_name }}
            </el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="mt-dialog-footer">
          <el-button size="small" @click="moveToCuttingDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" size="small" :loading="moveToCuttingSubmitting" class="mt-submit-btn" @click="submitMoveToCutting">
            <el-icon style="margin-right:4px"><Check /></el-icon>登録
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 面取ロット→面取指示：生産日・面取機指定ダイアログ -->
    <el-dialog
      v-model="moveToChamferingDialogVisible"
      width="440px"
      :close-on-click-modal="false"
      class="mt-dialog"
      @close="pendingChamferingBatchRow = null; moveToChamferingForm.production_line_2 = ''"
    >
      <template #header>
        <div class="mt-dialog-header mt-dialog-header--chamfering">
          <div class="mt-dialog-title-wrap">
            <span class="mt-dialog-title">面取指示の登録</span>
            <span class="mt-dialog-subtitle">生産日と面取機を指定してロットを移行します</span>
          </div>
        </div>
      </template>
      <div class="mt-dialog-body">
        <div class="mt-field-row">
          <div class="mt-field-label">生産日</div>
          <div class="mt-date-control">
            <el-button size="small" circle @click="moveToChamferingForm.production_day = shiftDate(moveToChamferingForm.production_day || getTodayString(), -1)">
              <el-icon><ArrowLeft/></el-icon>
            </el-button>
            <el-date-picker
              v-model="moveToChamferingForm.production_day"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="生産日を選択"
              size="small"
              class="mt-date-picker"
            />
            <el-button size="small" circle @click="moveToChamferingForm.production_day = shiftDate(moveToChamferingForm.production_day || getTodayString(), 1)">
              <el-icon><ArrowRight/></el-icon>
            </el-button>
            <el-button size="small" plain class="mt-today-btn" @click="moveToChamferingForm.production_day = getTodayString()">今日</el-button>
          </div>
        </div>

        <div class="mt-field-row" :class="{'mt-field-col': true}">
          <div class="mt-field-label">面取機</div>
          <el-select
            v-model="moveToChamferingForm.production_line"
            placeholder="面取機を選択"
            filterable
            clearable
            size="small"
            class="mt-select-full"
          >
            <el-option
              v-for="m in chamferingMachineOptions"
              :key="m.machine_name"
              :label="m.machine_name"
              :value="m.machine_name"
            />
          </el-select>
        </div>

        <div class="mt-field-row mt-field-col" v-if="pendingChamferingBatchRow?.has_sw_process">
          <div class="mt-field-label">面取機（SW）</div>
          <el-select
            v-model="moveToChamferingForm.production_line_2"
            placeholder="面取機（SW）を選択"
            filterable
            clearable
            size="small"
            class="mt-select-full"
          >
            <el-option
              v-for="m in chamferingMachineOptions"
              :key="m.machine_name"
              :label="m.machine_name"
              :value="m.machine_name"
            />
          </el-select>
        </div>
      </div>
      <template #footer>
        <div class="mt-dialog-footer">
          <el-button size="small" @click="moveToChamferingDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" size="small" :loading="moveToChamferingSubmitting" class="mt-submit-btn mt-submit-btn--chamfering" @click="submitMoveToChamfering">
            <el-icon style="margin-right:4px"><Check /></el-icon>登録
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 切断指示：双击编辑（切断機・生産数・生産順・備考） -->
    <el-dialog
      v-model="cuttingEditDialogVisible"
      width="504px"
      :close-on-click-modal="false"
      class="cutting-edit-dialog"
      @close="editingCuttingId = null"
    >
      <template #header>
        <div class="cutting-edit-dialog__header">
          <span class="cutting-edit-dialog__title">切断指示編集</span>
        </div>
      </template>
      <el-form :model="cuttingEditForm" label-width="72px" label-position="left" class="cutting-edit-form">
        <el-row :gutter="12" class="cutting-edit-form-row">
          <el-col :span="12">
            <el-form-item label="切断機" class="cutting-edit-form-item">
              <el-select
                v-model="cuttingEditForm.cutting_machine"
                placeholder="切断機を選択"
                filterable
                clearable
                size="small"
                style="width: 100%"
              >
                <el-option
                  v-for="m in cuttingMachineOptionsFiltered"
                  :key="m.machine_name"
                  :label="m.machine_name"
                  :value="m.machine_name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生産順" class="cutting-edit-form-item">
              <el-input-number
                v-model="cuttingEditForm.production_sequence"
                :min="1"
                :max="9999"
                controls-position="right"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12" class="cutting-edit-form-row">
          <el-col :span="12">
            <el-form-item label="生産数" class="cutting-edit-form-item cutting-edit-form-item--qty">
              <el-input
                v-model="cuttingEditForm.actual_production_quantity"
                placeholder="生産数"
                size="small"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="不良数" class="cutting-edit-form-item cutting-edit-form-item--defect">
              <el-input
                v-model="cuttingEditForm.defect_qty"
                placeholder="不良数"
                size="small"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12" class="cutting-edit-form-row">
          <el-col :span="12">
            <el-form-item label="ロット数" class="cutting-edit-form-item">
              <el-input-number
                v-model="cuttingEditForm.production_lot_size"
                :min="0"
                :max="9999"
                controls-position="right"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ロットNo." class="cutting-edit-form-item">
              <el-input
                v-model="cuttingEditForm.lot_number"
                placeholder="ロットNo."
                size="small"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12" class="cutting-edit-form-row">
          <el-col :span="12">
            <el-form-item label="使用サブ在庫" class="cutting-edit-form-item">
              <el-switch
                v-model="cuttingEditForm.use_material_stock_sub"
                :active-value="1"
                :inactive-value="0"
                size="small"
                active-text="サブ"
                inactive-text="主表"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="材料使用数" class="cutting-edit-form-item">
              <el-input-number
                v-model="cuttingEditForm.usage_count"
                :min="0.01"
                :max="9999"
                :step="0.1"
                :precision="4"
                controls-position="right"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="備考" class="cutting-edit-remarks cutting-edit-form-item">
          <div class="cutting-edit-remarks-btns">
            <el-button size="small" class="cutting-edit-tag-btn" @click="appendCuttingRemark('取合せ・試作')">取合せ・試作</el-button>
            <el-button size="small" class="cutting-edit-tag-btn" @click="appendCuttingRemark('取合せ')">取合せ</el-button>
            <el-button size="small" class="cutting-edit-tag-btn" @click="appendCuttingRemark('成型17号用')">成型17号用</el-button>
            <el-button size="small" class="cutting-edit-tag-btn" @click="appendCuttingRemark('青ニス')">青ニス</el-button>
            <el-button size="small" class="cutting-edit-tag-btn" @click="appendCuttingRemark('半端材本')">半端材本</el-button>
          </div>
          <el-input
            v-model="cuttingEditForm.remarks"
            type="textarea"
            :rows="2"
            placeholder="備考"
            maxlength="500"
            show-word-limit
            size="small"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="cutting-edit-dialog__footer">
          <el-button size="small" @click="cuttingEditDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" :loading="cuttingEditSubmitting" class="cutting-edit-save-btn" @click="saveCuttingEdit">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 面取指示：双击编辑（面取機・生産数・生産順・備考） -->
    <el-dialog
      v-model="chamferingEditDialogVisible"
      width="504px"
      :close-on-click-modal="false"
      class="cutting-edit-dialog chamfering-edit-dialog"
      @close="editingChamferingId = null"
    >
      <template #header>
        <div class="cutting-edit-dialog__header">
          <span class="cutting-edit-dialog__title">面取指示編集</span>
        </div>
      </template>
      <el-form :model="chamferingEditForm" label-width="72px" label-position="left" class="cutting-edit-form chamfering-edit-form">
        <el-row :gutter="12" class="cutting-edit-form-row">
          <el-col :span="12">
            <el-form-item label="面取機" class="cutting-edit-form-item">
              <el-select
                v-model="chamferingEditForm.chamfering_machine"
                placeholder="面取機を選択"
                filterable
                clearable
                size="small"
                style="width: 100%"
              >
                <el-option
                  v-for="m in chamferingMachineOptions"
                  :key="m.machine_name"
                  :label="m.machine_name"
                  :value="m.machine_name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生産順" class="cutting-edit-form-item">
              <el-input-number
                v-model="chamferingEditForm.production_sequence"
                :min="1"
                :max="9999"
                controls-position="right"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12" class="cutting-edit-form-row">
          <el-col :span="12">
            <el-form-item label="生産数" class="cutting-edit-form-item cutting-edit-form-item--qty">
              <el-input
                v-model="chamferingEditForm.actual_production_quantity"
                placeholder="生産数"
                size="small"
                clearable
                style="width: 100%"
                @input="onChamferingEditProductionQuantityInput"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="不良数" class="cutting-edit-form-item cutting-edit-form-item--defect">
              <el-input
                v-model="chamferingEditForm.defect_qty"
                placeholder="不良数"
                size="small"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12" class="cutting-edit-form-row">
          <el-col :span="12">
            <el-form-item label="ロット数" class="cutting-edit-form-item">
              <el-input-number
                v-model="chamferingEditForm.production_lot_size"
                :min="0"
                :max="9999"
                controls-position="right"
                size="small"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ロットNo." class="cutting-edit-form-item">
              <el-input
                v-model="chamferingEditForm.lot_number"
                placeholder="ロットNo."
                size="small"
                clearable
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="備考" class="cutting-edit-form-item">
          <el-input
            v-model="chamferingEditForm.remarks"
            type="textarea"
            :rows="2"
            placeholder="備考"
            maxlength="500"
            show-word-limit
            size="small"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="cutting-edit-dialog__footer">
          <el-button size="small" @click="chamferingEditDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" :loading="chamferingEditSubmitting" class="cutting-edit-save-btn chamfering-edit-save-btn" @click="saveChamferingEdit">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 面取指示：新規追加ダイアログ（chamfering_management 構造に合わせたフォーム） -->
    <el-dialog
      v-model="chamferingNewDialogVisible"
      title="面取指示 - 新規追加"
      width="min(96vw, 480px)"
      :close-on-click-modal="false"
      class="chamfering-new-dialog"
      @closed="resetChamferingNewForm"
    >
      <el-form :model="chamferingNewForm" label-width="82px" label-position="left" class="chamfering-new-form">
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="生産日" required>
              <el-date-picker
                v-model="chamferingNewForm.production_day"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="生産日"
                size="small"
                style="width: 100%"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="ライン">
              <el-select
                v-model="chamferingNewForm.production_line"
                placeholder="ラインを選択"
                filterable
                clearable
                size="small"
                style="width: 100%"
              >
                <el-option
                  v-for="m in machineOptions"
                  :key="m.machine_name"
                  :label="m.machine_name"
                  :value="m.machine_name"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="面取機" required>
              <el-select
                v-model="chamferingNewForm.chamfering_machine"
                placeholder="面取機を選択"
                filterable
                clearable
                size="small"
                style="width: 100%"
              >
                <el-option
                  v-for="m in chamferingMachineOptions"
                  :key="m.machine_name"
                  :label="m.machine_name"
                  :value="m.machine_name"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生産順">
              <el-input-number
                v-model="chamferingNewForm.production_sequence"
                :min="1"
                :max="9999"
                controls-position="right"
                size="small"
                style="width: 100%"
                placeholder="省略時は自動"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="製品CD" required>
          <el-select
            v-model="chamferingNewForm.product_cd"
            placeholder="製品を選択（面取工程）"
            filterable
            clearable
            size="small"
            style="width: 100%"
            @change="onChamferingNewProductChange"
          >
            <el-option
              v-for="p in chamferingProductOptions"
              :key="p.product_cd"
              :label="`${p.product_cd} ${p.product_name || ''}`"
              :value="p.product_cd"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="製品名">
          <el-input v-model="chamferingNewForm.product_name" placeholder="製品CD選択で自動入力" size="small" readonly />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="生産数">
              <el-input v-model="chamferingNewForm.actual_production_quantity" placeholder="生産数" size="small" clearable />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="原材料">
              <el-select
                v-model="chamferingNewForm.material_name"
                placeholder="原材料を選択"
                filterable
                clearable
                size="small"
                style="width: 100%"
              >
                <el-option
                  v-for="mat in chamferingMaterialOptions"
                  :key="mat.material_cd"
                  :label="mat.material_name"
                  :value="mat.material_name"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="管理コード">
          <el-input v-model="chamferingNewForm.management_code" size="small" readonly placeholder="自動生成" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="chamfering-new-dialog__footer">
          <el-button size="small" @click="chamferingNewDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" :loading="chamferingNewSubmitting" @click="submitChamferingNew">登録</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 生産ロット：双击编辑（テーブル全項目） -->
    <el-dialog
      v-model="planEditDialogVisible"
      width="min(96vw, 900px)"
      :close-on-click-modal="false"
      class="plan-edit-dialog"
      @close="editingPlanId = null; editingChamferingPlanId = null"
    >
      <template #header>
        <div class="ped-header">
          <div class="ped-header-icon"><el-icon size="16"><Calendar /></el-icon></div>
          <div class="ped-header-text">
            <span class="ped-title">ロット内容編集</span>
            <span v-if="editingChamferingPlanId" class="ped-badge">面取ロット</span>
            <span class="ped-subtitle" v-if="planEditForm.product_name">{{ planEditForm.product_name }}</span>
          </div>
        </div>
      </template>

      <div class="ped-body">
        <!-- Section 1: 基本情報 -->
        <div class="ped-section">
          <div class="ped-section-label ped-sec-blue">基本情報</div>
          <div class="ped-grid ped-grid-3">
            <div class="ped-field">
              <label class="ped-label">生産月</label>
              <el-date-picker v-model="planEditForm.production_month" type="date" value-format="YYYY-MM-DD" placeholder="生産月" size="small" style="width:100%" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">ライン</label>
              <el-input v-model="planEditForm.production_line" placeholder="ライン" size="small" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">順位</label>
              <el-input-number v-model="planEditForm.priority_order" :min="0" :max="9999" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">製品CD</label>
              <el-input v-model="planEditForm.product_cd" placeholder="製品CD" size="small" clearable />
            </div>
            <div class="ped-field ped-field-span2">
              <label class="ped-label">製品名</label>
              <el-input v-model="planEditForm.product_name" placeholder="製品名" size="small" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">計画数</label>
              <el-input-number v-model="planEditForm.planned_quantity" :min="0" :max="999999" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">生産数</label>
              <el-input-number v-model="planEditForm.actual_production_quantity" :min="0" :max="999999" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field"></div>
          </div>
        </div>

        <!-- Section 2: 日程・ロット -->
        <div class="ped-section">
          <div class="ped-section-label ped-sec-green">日程・ロット</div>
          <div class="ped-grid ped-grid-4">
            <div class="ped-field">
              <label class="ped-label">開始日</label>
              <el-date-picker v-model="planEditForm.start_date" type="date" value-format="YYYY-MM-DD" placeholder="開始日" size="small" style="width:100%" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">終了日</label>
              <el-date-picker v-model="planEditForm.end_date" type="date" value-format="YYYY-MM-DD" placeholder="終了日" size="small" style="width:100%" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">生産ロット数</label>
              <el-input-number v-model="planEditForm.production_lot_size" :min="0" :max="9999" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">ロットNo</label>
              <el-input v-model="planEditForm.lot_number" placeholder="ロットNo" size="small" clearable />
            </div>
          </div>
        </div>

        <!-- Section 3: 工程フラグ -->
        <div class="ped-section">
          <div class="ped-section-label ped-sec-amber">工程フラグ</div>
          <div class="ped-switch-row">
            <div class="ped-switch-item">
              <el-switch v-model="planEditForm.is_cutting_instructed" :active-value="1" :inactive-value="0" size="small" />
              <span class="ped-switch-label">切断指示</span>
            </div>
            <div class="ped-switch-item">
              <el-switch v-model="planEditForm.has_chamfering_process" :active-value="1" :inactive-value="0" size="small" />
              <span class="ped-switch-label">面取工程</span>
            </div>
            <div class="ped-switch-item">
              <el-switch v-model="planEditForm.is_chamfering_instructed" :active-value="1" :inactive-value="0" size="small" />
              <span class="ped-switch-label">面取指示</span>
            </div>
            <div class="ped-switch-item">
              <el-switch v-model="planEditForm.has_sw_process" :active-value="1" :inactive-value="0" size="small" />
              <span class="ped-switch-label">SW工程</span>
            </div>
            <div class="ped-switch-item">
              <el-switch v-model="planEditForm.is_sw_instructed" :active-value="1" :inactive-value="0" size="small" />
              <span class="ped-switch-label">SW指示</span>
            </div>
          </div>
        </div>

        <!-- Section 4: 寸法・材料 -->
        <div class="ped-section">
          <div class="ped-section-label ped-sec-purple">寸法・材料</div>
          <div class="ped-grid ped-grid-3">
            <div class="ped-field">
              <label class="ped-label">管理コード</label>
              <el-input v-model="planEditForm.management_code" placeholder="自動生成（保存時に再計算）" size="small" readonly />
            </div>
            <div class="ped-field">
              <label class="ped-label">取数</label>
              <el-input-number v-model="planEditForm.take_count" :min="0" :max="99999" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">切断長</label>
              <el-input-number v-model="planEditForm.cutting_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">面取長</label>
              <el-input-number v-model="planEditForm.chamfering_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">展開長</label>
              <el-input-number v-model="planEditForm.developed_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">端材長(mm)</label>
              <el-input-number v-model="planEditForm.scrap_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="ped-field">
              <label class="ped-label">原材料</label>
              <el-input v-model="planEditForm.material_name" placeholder="原材料" size="small" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">材料メーカー</label>
              <el-input v-model="planEditForm.material_manufacturer" placeholder="材料メーカー" size="small" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">規格</label>
              <el-input v-model="planEditForm.standard_specification" placeholder="規格" size="small" clearable />
            </div>
            <div class="ped-field">
              <label class="ped-label">使用サブ在庫</label>
              <el-switch v-model="planEditForm.use_material_stock_sub" :active-value="1" :inactive-value="0" size="small" active-text="サブ" inactive-text="主表" />
            </div>
            <div class="ped-field">
              <label class="ped-label">材料使用数</label>
              <el-input
                v-model.number="planEditForm.usage_count"
                type="number"
                size="small"
                style="width:100%"
                min="0.01"
                max="9999"
              />
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="ped-footer">
          <el-button size="small" @click="planEditDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" :loading="planEditSubmitting" @click="savePlanEdit">
            <el-icon style="margin-right:4px"><Check /></el-icon>保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 生産数：未完了分を翌日へ順延 -->
    <el-dialog
      v-model="splitToNextDayDialogVisible"
      width="420px"
      class="split-to-next-day-dialog"
      :close-on-click-modal="false"
      @close="splitDialogRow = null"
    >
      <template #header>
        <div class="snd-header">
          <div class="snd-header-icon">
            <el-icon size="16"><DArrowRight /></el-icon>
          </div>
          <div class="snd-header-text">
            <span class="snd-title">未完了分を翌日へ順延</span>
            <span class="snd-subtitle" v-if="splitDialogRow">{{ splitDialogRow.product_name ?? splitDialogRow.product_cd ?? '' }}</span>
          </div>
        </div>
      </template>

      <div v-if="splitDialogRow" class="snd-body">
        <!-- 元データ概要カード -->
        <div class="snd-info-card">
          <div class="snd-info-row">
            <span class="snd-info-label">生産日</span>
            <span class="snd-info-value">{{ formatDateOnly(String(splitDialogRow.production_day ?? '')) || '-' }}</span>
          </div>
          <div class="snd-info-row">
            <span class="snd-info-label">切断機</span>
            <span class="snd-info-value">{{ splitDialogRow.cutting_machine ?? '-' }}</span>
          </div>
          <div class="snd-info-row">
            <span class="snd-info-label">元生産数</span>
            <span class="snd-info-value snd-info-qty">{{ splitDialogRow.actual_production_quantity ?? 0 }}</span>
          </div>
        </div>

        <!-- 入力フォーム -->
        <div class="snd-form-section">
          <div class="snd-section-label">分割設定</div>
          <div class="snd-form-grid">
            <div class="snd-field">
              <label class="snd-field-label">当日完成数 <span class="snd-required">*</span></label>
              <el-input
                ref="splitTodayQuantityInputRef"
                v-model="splitTodayQuantityInput"
                type="text"
                inputmode="numeric"
                placeholder="0"
                maxlength="8"
                size="small"
                class="snd-qty-input"
                @input="onSplitTodayQuantityInput"
              >
                <template #suffix>
                  <span class="snd-input-suffix">個</span>
                </template>
              </el-input>
            </div>
            <div class="snd-field">
              <label class="snd-field-label">翌日順延数</label>
              <div class="snd-remainder-badge">
                {{ Math.max(0, (splitDialogRow.actual_production_quantity ?? 0) - (parseInt(splitTodayQuantityInput, 10) || 0)) }}
                <span class="snd-remainder-unit">個</span>
              </div>
            </div>
          </div>
          <div class="snd-field snd-field-full">
            <label class="snd-field-label">翌日の生産日</label>
            <el-date-picker
              v-model="splitNextDay"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="省略時は自動（+1日）"
              size="small"
              style="width:100%"
              :disabled-date="disabledWeekendDate"
            />
          </div>
        </div>

        <!-- 説明 -->
        <p class="snd-hint">
          <el-icon style="margin-right:4px;color:#f59e0b"><Warning /></el-icon>
          順延後、元の行は自動的に「完了」になります。
        </p>
      </div>

      <template #footer>
        <div class="snd-footer">
          <el-button size="small" @click="splitToNextDayDialogVisible = false">取消</el-button>
          <el-button
            type="warning"
            size="small"
            :loading="splitToNextDaySubmitting"
            @click="confirmSplitToNextDay"
          >
            <el-icon style="margin-right:4px"><DArrowRight /></el-icon>順延する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 面取指示：未完了分を翌日へ順延 -->
    <el-dialog
      v-model="chamferingSplitDialogVisible"
      width="420px"
      class="split-to-next-day-dialog chamfering-snd-dialog"
      :close-on-click-modal="false"
      @close="chamferingSplitDialogRow = null"
    >
      <template #header>
        <div class="snd-header">
          <div class="snd-header-icon">
            <el-icon size="16"><DArrowRight /></el-icon>
          </div>
          <div class="snd-header-text">
            <span class="snd-title">未完了分を翌日へ順延</span>
            <span class="snd-subtitle" v-if="chamferingSplitDialogRow">{{ chamferingSplitDialogRow.product_name ?? chamferingSplitDialogRow.product_cd ?? '' }}</span>
          </div>
        </div>
      </template>

      <div v-if="chamferingSplitDialogRow" class="snd-body">
        <div class="snd-info-card">
          <div class="snd-info-row">
            <span class="snd-info-label">生産日</span>
            <span class="snd-info-value">{{ formatDateOnly(String(chamferingSplitDialogRow.production_day ?? '')) || '-' }}</span>
          </div>
          <div class="snd-info-row">
            <span class="snd-info-label">面取機</span>
            <span class="snd-info-value">{{ chamferingSplitDialogRow.chamfering_machine ?? '-' }}</span>
          </div>
          <div class="snd-info-row">
            <span class="snd-info-label">元生産数</span>
            <span class="snd-info-value snd-info-qty">{{ chamferingSplitDialogRow.actual_production_quantity ?? 0 }}</span>
          </div>
        </div>

        <div class="snd-form-section">
          <div class="snd-section-label">分割設定</div>
          <div class="snd-form-grid">
            <div class="snd-field">
              <label class="snd-field-label">当日完成数 <span class="snd-required">*</span></label>
              <el-input
                ref="chamferingSplitTodayQuantityInputRef"
                v-model="chamferingSplitTodayQuantityInput"
                type="text"
                inputmode="numeric"
                placeholder="0"
                maxlength="8"
                size="small"
                class="snd-qty-input"
                @input="onChamferingSplitTodayQuantityInput"
              >
                <template #suffix>
                  <span class="snd-input-suffix">個</span>
                </template>
              </el-input>
            </div>
            <div class="snd-field">
              <label class="snd-field-label">翌日順延数</label>
              <div class="snd-remainder-badge">
                {{ Math.max(0, (chamferingSplitDialogRow.actual_production_quantity ?? 0) - (parseInt(chamferingSplitTodayQuantityInput, 10) || 0)) }}
                <span class="snd-remainder-unit">個</span>
              </div>
            </div>
          </div>
          <div class="snd-field snd-field-full">
            <label class="snd-field-label">翌日の生産日</label>
            <el-date-picker
              v-model="chamferingSplitNextDay"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="省略時は自動（+1日）"
              size="small"
              style="width:100%"
              :disabled-date="disabledWeekendDate"
            />
          </div>
        </div>

        <p class="snd-hint">
          <el-icon style="margin-right:4px;color:#f59e0b"><Warning /></el-icon>
          順延後、元の行は自動的に「完了」になります。
        </p>
      </div>

      <template #footer>
        <div class="snd-footer">
          <el-button size="small" @click="chamferingSplitDialogVisible = false">取消</el-button>
          <el-button
            type="warning"
            size="small"
            :loading="chamferingSplitSubmitting"
            @click="confirmChamferingSplit"
          >
            <el-icon style="margin-right:4px"><DArrowRight /></el-icon>順延する
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- データ管理：instruction_plans 全件表示＋筛选 -->
    <el-dialog
      v-model="dataManagementDialogVisible"
      title="データ管理"
      width="min(98vw, 1200px)"
      destroy-on-close
      class="data-management-dialog"
      @open="loadDataManagementList"
    >
      <div class="data-management-toolbar">
        <el-form :model="dataManagementFilter" inline size="small" class="filter-form">
          <el-form-item label="生産月">
            <el-select v-model="dataManagementFilter.production_month" placeholder="YYYY-MM" clearable filterable style="width: 110px" @change="loadDataManagementList">
              <el-option v-for="m in scheduleMonths" :key="m.value" :label="m.label" :value="m.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="ライン">
            <el-select v-model="dataManagementFilter.equipment" placeholder="全部" clearable filterable style="width: 120px" popper-class="data-management-product-select-dropdown">
              <el-option label="（全部）" value="" />
              <el-option v-for="line in dataManagementLineOptions" :key="line" :label="line" :value="line" />
            </el-select>
          </el-form-item>
          <el-form-item label="製品名">
            <el-select v-model="dataManagementFilter.product_name" placeholder="全部" clearable filterable style="width: 160px" popper-class="data-management-product-select-dropdown">
              <el-option label="（全部）" value="" />
              <el-option v-for="name in dataManagementProductNameOptions" :key="name" :label="name" :value="name" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="openNewRecordDialog(false)">+ 新規追加</el-button>
            <el-button type="default" size="small" class="btn-trial-add" @click="openNewRecordDialog(true)">試作追加</el-button>
          </el-form-item>
        </el-form>
      </div>
      <div class="data-management-table-wrap">
        <el-table
          v-loading="dataManagementLoading"
          :data="paginatedDataManagementList"
          size="small"
          stripe
          border
          max-height="65vh"
          style="width: 100%"
        >
          <!-- 1. 生産月 -->
          <el-table-column prop="production_month" label="生産月" width="92" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'production_month')">
                <el-date-picker
                  :model-value="row.production_month ? String(row.production_month).slice(0, 10) : ''"
                  type="date"
                  value-format="YYYY-MM-DD"
                  size="small"
                  style="width: 100%"
                  @change="(v: string) => saveDataManagementCell(row, 'production_month', v)"
                  @blur="dataManagementEditingCell = null"
                />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'production_month')">{{ row.production_month ? String(row.production_month).slice(0, 7) : '-' }}</span>
            </template>
          </el-table-column>

          <!-- 2. ライン -->
          <el-table-column prop="production_line" label="ライン" width="70" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'production_line')">
                <el-input :model-value="row.production_line ?? ''" size="small" @update:model-value="(v) => (row.production_line = v ?? '')" @blur="saveDataManagementCell(row, 'production_line', row.production_line ?? '')" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'production_line')">{{ row.production_line || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 3. 順位 -->
          <el-table-column prop="priority_order" label="順位" width="45" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'priority_order')">
                <el-input-number :model-value="row.priority_order ?? null" size="small" :min="0" :max="9999" controls-position="right" style="width: 100%" @change="(v: number | undefined) => saveDataManagementCell(row, 'priority_order', v ?? null)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'priority_order')">{{ row.priority_order ?? '-' }}</span>
            </template>
          </el-table-column>

          <!-- 4. 製品名 -->
          <el-table-column prop="product_name" label="製品名" min-width="120" show-overflow-tooltip>
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'product_name')">
                <el-input :model-value="row.product_name ?? ''" size="small" @update:model-value="(v) => (row.product_name = v ?? '')" @blur="saveDataManagementCell(row, 'product_name', row.product_name ?? '')" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'product_name')">{{ row.product_name || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 5. 原材料 -->
          <el-table-column prop="material_name" label="原材料" width="120" show-overflow-tooltip align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'material_name')">
                <el-input :model-value="row.material_name ?? ''" size="small" @update:model-value="(v) => (row.material_name = v ?? '')" @blur="saveDataManagementCell(row, 'material_name', row.material_name ?? '')" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'material_name')">{{ row.material_name || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 6. 計画数 -->
          <el-table-column prop="planned_quantity" label="計画数" width="72" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'planned_quantity')">
                <el-input-number :model-value="row.planned_quantity ?? null" size="small" :min="0" controls-position="right" style="width: 100%" @change="(v: number | undefined) => saveDataManagementCell(row, 'planned_quantity', v ?? null)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'planned_quantity')">{{ row.planned_quantity ?? '-' }}</span>
            </template>
          </el-table-column>

          <!-- 7. ロット数 -->
          <el-table-column prop="production_lot_size" label="ロット数" width="70" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'production_lot_size')">
                <el-input-number :model-value="row.production_lot_size ?? null" size="small" :min="0" controls-position="right" style="width: 100%" @change="(v: number | undefined) => saveDataManagementCell(row, 'production_lot_size', v ?? null)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'production_lot_size')">{{ row.production_lot_size ?? '-' }}</span>
            </template>
          </el-table-column>

          <!-- 8. ロットNo -->
          <el-table-column prop="lot_number" label="No." width="50" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'lot_number')">
                <el-input :model-value="row.lot_number ?? ''" size="small" @update:model-value="(v) => (row.lot_number = v ?? '')" @blur="saveDataManagementCell(row, 'lot_number', row.lot_number ?? '')" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'lot_number')">{{ row.lot_number || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 9. 生産数 -->
          <el-table-column prop="actual_production_quantity" label="生産数" width="72" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'actual_production_quantity')">
                <el-input-number :model-value="row.actual_production_quantity ?? null" size="small" :min="0" controls-position="right" style="width: 100%" @change="(v: number | undefined) => saveDataManagementCell(row, 'actual_production_quantity', v ?? null)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'actual_production_quantity')">{{ row.actual_production_quantity ?? '-' }}</span>
            </template>
          </el-table-column>

          <!-- 10. 開始日 -->
          <el-table-column prop="start_date" label="開始日" width="96" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'start_date')">
                <el-date-picker :model-value="row.start_date ? String(row.start_date).slice(0, 10) : ''" type="date" value-format="YYYY-MM-DD" size="small" style="width: 100%" @change="(v: string) => saveDataManagementCell(row, 'start_date', v)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'start_date')">{{ row.start_date ? String(row.start_date).slice(0, 10) : '-' }}</span>
            </template>
          </el-table-column>

          <!-- 11. 終了日 -->
          <el-table-column prop="end_date" label="終了日" width="96" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'end_date')">
                <el-date-picker :model-value="row.end_date ? String(row.end_date).slice(0, 10) : ''" type="date" value-format="YYYY-MM-DD" size="small" style="width: 100%" @change="(v: string) => saveDataManagementCell(row, 'end_date', v)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'end_date')">{{ row.end_date ? String(row.end_date).slice(0, 10) : '-' }}</span>
            </template>
          </el-table-column>

          <!-- 12. 面取工程 -->
          <el-table-column prop="has_chamfering_process" label="面取工程" width="78" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'has_chamfering_process')">
                <el-switch :model-value="!!row.has_chamfering_process" size="small" @change="(v: string | number | boolean) => saveDataManagementCell(row, 'has_chamfering_process', v ? 1 : 0)" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'has_chamfering_process')">{{ row.has_chamfering_process ? '○' : '-' }}</span>
            </template>
          </el-table-column>

          <!-- 13. SW工程 -->
          <el-table-column prop="has_sw_process" label="SW工程" width="70" align="center">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'has_sw_process')">
                <el-switch :model-value="!!row.has_sw_process" size="small" @change="(v: string | number | boolean) => saveDataManagementCell(row, 'has_sw_process', v ? 1 : 0)" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'has_sw_process')">{{ row.has_sw_process ? '○' : '-' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div class="data-management-footer">
        <span class="total-text">計 {{ filteredDataManagementList.length }} 件</span>
        <el-pagination
          v-model:current-page="dataManagementPagination.currentPage"
          v-model:page-size="dataManagementPagination.pageSize"
          :page-sizes="[30, 50, 100]"
          :total="filteredDataManagementList.length"
          size="small"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="dataManagementPagination.currentPage = 1"
          @current-change="() => {}"
        />
      </div>
    </el-dialog>

    <el-dialog
      v-model="cuttingDoneDialogVisible"
      title="切断済リスト"
      width="min(98vw, 1200px)"
      destroy-on-close
      class="cutting-done-dialog"
      @open="loadCuttingDoneList"
    >
      <div class="cutting-done-toolbar">
        <el-form :model="cuttingDoneFilter" inline size="small" class="filter-form">
          <el-form-item label="期間">
            <el-date-picker
              v-model="cuttingDoneFilter.period"
              type="daterange"
              range-separator="~"
              start-placeholder="開始日"
              end-placeholder="終了日"
              value-format="YYYY-MM-DD"
              style="width: 260px"
              @change="onCuttingDoneFilterChange"
            />
          </el-form-item>
          <el-form-item label="製品名">
            <el-select
              v-model="cuttingDoneFilter.product_name"
              placeholder="全部"
              clearable
              filterable
              style="width: 180px"
              popper-class="data-management-product-select-dropdown"
              @change="onCuttingDoneFilterChange"
            >
              <el-option label="（全部）" value="" />
              <el-option v-for="name in cuttingDoneProductNameOptions" :key="name" :label="name" :value="name" />
            </el-select>
          </el-form-item>
          <el-form-item label="生産完了チェック">
            <el-switch
              v-model="cuttingDoneFilter.only_completed"
              inline-prompt
              active-text="完了のみ"
              inactive-text="全部"
              @change="onCuttingDoneFilterChange"
            />
          </el-form-item>
          <el-form-item>
            <el-button size="small" @click="resetCuttingDoneFilter">リセット</el-button>
          </el-form-item>
        </el-form>
      </div>
      <div class="cutting-done-table-wrap">
        <el-table
          v-loading="cuttingDoneLoading"
          :data="cuttingDoneListPaged"
          size="small"
          stripe
          border
          max-height="65vh"
          style="width: 100%"
        >
          <el-table-column prop="production_day" label="生産日" width="104" align="center">
            <template #default="{ row }">{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
          </el-table-column>
          <el-table-column prop="production_line" label="ライン" width="94" align="center" show-overflow-tooltip />
          <el-table-column prop="cutting_machine" label="切断機" width="106" align="center" show-overflow-tooltip />
          <el-table-column prop="product_cd" label="製品CD" width="112" align="center" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="166" show-overflow-tooltip />
          <el-table-column prop="actual_production_quantity" label="生産数" width="84" align="right" />
          <el-table-column prop="defect_qty" label="不良数" width="84" align="right" />
          <el-table-column prop="production_completed_check" label="生産完了" width="92" align="center">
            <template #default="{ row }">{{ row.production_completed_check ? '切断済' : '未切断' }}</template>
          </el-table-column>
          <el-table-column label="管理コード" width="122" align="center">
            <template #default="{ row }">{{ getManagementCodeLast5(row) }}</template>
          </el-table-column>
        </el-table>
      </div>
      <div class="cutting-done-footer">
        <span class="total-text">計 {{ cuttingDoneListFiltered.length }} 件</span>
        <el-pagination
          v-model:current-page="cuttingDonePagination.currentPage"
          v-model:page-size="cuttingDonePagination.pageSize"
          :page-sizes="[30, 50, 100]"
          :total="cuttingDoneListFiltered.length"
          size="small"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="cuttingDonePagination.currentPage = 1"
          @current-change="() => {}"
        />
      </div>
    </el-dialog>

    <el-dialog
      v-model="chamferingDoneDialogVisible"
      title="面取済リスト"
      width="min(98vw, 1200px)"
      destroy-on-close
      class="chamfering-done-dialog"
      @open="loadChamferingDoneList"
    >
      <div class="chamfering-done-toolbar">
        <el-form :model="chamferingDoneFilter" inline size="small" class="filter-form">
          <el-form-item label="期間">
            <el-date-picker
              v-model="chamferingDoneFilter.period"
              type="daterange"
              range-separator="~"
              start-placeholder="開始日"
              end-placeholder="終了日"
              value-format="YYYY-MM-DD"
              style="width: 260px"
              @change="onChamferingDoneFilterChange"
            />
          </el-form-item>
          <el-form-item label="製品名">
            <el-select
              v-model="chamferingDoneFilter.product_name"
              placeholder="全部"
              clearable
              filterable
              style="width: 180px"
              popper-class="data-management-product-select-dropdown"
              @change="onChamferingDoneFilterChange"
            >
              <el-option label="（全部）" value="" />
              <el-option v-for="name in chamferingDoneProductNameOptions" :key="name" :label="name" :value="name" />
            </el-select>
          </el-form-item>
          <el-form-item label="生産完了チェック">
            <el-switch
              v-model="chamferingDoneFilter.only_completed"
              inline-prompt
              active-text="完了のみ"
              inactive-text="全部"
              @change="onChamferingDoneFilterChange"
            />
          </el-form-item>
          <el-form-item>
            <el-button size="small" @click="resetChamferingDoneFilter">リセット</el-button>
          </el-form-item>
        </el-form>
      </div>
      <div class="chamfering-done-table-wrap">
        <el-table
          v-loading="chamferingDoneLoading"
          :data="chamferingDoneListPaged"
          size="small"
          stripe
          border
          max-height="65vh"
          style="width: 100%"
        >
          <el-table-column prop="production_day" label="生産日" width="104" align="center">
            <template #default="{ row }">{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
          </el-table-column>
          <el-table-column prop="production_line" label="ライン" width="94" align="center" show-overflow-tooltip />
          <el-table-column prop="chamfering_machine" label="面取機" width="106" align="center" show-overflow-tooltip />
          <el-table-column prop="product_cd" label="製品CD" width="112" align="center" show-overflow-tooltip />
          <el-table-column prop="product_name" label="製品名" min-width="166" show-overflow-tooltip />
          <el-table-column prop="actual_production_quantity" label="生産数" width="84" align="right" />
          <el-table-column prop="defect_qty" label="不良数" width="84" align="right" />
          <el-table-column prop="production_completed_check" label="生産完了" width="92" align="center">
            <template #default="{ row }">{{ row.production_completed_check ? '面取済' : '未面取' }}</template>
          </el-table-column>
          <el-table-column label="管理コード" width="122" align="center">
            <template #default="{ row }">{{ getManagementCodeLast5Chamfering(row) }}</template>
          </el-table-column>
        </el-table>
      </div>
      <div class="chamfering-done-footer">
        <span class="total-text">計 {{ chamferingDoneListFiltered.length }} 件</span>
        <el-pagination
          v-model:current-page="chamferingDonePagination.currentPage"
          v-model:page-size="chamferingDonePagination.pageSize"
          :page-sizes="[30, 50, 100]"
          :total="chamferingDoneListFiltered.length"
          size="small"
          layout="total, sizes, prev, pager, next"
          background
          @size-change="chamferingDonePagination.currentPage = 1"
          @current-change="() => {}"
        />
      </div>
    </el-dialog>

    <!-- 新規追加ダイアログ（新規＝量産品 / 試作＝試作品） -->
    <el-dialog
      v-model="newRecordDialogVisible"
      width="min(96vw, 580px)"
      :close-on-click-modal="false"
      class="new-record-dialog"
      :show-close="false"
    >
      <template #header>
        <div class="nr-header" :class="newRecordIsTrialMode ? 'nr-header--trial' : 'nr-header--normal'">
          <div class="nr-header-icon">
            <el-icon size="16"><DocumentCopy v-if="newRecordIsTrialMode" /><Calendar v-else /></el-icon>
          </div>
          <div class="nr-header-text">
            <span class="nr-title">{{ newRecordIsTrialMode ? '試作ロット追加' : '新規ロット追加' }}</span>
            <span class="nr-subtitle">{{ newRecordIsTrialMode ? '試作品' : '量産品' }}</span>
          </div>
          <el-button class="nr-close-btn" text @click="newRecordDialogVisible = false">
            <el-icon size="15"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></el-icon>
          </el-button>
        </div>
      </template>

      <div class="nr-body">
        <!-- ■ 基本情報 -->
        <div class="nr-section">
          <div class="nr-sec-hd"><span class="nr-sec-dot nr-dot-blue"></span>基本情報</div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">生産月<em>*</em></span>
              <el-date-picker v-model="newRecordForm.production_month" type="month" value-format="YYYY-MM" placeholder="YYYY-MM" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">ライン</span>
              <el-select v-model="newRecordForm.production_line" placeholder="成型ライン" filterable clearable size="small" style="width:100%">
                <el-option v-for="opt in newRecordLineOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
              </el-select>
            </div>
            <div class="nr-col">
              <span class="nr-lbl">優先順位</span>
              <el-input-number v-model="newRecordForm.priority_order" :min="0" :max="9999" controls-position="right" size="small" style="width:100%" />
            </div>
          </div>
          <div class="nr-row1">
            <div class="nr-col">
              <span class="nr-lbl">製品<em>*</em></span>
              <el-select v-model="newRecordForm.product_cd" placeholder="製品名／CDで検索・選択" filterable clearable size="small" style="width:100%" @change="onNewRecordProductChange">
                <el-option v-for="p in newRecordProductOptions" :key="p.product_cd" :label="`${p.product_name}  [${p.product_cd}]`" :value="p.product_cd" />
              </el-select>
            </div>
          </div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">製品名（確認）</span>
              <el-input v-model="newRecordForm.product_name" size="small" readonly style="background:#f8fafc" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">製品CD</span>
              <el-input v-model="newRecordForm.product_cd" size="small" readonly style="background:#f8fafc" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">ロットNo</span>
              <el-input v-model="newRecordForm.lot_number" placeholder="ロットNo" size="small" />
            </div>
          </div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">原材料</span>
              <el-input v-model="newRecordForm.material_name" placeholder="原材料名" size="small" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">材料メーカー</span>
              <el-input v-model="newRecordForm.material_manufacturer" placeholder="材料メーカー" size="small" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">規格</span>
              <el-input v-model="newRecordForm.standard_specification" placeholder="規格" size="small" />
            </div>
            <div class="nr-field">
              <label class="nr-label">使用サブ在庫</label>
              <el-switch v-model="newRecordForm.use_material_stock_sub" :active-value="1" :inactive-value="0" size="small" active-text="サブ" inactive-text="主表" />
            </div>
            <div class="nr-field">
              <label class="nr-label">材料使用数</label>
              <el-input
                v-model.number="newRecordForm.usage_count"
                type="number"
                size="small"
                style="width:100%"
                min="0.01"
                max="9999"
              />
            </div>
          </div>
        </div>

        <!-- ■ 数量・寸法 -->
        <div class="nr-section">
          <div class="nr-sec-hd"><span class="nr-sec-dot nr-dot-green"></span>数量・寸法</div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">計画数</span>
              <el-input-number v-model="newRecordForm.planned_quantity" :min="0" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">ロット数</span>
              <el-input-number v-model="newRecordForm.production_lot_size" :min="0" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">生産数</span>
              <el-input-number v-model="newRecordForm.actual_production_quantity" :min="0" controls-position="right" size="small" style="width:100%" />
            </div>
          </div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">取数</span>
              <el-input-number v-model="newRecordForm.take_count" :min="0" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">切断長</span>
              <el-input-number v-model="newRecordForm.cutting_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">面取長</span>
              <el-input-number v-model="newRecordForm.chamfering_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
          </div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">展開長</span>
              <el-input-number v-model="newRecordForm.developed_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">端材長</span>
              <el-input-number v-model="newRecordForm.scrap_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col"></div>
          </div>
        </div>

        <!-- ■ 日程・工程 -->
        <div class="nr-section nr-section--last">
          <div class="nr-sec-hd"><span class="nr-sec-dot nr-dot-amber"></span>日程・工程</div>
          <div class="nr-row3 nr-row-align-end">
            <div class="nr-col">
              <span class="nr-lbl">開始日</span>
              <el-date-picker v-model="newRecordForm.start_date" type="date" value-format="YYYY-MM-DD" placeholder="YYYY-MM-DD" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">終了日</span>
              <el-date-picker v-model="newRecordForm.end_date" type="date" value-format="YYYY-MM-DD" placeholder="YYYY-MM-DD" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">工程フラグ</span>
              <div class="nr-switches">
                <label class="nr-sw-item">
                  <el-switch v-model="newRecordForm.has_chamfering_process" :active-value="1" :inactive-value="0" size="small" />
                  <span>面取</span>
                </label>
                <label class="nr-sw-item">
                  <el-switch v-model="newRecordForm.has_sw_process" :active-value="1" :inactive-value="0" size="small" />
                  <span>SW</span>
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="nr-footer">
          <el-button size="small" @click="newRecordDialogVisible = false">キャンセル</el-button>
          <el-button
            :type="newRecordIsTrialMode ? 'warning' : 'primary'"
            size="small"
            :loading="newRecordSubmitting"
            class="nr-save-btn"
            @click="createDataManagementRecord"
          >
            <el-icon style="margin-right:3px"><Check /></el-icon>保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 面取ロット一覧：新規追加ダイアログ（chamfering_plans 項目・新規ロット追加と同様の nr スタイル） -->
    <el-dialog
      v-model="chamferingPlanNewDialogVisible"
      width="min(96vw, 580px)"
      :close-on-click-modal="false"
      class="new-record-dialog chamfering-plan-new-dialog"
      :show-close="false"
      @closed="resetChamferingPlanNewForm"
    >
      <template #header>
        <div class="nr-header nr-header--normal">
          <div class="nr-header-icon">
            <el-icon size="16"><DocumentCopy /></el-icon>
          </div>
          <div class="nr-header-text">
            <span class="nr-title">面取ロット 新規追加</span>
            <span class="nr-subtitle">chamfering_plans</span>
          </div>
          <el-button class="nr-close-btn" text @click="chamferingPlanNewDialogVisible = false">
            <el-icon size="15"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></el-icon>
          </el-button>
        </div>
      </template>

      <div class="nr-body">
        <div class="nr-section">
          <div class="nr-sec-hd"><span class="nr-sec-dot nr-dot-blue"></span>基本情報</div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">生産月<em>*</em></span>
              <el-date-picker v-model="chamferingPlanNewForm.production_month" type="month" value-format="YYYY-MM" placeholder="YYYY-MM" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">生産日<em>*</em></span>
              <el-date-picker v-model="chamferingPlanNewForm.production_day" type="date" value-format="YYYY-MM-DD" placeholder="YYYY-MM-DD" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">ライン（面取機）<em>*</em></span>
              <el-select v-model="chamferingPlanNewForm.production_line" placeholder="面取機を選択" filterable clearable size="small" style="width:100%">
                <el-option v-for="m in chamferingMachineOptions" :key="m.machine_name" :label="m.machine_name" :value="m.machine_name" />
              </el-select>
            </div>
          </div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">順位</span>
              <el-input-number v-model="chamferingPlanNewForm.production_order" :min="0" :max="9999" controls-position="right" size="small" style="width:100%" placeholder="省略可" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">製品<em>*</em></span>
              <el-select v-model="chamferingPlanNewForm.product_cd" placeholder="製品を選択" filterable clearable size="small" style="width:100%" @change="onChamferingPlanNewProductChange">
                <el-option v-for="p in chamferingProductOptions" :key="p.product_cd" :label="`${p.product_name ?? ''}  [${p.product_cd}]`" :value="p.product_cd" />
              </el-select>
            </div>
            <div class="nr-col">
              <span class="nr-lbl">製品名（確認）</span>
              <el-input v-model="chamferingPlanNewForm.product_name" size="small" readonly style="background:#f8fafc" />
            </div>
          </div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">ロットNo</span>
              <el-input v-model="chamferingPlanNewForm.lot_number" placeholder="ロットNo" size="small" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">原材料</span>
              <el-input v-model="chamferingPlanNewForm.material_name" placeholder="原材料名" size="small" />
            </div>
            <div class="nr-col"></div>
          </div>
        </div>

        <div class="nr-section">
          <div class="nr-sec-hd"><span class="nr-sec-dot nr-dot-green"></span>数量・寸法</div>
          <div class="nr-row3">
            <div class="nr-col">
              <span class="nr-lbl">生産数</span>
              <el-input-number v-model="chamferingPlanNewForm.actual_production_quantity" :min="0" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">ロット数</span>
              <el-input-number v-model="chamferingPlanNewForm.production_lot_size" :min="0" controls-position="right" size="small" style="width:100%" />
            </div>
            <div class="nr-col">
              <span class="nr-lbl">面取長</span>
              <el-input-number v-model="chamferingPlanNewForm.chamfering_length" :min="0" :precision="2" controls-position="right" size="small" style="width:100%" />
            </div>
          </div>
        </div>

        <div class="nr-section nr-section--last">
          <div class="nr-sec-hd"><span class="nr-sec-dot nr-dot-amber"></span>工程</div>
          <div class="nr-row3 nr-row-align-end">
            <div class="nr-col">
              <span class="nr-lbl">SW工程</span>
              <div class="nr-switches">
                <label class="nr-sw-item">
                  <el-switch v-model="chamferingPlanNewForm.has_sw_process" :active-value="1" :inactive-value="0" size="small" />
                  <span>SW</span>
                </label>
              </div>
            </div>
            <div class="nr-col"></div>
            <div class="nr-col"></div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="nr-footer">
          <el-button size="small" @click="chamferingPlanNewDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" size="small" :loading="chamferingPlanNewSubmitting" class="nr-save-btn" @click="saveChamferingPlanNew">
            <el-icon style="margin-right:3px"><Check /></el-icon>保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- ■ 指定日 材料数 確認ダイアログ -->
    <el-dialog
      v-model="specifiedDateDialogVisible"
      title="指定日 — 所需材料数"
      width="520px"
      class="specified-date-dialog"
      :close-on-click-modal="false"
    >
      <div class="specified-date-dialog-body">
        <div class="specified-date-controls">
          <el-button type="default" size="small" circle :icon="ArrowLeft" title="前日" @click="shiftSpecifiedDate(-1)" />
          <el-date-picker
            v-model="specifiedDate"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="日付を選択"
            size="small"
            class="specified-date-picker"
            @change="loadSpecifiedDateUsage"
          />
          <el-button type="default" size="small" circle :icon="ArrowRight" title="翌日" @click="shiftSpecifiedDate(1)" />
          <el-button size="small" plain class="specified-date-today-btn" @click="setSpecifiedDateToday">今日</el-button>
          <el-button
            type="primary"
            size="small"
            :loading="specifiedDateLoading"
            @click="loadSpecifiedDateUsage"
          >
            検索
          </el-button>
        </div>
        <div v-if="specifiedDateLoading" class="usage-dialog-loading">集計中...</div>
        <template v-else-if="specifiedDate">
          <div class="usage-preview-desc">{{ specifiedDate }} の使用材料数（材料別）</div>
          <el-table
            :data="specifiedDateUsageSummarySorted.byMaterial"
            size="small"
            border
            max-height="340"
            class="usage-preview-table specified-date-table"
          >
            <el-table-column label="原材料" min-width="160" align="center">
              <template #default="{ row }">
                <el-tooltip
                  placement="right"
                  :show-after="200"
                  popper-class="usage-product-tooltip"
                >
                  <template #content>
                    <div class="usage-tooltip-title">使用製品</div>
                    <div v-for="p in row.products" :key="p.productCd" class="usage-tooltip-row">
                      <span class="usage-tooltip-cd">{{ p.productCd }}</span>
                      <span class="usage-tooltip-name">{{ p.productName }}</span>
                    </div>
                    <div v-if="!row.products.length" class="usage-tooltip-row">-</div>
                  </template>
                  <span class="usage-material-label">{{ row.materialName }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="usageCount" label="使用数（管理コード数）" width="160" align="center" />
          </el-table>
          <div v-if="!specifiedDateUsageSummarySorted.byMaterial.length" class="usage-preview-empty">データなし</div>
          <div v-if="specifiedDateUsageSummarySorted.byMaterial.length" class="specified-date-total">
            合計：{{ specifiedDateUsageSummarySorted.totalCount }} 束
          </div>
        </template>
      </div>
      <template #footer>
        <div class="specified-date-dialog-footer">
          <el-button size="small" @click="specifiedDateDialogVisible = false">閉じる</el-button>
          <el-button type="primary" size="small" :disabled="!specifiedDateUsageSummarySorted.byMaterial.length" @click="printSpecifiedDateUsage">
            打印
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'CuttingInstruction' })

import { ref, reactive, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Check, CircleCheck, DocumentCopy, Delete, ArrowLeft, ArrowRight, DArrowRight, Warning, Refresh } from '@element-plus/icons-vue'
import request from '@/utils/request'

/** instruction_plans 一行の型（API 返却・テーブル表示と一致） */
interface CuttingPlanRow {
  id?: number
  production_month?: string
  production_line?: string
  priority_order?: number | null
  product_cd?: string
  product_name?: string
  planned_quantity?: number | null
  start_date?: string | null
  end_date?: string | null
  production_lot_size?: number | null
  lot_number?: string | null
  is_cutting_instructed?: number | null
  has_chamfering_process?: number | null
  is_chamfering_instructed?: number | null
  has_sw_process?: number | null
  is_sw_instructed?: number | null
  management_code?: string | null
  actual_production_quantity?: number | null
  take_count?: number | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  scrap_length?: number | null
  material_name?: string | null
  material_manufacturer?: string | null
  standard_specification?: string | null
  created_at?: string | null
  updated_at?: string | null
}

function formatUsageCountDisplay(row: { usage_count?: number | null }): string {
  const v = row.usage_count
  const num = v != null && !isNaN(Number(v)) ? Number(v) : 1
  return num.toFixed(1)
}

/** 日付文字列を YYYY-MM-DD で表示（ISO の先頭10文字） */
const formatDateOnly = (v: string | null | undefined) => {
  if (v == null || v === '') return ''
  const s = String(v)
  return s.slice(0, 10)
}

/** 生産ロット一覧：順位ごとの浅色背景クラス（順位数字で区別） */
function getPlanBatchPriorityClass(order: number | null | undefined): string {
  if (order == null || order === undefined) return 'plan-batch-priority-none'
  const idx = (Number(order) - 1) % 5
  return `plan-batch-priority-${idx}`
}

const planSearchForm = reactive({
  equipment: '',
  product_name: '',
  material_name: '',
})

const planPagination = reactive({
  currentPage: 1,
  pageSize: 50,
})

const plans = ref<CuttingPlanRow[]>([])
const planLoading = ref(false)
const planBatchActionLoading = ref<number | null>(null)

/** 左下：切断指示（cutting_management 表） */
/** cutting_management: instruction_plans と同様の項目 + production_day, cutting_machine, production_sequence, cd, production_completed_check */
interface CuttingManagementRow {
  id?: number
  production_month?: string | null
  production_day?: string | null
  production_line?: string | null
  cutting_machine?: string | null
  production_sequence?: number | null
  priority_order?: number | null
  product_cd?: string | null
  product_name?: string | null
  planned_quantity?: number | null
  start_date?: string | null
  end_date?: string | null
  production_lot_size?: number | null
  lot_number?: string | null
  is_cutting_instructed?: number | null
  has_chamfering_process?: number | null
  is_chamfering_instructed?: number | null
  has_sw_process?: number | null
  is_sw_instructed?: number | null
  management_code?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
  take_count?: number | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  scrap_length?: number | null
  material_name?: string | null
  material_manufacturer?: string | null
  standard_specification?: string | null
  production_completed_check?: number | null
  material_usage_reflected?: string | null
  cd?: string | null
  production_time?: number | string | null
  remarks?: string | null
  created_at?: string | null
  updated_at?: string | null
}
const cuttingManagementList = ref<CuttingManagementRow[]>([])
const cuttingManagementListTomorrow = ref<CuttingManagementRow[]>([])
const cuttingManagementLoading = ref(false)
/** 今日用・翌日用の生産日（YYYY-MM-DD）。今日默认当天，翌日默认次日（不跳过休息日） */
function getTodayString() {
  const d = new Date()
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}
function getTomorrowString() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}
/** 日期加减 N 天，返回 YYYY-MM-DD */
function shiftDate(dateStr: string, deltaDays: number): string {
  if (!dateStr || typeof dateStr !== 'string') return dateStr || getTodayString()
  const d = new Date(dateStr.slice(0, 10) + 'T12:00:00')
  d.setDate(d.getDate() + deltaDays)
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}
function shiftDateToday(delta: number) {
  selectedDateToday.value = shiftDate(selectedDateToday.value, delta)
  loadCuttingManagement()
}
function shiftDateTomorrow(delta: number) {
  selectedDateTomorrow.value = shiftDate(selectedDateTomorrow.value, delta)
  loadCuttingManagement()
}
function shiftChamferingDateToday(delta: number) {
  selectedChamferingDateToday.value = shiftDate(selectedChamferingDateToday.value, delta)
  loadChamferingManagement()
}
function shiftChamferingDateTomorrow(delta: number) {
  selectedChamferingDateTomorrow.value = shiftDate(selectedChamferingDateTomorrow.value, delta)
  loadChamferingManagement()
}
const selectedDateToday = ref(getTodayString())
const selectedDateTomorrow = ref(getTomorrowString())
/** 切断機でフィルタ（空は全件） */
const cuttingMachineFilter = ref('')
/** 切断機オプション（マスタ「切断」含む + 一覧で使用した値） */
const cuttingMachineOptions = ref<{ machine_name: string }[]>([])
/** 切断機ボタン用：外注切断を除外 */
const cuttingMachineOptionsFiltered = computed(() =>
  cuttingMachineOptions.value.filter((m) => m.machine_name !== '外注切断')
)
/** 切断指示-今日：生産数・不良・生産時間の合計 */
const cuttingTodayTotal = computed(() => {
  const list = cuttingManagementList.value
  let qty = 0
  let defect = 0
  let time = 0
  for (const row of list) {
    const n = row.actual_production_quantity
    if (n != null && typeof n === 'number' && !Number.isNaN(n)) qty += n
    else if (n != null && String(n).trim() !== '') {
      const v = Number(String(n).trim())
      if (!Number.isNaN(v)) qty += v
    }
    const d = row.defect_qty
    if (d != null && typeof d === 'number' && !Number.isNaN(d)) defect += d
    const t = row.production_time
    if (t != null && (typeof t === 'number' || typeof t === 'string')) {
      const tv = typeof t === 'number' ? t : parseFloat(String(t))
      if (!Number.isNaN(tv)) time += tv
    }
  }
  return { quantity: qty, defect, time: time === 0 ? null : Math.round(time * 10) / 10 }
})
/** 切断指示-翌日：生産数・不良・生産時間の合計 */
const cuttingTomorrowTotal = computed(() => {
  const list = cuttingManagementListTomorrow.value
  let qty = 0
  let defect = 0
  let time = 0
  for (const row of list) {
    const n = row.actual_production_quantity
    if (n != null && typeof n === 'number' && !Number.isNaN(n)) qty += n
    else if (n != null && String(n).trim() !== '') {
      const v = Number(String(n).trim())
      if (!Number.isNaN(v)) qty += v
    }
    const d = row.defect_qty
    if (d != null && typeof d === 'number' && !Number.isNaN(d)) defect += d
    const t = row.production_time
    if (t != null && (typeof t === 'number' || typeof t === 'string')) {
      const tv = typeof t === 'number' ? t : parseFloat(String(t))
      if (!Number.isNaN(tv)) time += tv
    }
  }
  return { quantity: qty, defect, time: time === 0 ? null : Math.round(time * 10) / 10 }
})
/** 面取指示-今日：生産数・不良・生産時間の合計 */
const chamferingTodayTotal = computed(() => {
  const list = chamferingManagementListToday.value
  let qty = 0
  let defect = 0
  let time = 0
  for (const row of list) {
    const n = row.actual_production_quantity
    if (n != null && typeof n === 'number' && !Number.isNaN(n)) qty += n
    else if (n != null && String(n).trim() !== '') {
      const v = Number(String(n).trim())
      if (!Number.isNaN(v)) qty += v
    }
    const d = row.defect_qty
    if (d != null && typeof d === 'number' && !Number.isNaN(d)) defect += d
    const t = row.production_time
    if (t != null && (typeof t === 'number' || typeof t === 'string')) {
      const tv = typeof t === 'number' ? t : parseFloat(String(t))
      if (!Number.isNaN(tv)) time += tv
    }
  }
  return { quantity: qty, defect, time: time === 0 ? null : Math.round(time * 10) / 10 }
})
/** 面取指示-翌日：生産数・不良・生産時間の合計 */
const chamferingTomorrowTotal = computed(() => {
  const list = chamferingManagementListTomorrow.value
  let qty = 0
  let defect = 0
  let time = 0
  for (const row of list) {
    const n = row.actual_production_quantity
    if (n != null && typeof n === 'number' && !Number.isNaN(n)) qty += n
    else if (n != null && String(n).trim() !== '') {
      const v = Number(String(n).trim())
      if (!Number.isNaN(v)) qty += v
    }
    const d = row.defect_qty
    if (d != null && typeof d === 'number' && !Number.isNaN(d)) defect += d
    const t = row.production_time
    if (t != null && (typeof t === 'number' || typeof t === 'string')) {
      const tv = typeof t === 'number' ? t : parseFloat(String(t))
      if (!Number.isNaN(tv)) time += tv
    }
  }
  return { quantity: qty, defect, time: time === 0 ? null : Math.round(time * 10) / 10 }
})
// ─────────────────────────────────────────────
// 材料使用数：計算属性（今日・翌日联合去重）
// ─────────────────────────────────────────────

/** 材料別集計の1行 */
interface UsageByMaterial {
  materialName: string
  usageCount: number
  /** この材料を使用している製品リスト（tooltip 用） */
  products: Array<{ productCd: string; productName: string }>
}
interface UsageSummary { byMaterial: UsageByMaterial[]; totalCount: number }

/** 材料別集計ヘルパー：rows から materialName 別に集計し totalCount を返す */
function buildUsageSummaryByMaterial(rows: CuttingManagementRow[]): UsageSummary {
  // materialName → { codes: Set<management_code>, products: Map<productCd, productName> }
  const map = new Map<string, { codes: Set<string>; products: Map<string, string> }>()
  for (const row of rows) {
    const code = row.management_code
    if (!code) continue
    const matKey = row.material_name?.trim() || '不明'
    if (!map.has(matKey)) map.set(matKey, { codes: new Set(), products: new Map() })
    const entry = map.get(matKey)!
    entry.codes.add(code)
    const pcd = row.product_cd ?? ''
    const pname = row.product_name ?? pcd
    if (pcd) entry.products.set(pcd, pname)
  }
  const byMaterial: UsageByMaterial[] = []
  let totalCount = 0
  for (const [materialName, v] of map) {
    const products = Array.from(v.products.entries()).map(([productCd, productName]) => ({ productCd, productName }))
    byMaterial.push({ materialName, usageCount: v.codes.size, products })
    totalCount += v.codes.size
  }
  return { byMaterial, totalCount }
}

/** 今日の使用材料数（材料別）。management_code で去重 */
const cuttingTodayUsageSummary = computed<UsageSummary>(() =>
  buildUsageSummaryByMaterial(cuttingManagementList.value)
)

// ─────────────────────────────────────────────
// 使用材料数（材料別）- 今日：独立した日付筛选
// ─────────────────────────────────────────────
const usageSummaryDateToday = ref(getTodayString())
const usageSummaryCuttingList = ref<CuttingManagementRow[]>([])
const usageSummaryCuttingLoading = ref(false)
/** いずれかの日付で反映済となった management_code の集合（同一コードが別日でも「反映済」表示するため） */
const reflectedManagementCodesSet = ref<Set<string>>(new Set())

async function loadReflectedManagementCodes() {
  try {
    const res = await request.get<{ success?: boolean; management_codes?: string[] }>(
      '/api/material/usage/reflected-management-codes',
      { params: { source: 'cutting_management' } }
    )
    const list = (res as any)?.management_codes ?? []
    reflectedManagementCodesSet.value = new Set(list.map((c: string) => String(c).trim()).filter(Boolean))
  } catch {
    reflectedManagementCodesSet.value = new Set()
  }
}

/** 行が「反映済」と表示すべきか（当該日の反映済 or 別日で既に反映済の管理コード） */
function isUsageRowReflected(row: CuttingManagementRow): boolean {
  if (row.material_usage_reflected === '反映済') return true
  const code = row.management_code != null ? String(row.management_code).trim() : ''
  return code !== '' && reflectedManagementCodesSet.value.has(code)
}

/** 使用材料数（材料別）- 今日：反映対象（use_material_stock_sub=0）のみで合计・反映済・未反映。サブ行は除外 */
const usageSummaryTodayCounts = computed(() => {
  const list = usageSummaryCuttingList.value
  const reflectTargetList = list.filter((row: CuttingManagementRow) => (row as { use_material_stock_sub?: number }).use_material_stock_sub !== 1)
  const total = reflectTargetList.length
  const reflected = reflectTargetList.filter(row => isUsageRowReflected(row)).length
  return { total, reflected, notReflected: total - reflected }
})

async function loadUsageSummaryCuttingList() {
  const dayStr = normalizeDateStr(usageSummaryDateToday.value)
  if (!dayStr) return
  usageSummaryCuttingLoading.value = true
  try {
    await loadReflectedManagementCodes()
    const res = await request.get<{ success?: boolean; data?: CuttingManagementRow[] }>(
      '/api/plan/cutting-management/list',
      { params: { production_day: dayStr, limit: 2000 } }
    )
    usageSummaryCuttingList.value = (res as any)?.success ? ((res as any).data ?? []) as CuttingManagementRow[] : []
  } catch {
    usageSummaryCuttingList.value = []
  } finally {
    usageSummaryCuttingLoading.value = false
    fetchUsageReflectedStatus()
  }
}

function shiftUsageSummaryDateToday(delta: number) {
  usageSummaryDateToday.value = shiftDate(usageSummaryDateToday.value, delta)
  loadUsageSummaryCuttingList()
}

watch(usageSummaryDateToday, loadUsageSummaryCuttingList, { immediate: true })

// ─────────────────────────────────────────────
// 使用材料数（材料別）- 翌日：独立した日付筛选
// ─────────────────────────────────────────────
const usageSummaryDateTomorrow = ref(getTomorrowString())
const usageSummaryCuttingListTomorrow = ref<CuttingManagementRow[]>([])
const usageSummaryCuttingLoadingTomorrow = ref(false)

async function loadUsageSummaryCuttingListTomorrow() {
  const dayStr = normalizeDateStr(usageSummaryDateTomorrow.value)
  if (!dayStr) return
  usageSummaryCuttingLoadingTomorrow.value = true
  try {
    await loadReflectedManagementCodes()
    const res = await request.get<{ success?: boolean; data?: CuttingManagementRow[] }>(
      '/api/plan/cutting-management/list',
      { params: { production_day: dayStr, limit: 2000 } }
    )
    usageSummaryCuttingListTomorrow.value = (res as any)?.success ? ((res as any).data ?? []) as CuttingManagementRow[] : []
  } catch {
    usageSummaryCuttingListTomorrow.value = []
  } finally {
    usageSummaryCuttingLoadingTomorrow.value = false
    fetchUsageReflectedStatus()
  }
}

function shiftUsageSummaryDateTomorrow(delta: number) {
  usageSummaryDateTomorrow.value = shiftDate(usageSummaryDateTomorrow.value, delta)
  loadUsageSummaryCuttingListTomorrow()
}

watch(usageSummaryDateTomorrow, loadUsageSummaryCuttingListTomorrow, { immediate: true })

/** 使用材料数（材料別）一覧の在庫区分スイッチ変更時：cutting_management.use_material_stock_sub を更新 */
async function onChangeUsageSummaryStock(row: CuttingManagementRow, val: number | boolean | string) {
  const id = (row as { id?: number }).id
  if (id == null) return
  const newVal = val === 1 || val === true ? 1 : 0
  try {
    await request.patch(`/api/plan/cutting-management/${id}`, { use_material_stock_sub: newVal })
    ;(row as { use_material_stock_sub?: number }).use_material_stock_sub = newVal
    // サマリの合計値・反映対象件数にも影響するため、最新状態を再取得
    await loadUsageSummaryCuttingList()
  } catch (e) {
    console.error('在庫区分の更新に失敗:', e)
    ElMessage.error('在庫区分の更新に失敗しました')
  }
}

/** 翌日の使用材料数（材料別・今日にない管理コードのみ） */
const cuttingTomorrowUsageSummary = computed<UsageSummary>(() => {
  const todayCodes = new Set(
    cuttingManagementList.value
      .map(r => r.management_code)
      .filter((c): c is string => !!c)
  )
  const filtered = cuttingManagementListTomorrow.value.filter(
    r => !!r.management_code && !todayCodes.has(r.management_code!)
  )
  return buildUsageSummaryByMaterial(filtered)
})

// ─────────────────────────────────────────────
// 指定日：使用材料数
// ─────────────────────────────────────────────
const specifiedDateDialogVisible = ref(false)
const specifiedDate = ref('')
const specifiedDateLoading = ref(false)
const specifiedDateRows = ref<CuttingManagementRow[]>([])

const specifiedDateUsageSummary = computed<UsageSummary>(() =>
  buildUsageSummaryByMaterial(specifiedDateRows.value)
)

/** 指定日材料数：原材料で昇順ソートした表示用（ダイアログ・印刷共通） */
const specifiedDateUsageSummarySorted = computed(() => {
  const s = specifiedDateUsageSummary.value
  const byMaterial = [...(s.byMaterial || [])].sort((a, b) =>
    (a.materialName || '').localeCompare(b.materialName || '', 'ja')
  )
  return { ...s, byMaterial }
})

function openSpecifiedDateDialog() {
  specifiedDateDialogVisible.value = true
  if (!specifiedDate.value) specifiedDate.value = getTodayString()
  loadSpecifiedDateUsage()
}

function shiftSpecifiedDate(delta: number) {
  specifiedDate.value = shiftDate(specifiedDate.value || getTodayString(), delta)
  loadSpecifiedDateUsage()
}

function setSpecifiedDateToday() {
  specifiedDate.value = getTodayString()
  loadSpecifiedDateUsage()
}

/** 指定日材料数窗体を印刷 */
function printSpecifiedDateUsage() {
  const dateStr = specifiedDate.value || ''
  const summary = specifiedDateUsageSummarySorted.value
  const rows = summary.byMaterial || []
  const total = summary.totalCount ?? 0

  const rowsHtml = rows
    .map(
      (r) =>
        `<tr><td style="text-align:center;padding:5px 10px;border:1px solid #ddd">${escapeHtml(r.materialName)}</td><td style="text-align:center;padding:5px 10px;border:1px solid #ddd">${r.usageCount}</td></tr>`
    )
    .join('')

  const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>指定日 — 所需材料数</title><style>
    body { font-family: sans-serif; padding: 10px; margin: 0; }
    h2 { margin: 0 0 4px; font-size: 17px; }
    .print-date { color: #666; margin-bottom: 6px; font-size: 13px; }
    table { border-collapse: collapse; width: 100%; max-width: 400px; margin: 0 auto; }
    th { background: #f5f5f5; padding: 6px 10px; border: 1px solid #ddd; text-align: center; font-size: 13px; }
    td { font-size: 13px; }
    .print-total { margin-top: 6px; font-weight: 700; text-align: center; font-size: 13px; }
  </style></head><body>
    <h2>指定日 — 所需材料数</h2>
    <div class="print-date">${escapeHtml(dateStr)} の使用材料数（材料別）</div>
    <table>
      <thead><tr><th>原材料</th><th>使用数（管理コード数）</th></tr></thead>
      <tbody>${rowsHtml}</tbody>
    </table>
    <div class="print-total">合計：${total} 束</div>
  </body></html>`

  const w = window.open('', '_blank')
  if (!w) {
    ElMessage.warning('弹窗被拦截，请允许弹窗后重试')
    return
  }
  w.document.write(html)
  w.document.close()
  w.focus()
  setTimeout(() => {
    w.print()
    w.close()
  }, 250)
}

async function loadSpecifiedDateUsage() {
  if (!specifiedDate.value) return
  specifiedDateLoading.value = true
  try {
    const res = await request.get<{ success?: boolean; data?: CuttingManagementRow[] }>(
      '/api/plan/cutting-management/list',
      { params: { production_day: specifiedDate.value, limit: 2000 } }
    )
    specifiedDateRows.value = (res as any)?.success ? ((res as any).data ?? []) as CuttingManagementRow[] : []
  } catch (e) {
    specifiedDateRows.value = []
    ElMessage.error('指定日データの取得に失敗しました')
  } finally {
    specifiedDateLoading.value = false
  }
}

// ─────────────────────────────────────────────
// 使用数反映：確認ダイアログ → コミット（表の日付で反映）
// ─────────────────────────────────────────────
const usageReflectionLoading = ref(false)
/** 使用材料数（材料別）- 今日・翌日の反映済みバッジ用 */
const usageReflectedToday = ref<boolean | null>(null)
const usageReflectedTomorrow = ref<boolean | null>(null)

/** 使用材料数（材料別）- 今日・翌日の反映済みバッジ用（今日は usageSummaryDateToday、翌日は usageSummaryDateTomorrow） */
async function fetchUsageReflectedStatus() {
  const todayStr = normalizeDateStr(usageSummaryDateToday.value)
  const tomorrowStr = normalizeDateStr(usageSummaryDateTomorrow.value)
  if (!todayStr) {
    usageReflectedToday.value = null
    usageReflectedTomorrow.value = null
    return
  }
  try {
    const [todayRes, tomorrowRes] = await Promise.all([
      request.get<{ success?: boolean; reflected?: boolean }>('/api/material/usage/reflected', {
        params: { date: todayStr, source: 'cutting_management' },
      }),
      tomorrowStr
        ? request.get<{ success?: boolean; reflected?: boolean }>('/api/material/usage/reflected', {
            params: { date: tomorrowStr, source: 'cutting_management' },
          })
        : Promise.resolve({ reflected: false }),
    ])
    usageReflectedToday.value = (todayRes as any)?.reflected ?? false
    usageReflectedTomorrow.value = tomorrowStr ? ((tomorrowRes as any)?.reflected ?? false) : null
  } catch {
    usageReflectedToday.value = null
    usageReflectedTomorrow.value = null
  }
}

function normalizeDateStr(val: unknown): string {
  if (val == null) return ''
  if (typeof val === 'string') {
    const s = val.trim()
    const match = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
    if (match) return `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`
    return s.slice(0, 10)
  }
  if (typeof (val as Date).getFullYear === 'function') {
    const d = val as Date
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${y}-${m}-${day}`
  }
  return String(val).trim().slice(0, 10)
}

/** 使用数反映：確認ダイアログのみ表示し、OKで表の日付データを反映 */
async function confirmUsageReflection() {
  const todayParam = normalizeDateStr(usageSummaryDateToday.value)
  if (!todayParam) {
    ElMessage.warning('使用材料数（材料別）- 今日の日付を選択してください')
    return
  }
  if (usageSummaryTodayCounts.value.total === 0) {
    ElMessage.warning('反映対象のデータがありません（使用サブ在庫の行は対象外）。指定日に切断指示があるか確認してください。')
    return
  }
  try {
    await ElMessageBox.confirm(
      `使用材料数（材料別）- 表示中の ${todayParam} のデータを材料在庫に反映します。反映済の管理コードは反映しません。よろしいですか？`,
      '使用数反映の確認',
      {
        confirmButtonText: '反映する',
        cancelButtonText: 'キャンセル',
        type: 'warning',
      }
    )
  } catch {
    return
  }
  await commitUsageReflection()
}

async function commitUsageReflection() {
  const todayParam = normalizeDateStr(usageSummaryDateToday.value)
  const tomorrowParam = shiftDate(usageSummaryDateToday.value, 1)
  usageReflectionLoading.value = true
  try {
    const res = await request.post<{ success?: boolean; message?: string; inserted?: number; upserted?: number; stock_updated?: number }>(
      '/api/material/usage/commit',
      {
        today_date: todayParam,
        tomorrow_date: tomorrowParam,
        source: 'cutting_management',
      }
    )
    const isOk = (res as any)?.success === true
    const msg = (res as any)?.message ?? '使用数を反映しました'
    if (isOk) {
      ElMessage.success(msg)
    } else {
      ElMessage.warning(msg)
    }
    await fetchUsageReflectedStatus()
    await loadCuttingManagement()
    await loadUsageSummaryCuttingList()
  } catch (e) {
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '使用数反映に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    usageReflectionLoading.value = false
  }
}

/** ロット→切断にドロップ時：生産日・切断機を指定するダイアログ */
const moveToCuttingDialogVisible = ref(false)
const pendingBatchRow = ref<CuttingPlanRow | null>(null)
const moveToCuttingForm = reactive({ production_day: '', cutting_machine: '' })
const moveToCuttingSubmitting = ref(false)
/** 面取ロット→面取指示にドロップ時：生産日・面取機を指定するダイアログ */
const moveToChamferingDialogVisible = ref(false)
const pendingChamferingBatchRow = ref<ChamferingBatchRow | null>(null)
const moveToChamferingForm = reactive({ production_day: '', production_line: '', production_line_2: '' })
const moveToChamferingSubmitting = ref(false)
/** 切断指示：双击编辑弹窗 */
const cuttingEditDialogVisible = ref(false)
const editingCuttingId = ref<number | null>(null)
const cuttingEditForm = reactive({
  cutting_machine: '',
  actual_production_quantity: '' as string,
  defect_qty: '' as string,
  production_lot_size: null as number | null,
  lot_number: '',
  production_sequence: 1,
  remarks: '',
  use_material_stock_sub: 0 as number,
  usage_count: 1 as number,
})
const cuttingEditSubmitting = ref(false)
/** 面取指示：双击编辑弹窗 */
const chamferingEditDialogVisible = ref(false)
const editingChamferingId = ref<number | null>(null)
/** 面取指示編集：打开时的生産数基准，修改生産数时 不良数 = 基准 - 生産数 */
const chamferingEditBaselineQuantity = ref(0)
const chamferingEditForm = reactive({
  chamfering_machine: '',
  actual_production_quantity: '' as string,
  defect_qty: '' as string,
  production_lot_size: null as number | null,
  lot_number: '',
  production_sequence: 1,
  remarks: '',
})
const chamferingEditSubmitting = ref(false)
/** 面取指示 新規追加ダイアログ（chamfering_management 構造） */
const chamferingNewDialogVisible = ref(false)
const chamferingNewSubmitting = ref(false)
const chamferingNewForm = reactive({
  production_day: '',
  production_line: '',
  chamfering_machine: '',
  product_cd: '',
  product_name: '',
  actual_production_quantity: '' as string, // 普通文本框，提交时转为 number
  production_sequence: null as number | null,
  material_name: '',
  management_code: '', // 自动生成，watch 同步
})
/** 管理コード自动生成：YYMM + 製品CD + ライン下2桁 + 生産順2桁（不足补0） */
const chamferingManagementCodePreview = computed(() => {
  const day = (chamferingNewForm.production_day || '').toString().trim().slice(0, 10)
  const line = (chamferingNewForm.production_line || '').toString().trim()
  const productCd = (chamferingNewForm.product_cd || '').toString().trim()
  const seq = chamferingNewForm.production_sequence
  if (!day || day.length < 10) return ''
  const yy = day.slice(2, 4)
  const mm = day.slice(5, 7)
  const lineSuffix = line.slice(-2).padEnd(2, '0')
  const seqStr = String(seq ?? 1).padStart(2, '0')
  return `${yy}${mm}${productCd}${lineSuffix}${seqStr}`
})
watch(chamferingManagementCodePreview, (v) => { chamferingNewForm.management_code = v }, { immediate: true })
/** 生産日セル：双击でインライン編集（±1日ボタン + 日期选择） */
const editingProductionDayId = ref<number | null>(null)
const editingProductionDayValue = ref('')
/** 面取指示：生産日インライン編集用 */
const editingChamferingProductionDayId = ref<number | null>(null)
const editingChamferingProductionDayValue = ref('')
/** 完了切替 loading：当前正在请求的行 id，用于显示该行的 switch loading */
const cuttingCompletedLoading = ref<number>(0)
/** 面取指示 完了/カウント無 切替 loading */
const chamferingCompletedLoading = ref<number | null>(null)
const chamferingNoCountLoading = ref<number | null>(null)
/** 生産ロット双击编辑（面取ロット一覧から開く場合は editingChamferingPlanId を設定） */
const planEditDialogVisible = ref(false)
const editingPlanId = ref<number | null>(null)
const editingChamferingPlanId = ref<number | null>(null)
const planEditSubmitting = ref(false)
const planEditForm = reactive({
  production_month: '',
  production_line: '',
  priority_order: null as number | null,
  product_cd: '',
  product_name: '',
  planned_quantity: null as number | null,
  actual_production_quantity: null as number | null,
  start_date: '',
  end_date: '',
  production_lot_size: null as number | null,
  lot_number: '',
  is_cutting_instructed: 0 as number,
  has_chamfering_process: 0 as number,
  is_chamfering_instructed: 0 as number,
  has_sw_process: 0 as number,
  is_sw_instructed: 0 as number,
  management_code: '',
  take_count: null as number | null,
  cutting_length: null as number | null,
  chamfering_length: null as number | null,
  developed_length: null as number | null,
  scrap_length: null as number | null,
  material_name: '',
  material_manufacturer: '',
  standard_specification: '',
  use_material_stock_sub: 0 as number,
  usage_count: 1 as number,
})
/** データ管理ダイアログ（instruction_plans 全件＋筛选） */
const dataManagementDialogVisible = ref(false)
const dataManagementRawList = ref<CuttingPlanRow[]>([])
const dataManagementLoading = ref(false)
const dataManagementFilter = reactive({
  production_month: '',
  equipment: '',
  product_name: '',
})
/** ライン・製品名は raw から一覧を生成し、選択でクライアント側フィルタ */
const dataManagementLineOptions = computed(() => {
  const raw = dataManagementRawList.value
  const set = new Set<string>()
  raw.forEach((r) => {
    const v = (r.production_line ?? '').trim()
    if (v) set.add(v)
  })
  return Array.from(set).sort()
})
const dataManagementProductNameOptions = computed(() => {
  const raw = dataManagementRawList.value
  const set = new Set<string>()
  raw.forEach((r) => {
    const v = (r.product_name ?? '').trim()
    if (v) set.add(v)
  })
  return Array.from(set).sort()
})
const dataManagementList = computed(() => {
  const raw = dataManagementRawList.value
  const eq = dataManagementFilter.equipment
  const pn = dataManagementFilter.product_name
  if (!eq && !pn) return raw
  return raw.filter((r) => (!eq || (r.production_line ?? '') === eq) && (!pn || (r.product_name ?? '') === pn))
})
/** データ管理ページネーション（30件/ページ） */
const dataManagementPagination = reactive({ currentPage: 1, pageSize: 30 })
/** フィルタ後全件（合計表示用） */
const filteredDataManagementList = dataManagementList
/** 当ページ表示分 */
const paginatedDataManagementList = computed(() => {
  const start = (dataManagementPagination.currentPage - 1) * dataManagementPagination.pageSize
  return filteredDataManagementList.value.slice(start, start + dataManagementPagination.pageSize)
})

/** 切断済リスト（cutting_management） */
const cuttingDoneDialogVisible = ref(false)
const cuttingDoneLoading = ref(false)
const cuttingDoneRawList = ref<CuttingManagementRow[]>([])
const cuttingDoneFilter = reactive({
  period: [] as string[],
  product_name: '',
  only_completed: false,
})
const cuttingDonePagination = reactive({ currentPage: 1, pageSize: 50 })
const cuttingDoneProductNameOptions = computed(() => {
  const set = new Set<string>()
  cuttingDoneRawList.value.forEach((row) => {
    const name = (row.product_name ?? '').trim()
    if (name) set.add(name)
  })
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ja'))
})
const cuttingDoneListFiltered = computed(() => {
  const [startDay, endDay] = cuttingDoneFilter.period
  const productName = cuttingDoneFilter.product_name
  const onlyCompleted = cuttingDoneFilter.only_completed
  return cuttingDoneRawList.value.filter((row) => {
    const day = formatDateOnly(String(row.production_day ?? ''))
    if (startDay && day && day < startDay) return false
    if (endDay && day && day > endDay) return false
    if (startDay && !day) return false
    if (productName && (row.product_name ?? '') !== productName) return false
    if (onlyCompleted && !row.production_completed_check) return false
    return true
  })
})
const cuttingDoneListPaged = computed(() => {
  const start = (cuttingDonePagination.currentPage - 1) * cuttingDonePagination.pageSize
  return cuttingDoneListFiltered.value.slice(start, start + cuttingDonePagination.pageSize)
})
watch(
  () => [cuttingDoneFilter.period, cuttingDoneFilter.product_name, cuttingDoneFilter.only_completed],
  () => {
    cuttingDonePagination.currentPage = 1
  },
  { deep: true }
)

/** 新規追加ダイアログ（false＝量産品 / true＝試作品） */
const newRecordIsTrialMode = ref(false)
const newRecordDialogVisible = ref(false)
const newRecordSubmitting = ref(false)
const newRecordFormDefault = () => ({
  production_month: '',
  production_line: '',
  priority_order: null as number | null,
  product_cd: '',
  product_name: '',
  material_name: '',
  material_manufacturer: '',
  standard_specification: '',
  planned_quantity: null as number | null,
  production_lot_size: null as number | null,
  lot_number: '',
  actual_production_quantity: null as number | null,
  take_count: null as number | null,
  cutting_length: null as number | null,
  chamfering_length: null as number | null,
  developed_length: null as number | null,
  scrap_length: null as number | null,
  start_date: '',
  end_date: '',
  has_chamfering_process: 0 as number,
  has_sw_process: 0 as number,
  use_material_stock_sub: 0 as number,
  usage_count: 1 as number,
})
const newRecordForm = reactive(newRecordFormDefault())

/** 新規ロット追加：ライン（成型設備）オプション */
const newRecordLineOptions = ref<{ value: string; label: string }[]>([])
async function loadNewRecordLineOptions() {
  try {
    const result = await request.get<{ data?: { list?: { machine_name?: string }[] }; list?: { machine_name?: string }[] }>(
      '/api/master/machines',
      { params: { keyword: '成型', pageSize: 500 } }
    )
    const list = (result as any)?.data?.list ?? (result as any)?.list ?? []
    newRecordLineOptions.value = (list as { machine_name?: string }[])
      .filter((r) => r.machine_name && String(r.machine_name).includes('成型'))
      .map((r) => ({ value: String(r.machine_name), label: String(r.machine_name) }))
  } catch (e) {
    console.error('成型ライン取得失敗:', e)
    newRecordLineOptions.value = []
  }
}

/** 新規ロット追加：製品オプション
 * 試作追加（試作品）：product_type=試作品、且つ (製品CD末位が1 または 製品名に「加工」を含まない)
 * 新規追加（量産品）：product_type=量産品、且つ 製品CD末位が1 且つ 製品名に「加工」を含まない
 */
const newRecordProductOptions = ref<{ product_cd: string; product_name: string }[]>([])
async function loadNewRecordProductOptions() {
  const isTrial = newRecordIsTrialMode.value
  const productType = isTrial ? '試作品' : '量産品'
  try {
    const result = await request.get<{ data?: { list?: { product_cd?: string; product_name?: string }[] }; list?: { product_cd?: string; product_name?: string }[] }>(
      '/api/master/products',
      { params: { product_type: productType, pageSize: 10000 } }
    )
    const list = (result as any)?.data?.list ?? (result as any)?.list ?? []
    const raw = (list as { product_cd?: string; product_name?: string }[]) || []
    newRecordProductOptions.value = raw
      .filter((p) => {
        const cd = (p.product_cd ?? '').toString().trim()
        const name = (p.product_name ?? '').toString()
        if (!cd) return false
        const lastChar1 = cd.slice(-1) === '1'
        const noKagyo = !name.includes('加工')
        if (isTrial) {
          return lastChar1 || noKagyo
        }
        return lastChar1 && noKagyo
      })
      .map((p) => ({ product_cd: String(p.product_cd ?? ''), product_name: (p.product_name ?? p.product_cd ?? '').toString() }))
      .sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '', 'ja'))
  } catch (e) {
    console.error('製品一覧取得失敗:', e)
    newRecordProductOptions.value = []
  }
}

/** 製品選択時：batch-detail API で原材料・規格・取数・寸法・面取/SW工程を自動入力 */
async function onNewRecordProductChange(productCd: string) {
  if (!productCd) {
    newRecordForm.product_name = ''
    newRecordForm.material_name = ''
    newRecordForm.standard_specification = ''
    newRecordForm.material_manufacturer = ''
    newRecordForm.take_count = null
    newRecordForm.cutting_length = null
    newRecordForm.chamfering_length = null
    newRecordForm.developed_length = null
    newRecordForm.scrap_length = null
    newRecordForm.has_chamfering_process = 0
    newRecordForm.has_sw_process = 0
    return
  }
  const opt = newRecordProductOptions.value.find((p) => p.product_cd === productCd)
  if (opt) newRecordForm.product_name = opt.product_name
  try {
    const res = await request.get<{ success?: boolean; data?: Record<string, unknown> }>(
      `/api/master/products/batch-detail/${encodeURIComponent(productCd)}`
    )
    const data = (res as any)?.data
    if (data) {
      newRecordForm.material_name = (data.material_name ?? '') as string
      newRecordForm.standard_specification = (data.standard_specification ?? '') as string
      newRecordForm.material_manufacturer = (data.material_manufacturer ?? '') as string
      newRecordForm.take_count = (data.take_count ?? null) as number | null
      newRecordForm.cutting_length = (data.cutting_length ?? null) as number | null
      newRecordForm.chamfering_length = (data.chamfering_length ?? null) as number | null
      newRecordForm.developed_length = (data.developed_length ?? null) as number | null
      newRecordForm.scrap_length = (data.scrap_length ?? null) as number | null
      newRecordForm.has_chamfering_process = (data.has_chamfering_process === true ? 1 : 0) as number
      newRecordForm.has_sw_process = (data.has_sw_process === true ? 1 : 0) as number
    }
  } catch (e) {
    console.error('製品詳細取得失敗:', e)
  }
}

function openNewRecordDialog(trialMode: boolean = false) {
  newRecordIsTrialMode.value = trialMode
  Object.assign(newRecordForm, newRecordFormDefault())
  loadNewRecordLineOptions()
  loadNewRecordProductOptions()
  newRecordDialogVisible.value = true
}

async function createDataManagementRecord() {
  const month = (newRecordForm.production_month ?? '').toString().trim()
  const productCd = (newRecordForm.product_cd ?? '').toString().trim()
  const productName = (newRecordForm.product_name ?? '').toString().trim()
  if (!month) {
    ElMessage.warning('生産月を選択してください')
    return
  }
  if (!productCd || !productName) {
    ElMessage.warning('製品名で製品を選択してください')
    return
  }
  newRecordSubmitting.value = true
  try {
    if (!newRecordForm.product_name && productCd) {
      const opt = newRecordProductOptions.value.find((p) => p.product_cd === productCd)
      if (opt) newRecordForm.product_name = opt.product_name
    }
    const payload: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(newRecordForm)) {
      if (v !== '' && v !== null && v !== undefined) payload[k] = v
    }
    const result = await request.post<{ success?: boolean; message?: string }>(
      '/api/plan/batch/create',
      payload
    )
    if ((result as any)?.success) {
      ElMessage.success('レコードを追加しました')
      newRecordDialogVisible.value = false
      loadPlans()
      loadDataManagementList()
    } else {
      throw new Error((result as any)?.message ?? '追加に失敗しました')
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string | unknown[] } }; message?: string }
    const detail = err.response?.data?.detail
    let msg: string
    if (typeof detail === 'string') msg = detail
    else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string } | unknown
      msg = (first && typeof first === 'object' && 'msg' in first ? (first as { msg: string }).msg : String(first))
    } else msg = err.message ?? '追加に失敗しました'
    ElMessage.error(msg)
  } finally {
    newRecordSubmitting.value = false
  }
}

/** 編集中セル: { rowId, prop } */
const dataManagementEditingCell = ref<{ rowId: number; prop: string } | null>(null)
const dataManagementSavingCell = ref(false)
/** 拖拽放置区：ロット一覧（左）、切断指示、面取ロット一覧、面取指示 */
const dragOverZone = ref<'batchList' | 'cuttingManagement' | 'chamferingBatchList' | 'chamferingManagement' | null>(null)
/** 当前拖拽来源：仅用于控制是否显示放置提示 */
const dragSourceRef = ref<'batchList' | 'cuttingManagement' | 'chamferingBatch' | 'chamferingManagement' | null>(null)

/** 面取指示（chamfering_management） */
interface ChamferingManagementRow {
  id?: number
  cutting_management_id?: number | null
  production_month?: string | null
  production_day?: string | null
  production_line?: string | null
  chamfering_machine?: string | null
  production_order?: number | null
  production_sequence?: number | null
  product_cd?: string | null
  product_name?: string | null
  actual_production_quantity?: number | null
  defect_qty?: number | null
  production_lot_size?: number | null
  lot_number?: string | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  production_time?: number | null
  material_name?: string | null
  management_code?: string | null
  has_sw_process?: number | null
  production_completed_check?: number | null
  no_count?: number | null
  remarks?: string | null
  cd?: string | null
  created_at?: string | null
}
const chamferingManagementList = ref<ChamferingManagementRow[]>([])
const chamferingManagementListToday = ref<ChamferingManagementRow[]>([])
const chamferingManagementListTomorrow = ref<ChamferingManagementRow[]>([])
const chamferingManagementLoading = ref(false)
const selectedChamferingDateToday = ref(getTodayString())
const selectedChamferingMachineFilter = ref<string>('')
const selectedChamferingDateTomorrow = ref(getTomorrowString())

/** 面取ロット一覧（chamfering_plans）：切断登録時・面取工程ありで自動登録された待機データ */
interface ChamferingBatchRow {
  id?: number
  cutting_management_id?: number | null
  production_month?: string | null
  production_day?: string | null
  production_line?: string | null
  production_order?: number | null
  product_cd?: string | null
  product_name?: string | null
  actual_production_quantity?: number | null
  production_lot_size?: number | null
  lot_number?: string | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  material_name?: string | null
  management_code?: string | null
  cd?: string | null
  has_sw_process?: number | null
  created_at?: string | null
}
const chamferingBatchList = ref<ChamferingBatchRow[]>([])
const chamferingBatchLoading = ref(false)
const chamferingBatchActionLoading = ref<number | null>(null)
const chamferingSwLoading = ref<number | null>(null)

/** 面取ロット一覧：製品名昇順 → CD 昇順でソートした表示用 */
const chamferingBatchListSorted = computed(() =>
  [...chamferingBatchList.value].sort((a, b) => {
    const cmpName = (a.product_name || '').localeCompare(b.product_name || '', 'ja')
    if (cmpName !== 0) return cmpName
    const cdA = (a.cd ?? (a.management_code ? String(a.management_code).slice(-5) : '') ?? '').toString()
    const cdB = (b.cd ?? (b.management_code ? String(b.management_code).slice(-5) : '') ?? '').toString()
    return cdA.localeCompare(cdB, 'ja')
  })
)

/** 面取ロット一覧：新規追加ダイアログ */
const chamferingPlanNewDialogVisible = ref(false)
const chamferingPlanNewSubmitting = ref(false)
const chamferingPlanNewForm = reactive({
  production_month: '',
  production_day: '',
  production_line: '',
  production_order: null as number | null,
  product_cd: '',
  product_name: '',
  actual_production_quantity: 0,
  production_lot_size: null as number | null,
  lot_number: '',
  chamfering_length: null as number | null,
  material_name: '',
  has_sw_process: 0 as number,
})

/** カンバン発行（kanban_issuance）：切断現品票に必要な全フィールド */
interface KanbanIssuanceRow {
  id?: number
  process_type?: string | null
  source_id?: number | null
  kanban_no?: string | null
  issue_date?: string | null
  status?: string | null
  created_at?: string | null
  product_cd?: string | null
  product_name?: string | null
  production_line?: string | null
  cutting_machine?: string | null
  material_name?: string | null
  standard_specification?: string | null
  management_code?: string | null
  start_date?: string | null
  end_date?: string | null
  planned_quantity?: number | null
  production_lot_size?: number | null
  actual_production_quantity?: number | null
  take_count?: number | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  has_chamfering_process?: boolean | null
  lot_number?: string | null
  production_day?: string | null
}
const kanbanIssuanceList = ref<KanbanIssuanceRow[]>([])
const kanbanIssuanceLoading = ref(false)
const kanbanIssuePendingLoading = ref<number | null>(null)
const kanbanReissueLoading = ref<number | null>(null)
/** カンバン発行筛选：生産日・状態・製品名 */
const kanbanFilterProductionDay = ref<string>(getTodayString())
const kanbanFilterStatus = ref<string>('pending')
const kanbanFilterProductName = ref<string>('')
const kanbanIssuanceProductNameOptions = ref<string[]>([])
const kanbanIssuanceSelection = ref<KanbanIssuanceRow[]>([])
/** カンバン発行：分页（默认每页30件） */
const kanbanPage = ref(1)
const kanbanPageSize = ref(30)
/** カンバン発行：全ページ一括選択フラグ（ヘッダチェックボックスで制御） */
const kanbanSelectAllAllPages = ref(false)
const kanbanIssuanceListPaged = computed(() => {
  const list = kanbanIssuanceList.value
  const size = kanbanPageSize.value
  const start = (kanbanPage.value - 1) * size
  return list.slice(start, start + size)
})
const kanbanBatchIssueLoading = ref(false)
const kanbanSyncProductionDayLoading = ref(false)
/** カンバン発行：双击编辑弹窗 */
const kanbanEditDialogVisible = ref(false)
const kanbanEditRow = ref<KanbanIssuanceRow | null>(null)
const kanbanEditSubmitting = ref(false)
const kanbanEditForm = reactive<{
  product_cd: string
  product_name: string
  production_line: string
  cutting_machine: string
  material_name: string
  standard_specification: string
  management_code: string
  start_date: string
  end_date: string
  planned_quantity: number | null
  production_lot_size: number | null
  actual_production_quantity: number | null
  take_count: number | null
  cutting_length: number | null
  chamfering_length: number | null
  developed_length: number | null
  has_chamfering_process: boolean
  lot_number: string
  production_day: string
}>({
  product_cd: '',
  product_name: '',
  production_line: '',
  cutting_machine: '',
  material_name: '',
  standard_specification: '',
  management_code: '',
  start_date: '',
  end_date: '',
  planned_quantity: null,
  production_lot_size: null,
  actual_production_quantity: null,
  take_count: null,
  cutting_length: null,
  chamfering_length: null,
  developed_length: null,
  has_chamfering_process: false,
  lot_number: '',
  production_day: '',
})
const dragEnterCount = ref(0)
const DRAG_PLAN_KEY = 'cutting-plan-row'

/** 右侧上：製品情報（products 表・material_name は API で materials 結合） */
interface ProductDetail {
  product_cd?: string
  product_name?: string
  lot_size?: number | null
  material_cd?: string | null
  material_name?: string | null
  cut_length?: number | null
  chamfer_length?: number | null
  developed_length?: number | null
  scrap_length?: number | null
  take_count?: number | null
}
const selectedProductCd = ref<string | null>(null)
const productDetail = ref<ProductDetail | null>(null)
const productDetailLoading = ref(false)

/** 右侧下：設備能率（equipment_efficiency 表） */
interface EquipmentEfficiencyRow {
  machines_name?: string | null
  efficiency_rate?: number | null
  product_cd?: string | null
}
const equipmentEfficiencyList = ref<EquipmentEfficiencyRow[]>([])
const equipmentEfficiencyLoading = ref(false)

/** 生産ロット一覧右：設備能率は設備名に「切断」を含む行のみ表示 */
const equipmentEfficiencyListFiltered = computed(() => {
  const list = equipmentEfficiencyList.value
  return list.filter((r) => {
    const name = (r.machines_name ?? '').toString().trim()
    return name && name.includes('切断')
  })
})

/** 面取ロット一覧用：右側製品情報・設備能率 */
const selectedChamferingProductCd = ref<string | null>(null)
const chamferingProductDetail = ref<ProductDetail | null>(null)
const chamferingProductDetailLoading = ref(false)
const chamferingEquipmentEfficiencyList = ref<EquipmentEfficiencyRow[]>([])
const chamferingEquipmentEfficiencyLoading = ref(false)

/** 面取ロット一覧右：設備能率は設備名に「面取」を含む行のみ表示 */
const chamferingEquipmentEfficiencyListFiltered = computed(() => {
  const list = chamferingEquipmentEfficiencyList.value
  return list.filter((r) => {
    const name = (r.machines_name ?? '').toString().trim()
    return name && name.includes('面取')
  })
})

/** 拖拽中不触发点击 */
const isDragging = ref(false)

/** 生産ロット一覧：設備で取得した一覧を製品名・材料名でクライアント側フィルタ（データ管理と同様に完全一致） */
const planProductNameOptions = computed(() => {
  const set = new Set<string>()
  plans.value.forEach((r) => {
    const v = (r.product_name ?? '').trim()
    if (v) set.add(v)
  })
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ja'))
})
const planMaterialNameOptions = computed(() => {
  const set = new Set<string>()
  plans.value.forEach((r) => {
    const v = (r.material_name ?? '').trim()
    if (v) set.add(v)
  })
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ja'))
})
const planListFiltered = computed(() => {
  const raw = plans.value
  const pn = (planSearchForm.product_name ?? '').trim()
  const mn = (planSearchForm.material_name ?? '').trim()
  if (!pn && !mn) return raw
  return raw.filter(
    (r) =>
      (!pn || (r.product_name ?? '').trim() === pn) &&
      (!mn || (r.material_name ?? '').trim() === mn)
  )
})
/** 生産ロット一覧のクライアント側ページネーション用 */
const planListForTable = computed(() => {
  const list = planListFiltered.value
  const start = (planPagination.currentPage - 1) * planPagination.pageSize
  return list.slice(start, start + planPagination.pageSize)
})

watch(
  () => planListFiltered.value.length,
  (len) => {
    const ps = planPagination.pageSize
    const maxPage = Math.max(1, Math.ceil(len / ps) || 1)
    if (planPagination.currentPage > maxPage) planPagination.currentPage = maxPage
  }
)

function onPlanEquipmentChange() {
  planSearchForm.product_name = ''
  planSearchForm.material_name = ''
  loadPlans()
}

function onPlanProductOrMaterialFilterChange() {
  planPagination.currentPage = 1
}

// 生産月：自动生成当月前后3个月（共7个月），value 格式 YYYY-MM
const scheduleMonths = ref<{ value: string; label: string }[]>([])
const syncLengthsFromProductsLoading = ref(false)

/** 設備下拉：machines 表の machine_name で「成型」を含むもの */
const machineOptions = ref<{ machine_name: string }[]>([])

const loadMachineOptions = async () => {
  try {
    const result = await request.get<{ data?: { list?: { machine_name?: string }[] }; list?: { machine_name?: string }[] }>(
      '/api/master/machines',
      { params: { keyword: '成型', pageSize: 500 } }
    )
    const list = (result as any)?.data?.list ?? (result as any)?.list ?? []
    machineOptions.value = (list as { machine_name?: string }[])
      .filter((r) => r.machine_name && String(r.machine_name).includes('成型'))
      .map((r) => ({ machine_name: String(r.machine_name) }))
  } catch (error) {
    console.error('設備データの読み込みに失敗:', error)
    machineOptions.value = []
  }
}

/** 切断機オプション：machines の machine_name で「切断」を含むもの */
const loadCuttingMachineOptions = async () => {
  try {
    const result = await request.get<{ data?: { list?: { machine_name?: string }[] }; list?: { machine_name?: string }[] }>(
      '/api/master/machines',
      { params: { keyword: '切断', pageSize: 500 } }
    )
    const list = (result as any)?.data?.list ?? (result as any)?.list ?? []
    cuttingMachineOptions.value = (list as { machine_name?: string }[])
      .filter((r) => r.machine_name && String(r.machine_name).includes('切断'))
      .map((r) => ({ machine_name: String(r.machine_name) }))
  } catch (error) {
    console.error('切断機データの読み込みに失敗:', error)
    cuttingMachineOptions.value = []
  }
}

/** 面取機オプション：machines の machine_name で「面取」を含むもの */
const chamferingMachineOptions = ref<{ machine_name: string }[]>([])
const loadChamferingMachineOptions = async () => {
  try {
    const result = await request.get<{ data?: { list?: { machine_name?: string }[] }; list?: { machine_name?: string }[] }>(
      '/api/master/machines',
      { params: { keyword: '面取', pageSize: 500 } }
    )
    const list = (result as any)?.data?.list ?? (result as any)?.list ?? []
    chamferingMachineOptions.value = (list as { machine_name?: string }[])
      .filter((r) => r.machine_name && String(r.machine_name).includes('面取'))
      .map((r) => ({ machine_name: String(r.machine_name) }))
  } catch (error) {
    console.error('面取機データの読み込みに失敗:', error)
    chamferingMachineOptions.value = []
  }
}

/** 面取工程（KT02）製品一覧：新規追加ダイアログ用 */
const chamferingProductOptions = ref<{ product_cd: string; product_name: string }[]>([])
const loadChamferingProductOptions = async () => {
  try {
    const list = await request.get<{ product_cd: string; product_name: string }[]>(
      '/api/master/product/process/routes/products-by-process',
      { params: { process_cd: 'KT02' } }
    )
    chamferingProductOptions.value = Array.isArray(list)
      ? [...list].sort((a, b) => (a.product_name || '').localeCompare(b.product_name || '', 'ja'))
      : []
  } catch (error) {
    console.error('面取工程製品の読み込みに失敗:', error)
    chamferingProductOptions.value = []
  }
}

/** 原材料マスタ一覧：新規追加ダイアログ用 */
const chamferingMaterialOptions = ref<{ material_cd: string; material_name: string }[]>([])
const loadChamferingMaterialOptions = async () => {
  try {
    const result = await request.get<{ data?: { list?: { material_cd?: string; material_name?: string }[] }; list?: { material_cd?: string; material_name?: string }[] }>(
      '/api/master/materials',
      { params: { pageSize: 500 } }
    )
    const list = (result as any)?.data?.list ?? (result as any)?.list ?? []
    chamferingMaterialOptions.value = (list as { material_cd?: string; material_name?: string }[])
      .filter((r) => r.material_name != null)
      .map((r) => ({ material_cd: String(r.material_cd ?? ''), material_name: String(r.material_name ?? '') }))
  } catch (error) {
    console.error('原材料データの読み込みに失敗:', error)
    chamferingMaterialOptions.value = []
  }
}

const handlePlanSizeChange = (size: number) => {
  planPagination.pageSize = size
  planPagination.currentPage = 1
}

const handlePlanCurrentChange = (page: number) => {
  planPagination.currentPage = page
}

const loadScheduleMonths = () => {
  const now = new Date()
  const baseYear = now.getFullYear()
  const baseMonth = now.getMonth()
  scheduleMonths.value = Array.from({ length: 7 }, (_, i) => {
    const m = new Date(baseYear, baseMonth + (i - 3), 1)
    const year = m.getFullYear()
    const month = m.getMonth() + 1
    return {
      value: `${year}-${String(month).padStart(2, '0')}`,
      label: `${month}月`,
    }
  })
}

function getCurrentMonthYYYYMM(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

const syncLengthsFromProducts = async () => {
  try {
    await ElMessageBox.confirm(
      '製品マスタの切断長・面取長・展開長を、生産ロット（instruction_plans）・切断/面取関連テーブル・カンバン発行へ一括反映します。生産ロットについては製品工程ルートに基づき面取工程・SW工程フラグ（has_chamfering_process / has_sw_process）も更新します。よろしいですか？',
      '寸法マスタ同期',
      { confirmButtonText: '同期', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  syncLengthsFromProductsLoading.value = true
  try {
    const result = await request.post<{
      success?: boolean
      message?: string
      data?: Record<string, number>
    }>('/api/plan/batch/sync-lengths-from-products', {})
    if ((result as any)?.success) {
      ElMessage.success((result as any).message ?? '同期しました')
      loadPlans()
      loadCuttingManagement()
      loadChamferingBatchList()
      loadChamferingManagement()
      loadKanbanIssuance()
    } else {
      ElMessage.error((result as any)?.message ?? '同期に失敗しました')
    }
  } catch (e: unknown) {
    console.error('寸法マスタ同期に失敗:', e)
    const ax = e as { response?: { data?: { detail?: string } } }
    const detail = ax.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '同期に失敗しました')
  } finally {
    syncLengthsFromProductsLoading.value = false
  }
}

const loadPlans = async () => {
  planPagination.currentPage = 1
  planLoading.value = true
  try {
    const params: Record<string, string> = {}
    if (planSearchForm.equipment) params.equipment = planSearchForm.equipment
    const result = await request.get<{ success?: boolean; data?: CuttingPlanRow[]; message?: string }>(
      '/api/plan/batch/list',
      { params }
    )
    if ((result as any)?.success) {
      plans.value = ((result as any).data ?? []) as CuttingPlanRow[]
    } else {
      throw new Error((result as any)?.message ?? 'データの取得に失敗しました')
    }
  } catch (error) {
    console.error('計画リストの読み込みに失敗:', error)
    ElMessage.error('計画データの読み込みに失敗しました')
    plans.value = []
  } finally {
    planLoading.value = false
  }
}

function openDataManagementDialog() {
  resetDataManagementFilter()
  dataManagementDialogVisible.value = true
}

async function loadDataManagementList() {
  dataManagementLoading.value = true
  dataManagementEditingCell.value = null
  dataManagementPagination.currentPage = 1
  try {
    const params: Record<string, string | number> = { limit: 10000 }
    if (dataManagementFilter.production_month) params.production_month = dataManagementFilter.production_month
    const result = await request.get<{ success?: boolean; data?: CuttingPlanRow[]; message?: string }>(
      '/api/plan/batch/list',
      { params }
    )
    const list: CuttingPlanRow[] = (result as any)?.success ? ((result as any).data ?? []) : []
    dataManagementRawList.value = list
  } catch (e) {
    console.error('データ管理一覧の取得に失敗:', e)
    ElMessage.error('データの取得に失敗しました')
    dataManagementRawList.value = []
  } finally {
    dataManagementLoading.value = false
  }
}

function resetDataManagementFilter() {
  dataManagementFilter.production_month = ''
  dataManagementFilter.equipment = ''
  dataManagementFilter.product_name = ''
}

function openCuttingDoneDialog() {
  resetCuttingDoneFilter()
  cuttingDoneDialogVisible.value = true
}

function onCuttingDoneFilterChange() {
  cuttingDonePagination.currentPage = 1
}

function resetCuttingDoneFilter() {
  cuttingDoneFilter.period = []
  cuttingDoneFilter.product_name = ''
  cuttingDoneFilter.only_completed = false
  cuttingDonePagination.currentPage = 1
}

function getManagementCodeLast5(row: CuttingManagementRow): string {
  const raw = row.management_code != null ? String(row.management_code).trim() : ''
  if (!raw) return '-'
  return raw.slice(-5)
}

async function loadCuttingDoneList() {
  cuttingDoneLoading.value = true
  cuttingDonePagination.currentPage = 1
  try {
    const result = await request.get<{ success?: boolean; data?: CuttingManagementRow[] }>(
      '/api/plan/cutting-management/list',
      { params: { limit: 10000 } }
    )
    const list = (result as any)?.success ? ((result as any).data ?? []) as CuttingManagementRow[] : []
    cuttingDoneRawList.value = [...list].sort((a, b) => {
      const dayA = formatDateOnly(String(a.production_day ?? ''))
      const dayB = formatDateOnly(String(b.production_day ?? ''))
      if (dayA !== dayB) return dayB.localeCompare(dayA)
      const codeA = (a.management_code ?? '').toString().trim()
      const codeB = (b.management_code ?? '').toString().trim()
      return codeB.localeCompare(codeA, 'ja')
    })
  } catch (e) {
    console.error('切断済リストの取得に失敗:', e)
    ElMessage.error('切断済リストの取得に失敗しました')
    cuttingDoneRawList.value = []
  } finally {
    cuttingDoneLoading.value = false
  }
}

const chamferingDoneDialogVisible = ref(false)
const chamferingDoneLoading = ref(false)
const chamferingDoneRawList = ref<ChamferingManagementRow[]>([])
const chamferingDoneFilter = reactive({
  period: [] as string[],
  product_name: '',
  only_completed: false,
})
const chamferingDonePagination = reactive({ currentPage: 1, pageSize: 50 })
const chamferingDoneProductNameOptions = computed(() => {
  const set = new Set<string>()
  chamferingDoneRawList.value.forEach((row) => {
    const name = (row.product_name ?? '').trim()
    if (name) set.add(name)
  })
  return Array.from(set).sort((a, b) => a.localeCompare(b, 'ja'))
})
const chamferingDoneListFiltered = computed(() => {
  const [startDay, endDay] = chamferingDoneFilter.period
  const productName = chamferingDoneFilter.product_name
  const onlyCompleted = chamferingDoneFilter.only_completed
  return chamferingDoneRawList.value.filter((row) => {
    const day = formatDateOnly(String(row.production_day ?? ''))
    if (startDay && day && day < startDay) return false
    if (endDay && day && day > endDay) return false
    if (startDay && !day) return false
    if (productName && (row.product_name ?? '') !== productName) return false
    if (onlyCompleted && !row.production_completed_check) return false
    return true
  })
})
const chamferingDoneListPaged = computed(() => {
  const start = (chamferingDonePagination.currentPage - 1) * chamferingDonePagination.pageSize
  return chamferingDoneListFiltered.value.slice(start, start + chamferingDonePagination.pageSize)
})
watch(
  () => [chamferingDoneFilter.period, chamferingDoneFilter.product_name, chamferingDoneFilter.only_completed],
  () => {
    chamferingDonePagination.currentPage = 1
  },
  { deep: true }
)

function openChamferingDoneDialog() {
  resetChamferingDoneFilter()
  chamferingDoneDialogVisible.value = true
}

function onChamferingDoneFilterChange() {
  chamferingDonePagination.currentPage = 1
}

function resetChamferingDoneFilter() {
  chamferingDoneFilter.period = []
  chamferingDoneFilter.product_name = ''
  chamferingDoneFilter.only_completed = false
  chamferingDonePagination.currentPage = 1
}

function getManagementCodeLast5Chamfering(row: ChamferingManagementRow): string {
  const raw = row.management_code != null ? String(row.management_code).trim() : ''
  if (!raw) return '-'
  return raw.slice(-5)
}

async function loadChamferingDoneList() {
  chamferingDoneLoading.value = true
  chamferingDonePagination.currentPage = 1
  try {
    const result = await request.get<{ success?: boolean; data?: ChamferingManagementRow[] }>(
      '/api/plan/chamfering-management/list',
      { params: { limit: 10000 } }
    )
    const list = (result as any)?.success ? ((result as any).data ?? []) as ChamferingManagementRow[] : []
    chamferingDoneRawList.value = [...list].sort((a, b) => {
      const dayA = formatDateOnly(String(a.production_day ?? ''))
      const dayB = formatDateOnly(String(b.production_day ?? ''))
      if (dayA !== dayB) return dayB.localeCompare(dayA)
      const codeA = (a.management_code ?? '').toString().trim()
      const codeB = (b.management_code ?? '').toString().trim()
      return codeB.localeCompare(codeA, 'ja')
    })
  } catch (e) {
    console.error('面取済リストの取得に失敗:', e)
    ElMessage.error('面取済リストの取得に失敗しました')
    chamferingDoneRawList.value = []
  } finally {
    chamferingDoneLoading.value = false
  }
}

function isEditingDataCell(row: CuttingPlanRow, prop: string) {
  const c = dataManagementEditingCell.value
  return c && row.id !== undefined && c.rowId === row.id && c.prop === prop
}

function startEditDataCell(row: CuttingPlanRow, prop: string) {
  if (row.id == null || dataManagementSavingCell.value) return
  dataManagementEditingCell.value = { rowId: row.id, prop }
}

async function saveDataManagementCell(row: CuttingPlanRow, prop: string, value: unknown) {
  if (row.id == null) return
  dataManagementEditingCell.value = null
  dataManagementSavingCell.value = true
  try {
    const payload: Record<string, unknown> = {}
    if (prop === 'production_month' || prop === 'start_date' || prop === 'end_date') {
      payload[prop] = value != null && String(value).trim() !== '' ? String(value).slice(0, 10) : null
    } else if (['priority_order', 'planned_quantity', 'actual_production_quantity', 'production_lot_size', 'take_count', 'is_cutting_instructed', 'has_chamfering_process', 'is_chamfering_instructed', 'has_sw_process', 'is_sw_instructed'].includes(prop)) {
      payload[prop] = value === '' || value == null ? null : Number(value)
    } else if (['cutting_length', 'chamfering_length', 'developed_length', 'scrap_length'].includes(prop)) {
      payload[prop] = value === '' || value == null ? null : Number(value)
    } else {
      payload[prop] = value == null ? null : String(value).trim() || null
    }
    await request.patch(`/api/plan/batch/${row.id}`, payload)
    ;(row as Record<string, unknown>)[prop] = value
    ElMessage.success('更新しました')
  } catch (e) {
    console.error('セル更新に失敗:', e)
    ElMessage.error('更新に失敗しました')
  } finally {
    dataManagementSavingCell.value = false
  }
}

function onPlanCardClick(row: CuttingPlanRow) {
  if (isDragging.value) return
  const cd = row.product_cd ?? null
  if (!cd) return
  selectedProductCd.value = cd
  loadProductDetail(cd)
  loadEquipmentEfficiency(cd)
}

/** 生産ロット1件を複製（同内容で新規1件追加） */
async function copyPlanBatch(row: CuttingPlanRow) {
  const productionMonthRaw = row.production_month ? String(row.production_month) : ''
  const productionMonth = productionMonthRaw ? productionMonthRaw.slice(0, 7) : ''
  const productCd = (row.product_cd ?? '').toString().trim()
  const productName = (row.product_name ?? '').toString().trim()
  if (!productionMonth || !productCd || !productName) {
    ElMessage.error('複製元のデータが不足しているため複製できません')
    return
  }
  const id = row.id ?? null
  planBatchActionLoading.value = id
  try {
    const payload: Record<string, unknown> = {
      production_month: productionMonth,
      production_line: row.production_line ?? '',
      priority_order: row.priority_order ?? 0,
      product_cd: productCd,
      product_name: productName,
      material_name: row.material_name ?? '',
      material_manufacturer: row.material_manufacturer ?? '',
      standard_specification: row.standard_specification ?? '',
      planned_quantity: row.planned_quantity ?? 0,
      production_lot_size: row.production_lot_size ?? null,
      lot_number: row.lot_number ?? '',
      actual_production_quantity: row.actual_production_quantity ?? 0,
      take_count: row.take_count ?? null,
      cutting_length: row.cutting_length ?? null,
      chamfering_length: row.chamfering_length ?? null,
      developed_length: row.developed_length ?? null,
      scrap_length: row.scrap_length ?? null,
      start_date: row.start_date ? String(row.start_date).slice(0, 10) : '',
      end_date: row.end_date ? String(row.end_date).slice(0, 10) : '',
      has_chamfering_process: row.has_chamfering_process ?? 0,
      has_sw_process: row.has_sw_process ?? 0,
      use_material_stock_sub: (row as { use_material_stock_sub?: number }).use_material_stock_sub === 1 ? 1 : 0,
      usage_count: (row as { usage_count?: number }).usage_count != null ? Number((row as { usage_count?: number }).usage_count) : 1,
    }
    const result = await request.post<{ success?: boolean; message?: string }>(
      '/api/plan/batch/create',
      payload
    )
    if ((result as any)?.success) {
      ElMessage.success('複製しました')
      loadPlans()
    } else {
      throw new Error((result as any)?.message ?? '複製に失敗しました')
    }
  } catch (e: unknown) {
    const err = e as { response?: { data?: { detail?: string | unknown[] } }; message?: string }
    const detail = err.response?.data?.detail
    let msg: string
    if (typeof detail === 'string') msg = detail
    else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string } | unknown
      msg = (first && typeof first === 'object' && 'msg' in first ? (first as { msg: string }).msg : String(first))
    } else msg = err.message ?? '複製に失敗しました'
    ElMessage.error(msg)
  } finally {
    planBatchActionLoading.value = null
  }
}

/** 生産ロット1件を削除（確認ダイアログ後） */
async function deletePlanBatch(row: CuttingPlanRow) {
  const id = row.id
  if (id == null) return
  try {
    await ElMessageBox.confirm(
      `このロット（製品: ${row.product_name ?? row.product_cd ?? ''}）を削除しますか？`,
      '削除の確認',
      { confirmButtonText: '削除', cancelButtonText: 'キャンセル', type: 'warning' }
    )
  } catch {
    return
  }
  planBatchActionLoading.value = id
  try {
    await request.delete(`/api/plan/batch/${id}`)
    ElMessage.success('削除しました')
    loadPlans()
  } catch (e) {
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '削除に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    planBatchActionLoading.value = null
  }
}

/** 生産ロット一覧：材料使用数セルをダブルクリックして編集 */
async function onDblClickUsageCount(row: CuttingPlanRow) {
  const current = formatUsageCountDisplay(row as { usage_count?: number | null })
  try {
    const { value } = await ElMessageBox.prompt('材料使用数を入力してください（小数1桁まで）', '材料使用数の編集', {
      inputValue: current,
      inputPattern: /^(?:\d+)(?:\.\d)?$/,
      inputErrorMessage: '0.0以上の数値（小数1桁まで）を入力してください',
      confirmButtonText: '保存',
      cancelButtonText: 'キャンセル',
    })
    const num = Number(value)
    if (isNaN(num) || num <= 0) {
      ElMessage.error('0より大きい数値を入力してください')
      return
    }
    await saveDataManagementCell(row, 'usage_count', num)
  } catch {
    // キャンセル時などは何もしない
  }
}

/** 使用材料数（材料別）：材料使用数セルをダブルクリックして編集（cutting_management.usage_count を更新） */
async function onDblClickUsageSummaryUsageCount(row: CuttingManagementRow) {
  const id = (row as { id?: number }).id
  if (id == null) return
  const current = formatUsageCountDisplay(row as { usage_count?: number | null })
  try {
    const { value } = await ElMessageBox.prompt('材料使用数を入力してください（小数1桁まで）', '材料使用数の編集', {
      inputValue: current,
      inputPattern: /^(?:\d+)(?:\.\d)?$/,
      inputErrorMessage: '0.0以上の数値（小数1桁まで）を入力してください',
      confirmButtonText: '保存',
      cancelButtonText: 'キャンセル',
    })
    const num = Number(value)
    if (isNaN(num) || num <= 0) {
      ElMessage.error('0より大きい数値を入力してください')
      return
    }
    await request.patch(`/api/plan/cutting-management/${id}`, { usage_count: num })
    ;(row as { usage_count?: number | null }).usage_count = num
    await loadUsageSummaryCuttingList()
  } catch {
    // キャンセル等は無視
  }
}

async function loadProductDetail(productCd: string) {
  productDetail.value = null
  productDetailLoading.value = true
  try {
    const result = await request.get<{ success?: boolean; data?: { list?: ProductDetail[] }; message?: string }>(
      '/api/master/products',
      { params: { product_cd: productCd, page: 1, pageSize: 1 } }
    )
    if ((result as any)?.success && (result as any)?.data?.list?.length) {
      productDetail.value = (result as any).data.list[0] as ProductDetail
    }
  } catch (e) {
    console.error('製品詳細の取得に失敗:', e)
    ElMessage.error('製品データの取得に失敗しました')
  } finally {
    productDetailLoading.value = false
  }
}

async function loadEquipmentEfficiency(productCd: string) {
  equipmentEfficiencyList.value = []
  equipmentEfficiencyLoading.value = true
  try {
    const result = await request.get<{
      success?: boolean
      data?: { list?: EquipmentEfficiencyRow[] }
      list?: EquipmentEfficiencyRow[]
    }>('/api/master/equipment-efficiency', { params: { keyword: productCd, limit: 9999 } })
    const list = ((result as any)?.data?.list ?? (result as any)?.list ?? []) as EquipmentEfficiencyRow[]
    equipmentEfficiencyList.value = list.filter((r) => r.product_cd === productCd)
  } catch (e) {
    console.error('設備能率の取得に失敗:', e)
    ElMessage.error('設備能率データの取得に失敗しました')
  } finally {
    equipmentEfficiencyLoading.value = false
  }
}

function onChamferingBatchRowClick(row: ChamferingBatchRow) {
  if (isDragging.value) return
  const cd = (row.product_cd ?? '').toString().trim() || null
  if (!cd) return
  selectedChamferingProductCd.value = cd
  loadChamferingProductDetail(cd)
  loadChamferingEquipmentEfficiency(cd)
}

async function loadChamferingProductDetail(productCd: string) {
  chamferingProductDetail.value = null
  chamferingProductDetailLoading.value = true
  try {
    const result = await request.get<{ success?: boolean; data?: { list?: ProductDetail[] }; message?: string }>(
      '/api/master/products',
      { params: { product_cd: productCd, page: 1, pageSize: 1 } }
    )
    if ((result as any)?.success && (result as any)?.data?.list?.length) {
      chamferingProductDetail.value = (result as any).data.list[0] as ProductDetail
    }
  } catch (e) {
    console.error('面取ロット用・製品詳細の取得に失敗:', e)
    ElMessage.error('製品データの取得に失敗しました')
  } finally {
    chamferingProductDetailLoading.value = false
  }
}

async function loadChamferingEquipmentEfficiency(productCd: string) {
  chamferingEquipmentEfficiencyList.value = []
  chamferingEquipmentEfficiencyLoading.value = true
  try {
    const result = await request.get<{
      success?: boolean
      data?: { list?: EquipmentEfficiencyRow[] }
      list?: EquipmentEfficiencyRow[]
    }>('/api/master/equipment-efficiency', { params: { keyword: productCd, limit: 9999 } })
    const list = ((result as any)?.data?.list ?? (result as any)?.list ?? []) as EquipmentEfficiencyRow[]
    chamferingEquipmentEfficiencyList.value = list.filter((r) => r.product_cd === productCd)
  } catch (e) {
    console.error('面取ロット用・設備能率の取得に失敗:', e)
    ElMessage.error('設備能率データの取得に失敗しました')
  } finally {
    chamferingEquipmentEfficiencyLoading.value = false
  }
}

function onPlanCardDragStart(e: DragEvent, row: CuttingPlanRow) {
  isDragging.value = true
  dragSourceRef.value = 'batchList'
  if (!e.dataTransfer) return
  e.dataTransfer.effectAllowed = 'copy'
  e.dataTransfer.setData('application/json', JSON.stringify(row))
  e.dataTransfer.setData(DRAG_PLAN_KEY, String(row.id ?? ''))
}

function onPlanCardDragEnd() {
  isDragging.value = false
  dragSourceRef.value = null
  dragEnterCount.value = 0
  dragOverZone.value = null
}

function onDragOver(e: DragEvent, zone?: 'batchList' | 'cuttingManagement') {
  e.preventDefault()
  if (e.dataTransfer) {
    e.dataTransfer.dropEffect = zone === 'batchList' ? 'move' : 'copy'
  }
}

function onDragEnter(zone: 'batchList' | 'cuttingManagement') {
  dragEnterCount.value += 1
  // 切断指示内拖拽排序时不显示「ロットを切断指示へ移行」提示；仅从ロット拖入时显示
  if (zone === 'cuttingManagement' && dragSourceRef.value === 'cuttingManagement') return
  if (zone === 'batchList' && dragSourceRef.value === 'batchList') return
  dragOverZone.value = zone
}

function onDragLeave(_zone: 'batchList' | 'cuttingManagement') {
  dragEnterCount.value = Math.max(0, dragEnterCount.value - 1)
  if (dragEnterCount.value === 0) dragOverZone.value = null
}

function onDragOverChamfering(e: DragEvent, _zone: 'chamferingBatchList' | 'chamferingManagement') {
  e.preventDefault()
  e.stopPropagation()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

function onDragEnterChamfering(zone: 'chamferingBatchList' | 'chamferingManagement') {
  dragEnterCount.value += 1
  if (zone === 'chamferingBatchList' && dragSourceRef.value === 'chamferingManagement') dragOverZone.value = zone
  else if (zone === 'chamferingManagement' && dragSourceRef.value === 'chamferingBatch') dragOverZone.value = zone
}

function onDragLeaveChamfering(_zone: 'chamferingBatchList' | 'chamferingManagement') {
  dragEnterCount.value = Math.max(0, dragEnterCount.value - 1)
  if (dragEnterCount.value === 0) dragOverZone.value = null
}

function onChamferingBatchDragStart(e: DragEvent, row: ChamferingBatchRow) {
  if (isDragging.value) return
  isDragging.value = true
  dragSourceRef.value = 'chamferingBatch'
  if (!e.dataTransfer) return
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('application/json', JSON.stringify({ source: 'chamferingBatch', row }))
}

function onChamferingManagementDragStart(e: DragEvent, row: ChamferingManagementRow) {
  if (isDragging.value) return
  isDragging.value = true
  dragSourceRef.value = 'chamferingManagement'
  if (!e.dataTransfer) return
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('application/json', JSON.stringify({ source: 'chamferingManagement', row }))
}

function onChamferingDragEnd() {
  isDragging.value = false
  dragSourceRef.value = null
  dragEnterCount.value = 0
  dragOverZone.value = null
}

/** 面取指示行を別の行にドロップして同一面取機・同一生産日内で並び替え */
async function onDropChamferingRowForReorder(e: DragEvent, targetRow: ChamferingManagementRow) {
  e.preventDefault()
  e.stopPropagation()
  let payload: { source?: string; row?: ChamferingManagementRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw)
  } catch {
    return
  }
  if (payload?.source !== 'chamferingManagement' || !payload?.row) return
  const dragged = payload.row as ChamferingManagementRow
  if (!dragged.id || !targetRow.id || dragged.id === targetRow.id) return
  const cm = (dragged.chamfering_machine || '').trim()
  if (!cm) {
    ElMessage.warning('同一面取機内で並び替えてください')
    return
  }
  const dayStr = String(targetRow.production_day ?? '').slice(0, 10)
  const isToday = dayStr === selectedChamferingDateToday.value
  const list = isToday ? chamferingManagementListToday.value : chamferingManagementListTomorrow.value
  const productionDay = isToday ? selectedChamferingDateToday.value : selectedChamferingDateTomorrow.value
  const sameMachine = list.filter((r) => (r.chamfering_machine || '').trim() === cm)
  const fromIdx = sameMachine.findIndex((r) => r.id === dragged.id)
  const toIdx = sameMachine.findIndex((r) => r.id === targetRow.id)
  if (fromIdx === -1 || toIdx === -1) return
  const reordered = [...sameMachine]
  reordered.splice(fromIdx, 1)
  reordered.splice(toIdx, 0, dragged)
  const orderedIds = reordered.map((r) => r.id!).filter((id) => id != null)
  try {
    await request.post('/api/plan/chamfering-management/reorder', {
      chamfering_machine: cm,
      production_day: productionDay?.slice(0, 10) ?? dayStr,
      ordered_ids: orderedIds,
    })
    ElMessage.success('生産順を更新しました')
    loadChamferingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '並び替えに失敗しました'
    ElMessage.error(String(msg))
  }
}

function onDragoverChamferingRow(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

/** 面取指示：表頭前/表尾後のドロップで先頭または末尾へ移動 */
async function onDropChamferingRowToEdge(
  e: DragEvent,
  position: 'first' | 'last',
  context: 'today' | 'tomorrow'
) {
  e.preventDefault()
  e.stopPropagation()
  let payload: { source?: string; row?: ChamferingManagementRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw)
  } catch {
    return
  }
  if (payload?.source !== 'chamferingManagement' || !payload?.row) return
  const dragged = payload.row as ChamferingManagementRow
  if (!dragged.id) return
  const cm = (dragged.chamfering_machine || '').trim()
  if (!cm) {
    ElMessage.warning('同一面取機内で並び替えてください')
    return
  }
  const list = context === 'today' ? chamferingManagementListToday.value : chamferingManagementListTomorrow.value
  const productionDay = context === 'today' ? selectedChamferingDateToday.value : selectedChamferingDateTomorrow.value
  const sameMachine = list.filter((r) => (r.chamfering_machine || '').trim() === cm)
  const fromIdx = sameMachine.findIndex((r) => r.id === dragged.id)
  if (fromIdx === -1) return
  const rest = sameMachine.filter((r) => r.id !== dragged.id).map((r) => r.id!).filter((id) => id != null)
  const orderedIds = position === 'first' ? [dragged.id!, ...rest] : [...rest, dragged.id!]
  try {
    await request.post('/api/plan/chamfering-management/reorder', {
      chamfering_machine: cm,
      production_day: productionDay?.slice(0, 10) ?? '',
      ordered_ids: orderedIds,
    })
    ElMessage.success('生産順を更新しました')
    loadChamferingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '並び替えに失敗しました'
    ElMessage.error(String(msg))
  }
}

async function onDropChamferingManagement(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
  dragEnterCount.value = 0
  dragOverZone.value = null
  let payload: { source?: string; row?: ChamferingBatchRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw) as { source?: string; row?: ChamferingBatchRow }
  } catch {
    return
  }
  if (payload.source !== 'chamferingBatch' || !payload.row?.id) return
  const row = payload.row
  moveToChamferingForm.production_day = (selectedChamferingDateToday.value ? String(selectedChamferingDateToday.value).slice(0, 10) : '') || getTodayString()
  const opts = chamferingMachineOptions.value
  const selectedInToday = (selectedChamferingMachineFilter.value || '').trim()
  const defaultMachine = opts.some((m) => m.machine_name === selectedInToday) ? selectedInToday : (opts[0]?.machine_name ?? '')
  const firstChamfering = opts[0]?.machine_name ?? ''
  const secondChamfering = opts[1]?.machine_name ?? firstChamfering
  const rowLine = (row.production_line ?? '').trim()
  moveToChamferingForm.production_line = defaultMachine || (opts.some((m) => m.machine_name === rowLine) ? rowLine : firstChamfering)
  moveToChamferingForm.production_line_2 = row.has_sw_process ? (opts.some((m) => m.machine_name === rowLine) ? secondChamfering : (opts[1] ? opts[1].machine_name : firstChamfering)) : ''
  pendingChamferingBatchRow.value = row
  moveToChamferingDialogVisible.value = true
  onChamferingDragEnd()
}

async function submitMoveToChamfering() {
  const row = pendingChamferingBatchRow.value
  if (!row?.id) return
  const productionDay = moveToChamferingForm.production_day?.trim()
  if (!productionDay || productionDay.length < 10) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  const productionLine = moveToChamferingForm.production_line?.trim()
  if (!productionLine) {
    ElMessage.warning('面取機を選択してください')
    return
  }
  const isSw = !!row.has_sw_process
  if (isSw) {
    const productionLine2 = moveToChamferingForm.production_line_2?.trim()
    if (!productionLine2) {
      ElMessage.warning('面取機（SW）を選択してください')
      return
    }
  }
  moveToChamferingSubmitting.value = true
  try {
    const body: { chamfering_plan_id: number; production_day: string; production_line: string; production_line_2?: string } = {
      chamfering_plan_id: row.id,
      production_day: productionDay.slice(0, 10),
      production_line: productionLine,
    }
    if (isSw) body.production_line_2 = moveToChamferingForm.production_line_2?.trim() ?? ''
    await request.post('/api/plan/chamfering-plans/move-to-chamfering', body)
    ElMessage.success(isSw ? '面取指示を2件登録しました' : '面取指示に登録しました')
    moveToChamferingDialogVisible.value = false
    pendingChamferingBatchRow.value = null
    loadChamferingBatchList()
    loadChamferingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '面取指示への移行に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    moveToChamferingSubmitting.value = false
  }
}

async function onDropChamferingBatchList(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
  dragEnterCount.value = 0
  dragOverZone.value = null
  let payload: { source?: string; row?: ChamferingManagementRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw) as { source?: string; row?: ChamferingManagementRow }
  } catch {
    return
  }
  if (payload.source !== 'chamferingManagement' || !payload.row?.id) return
  const id = payload.row.id
  try {
    await request.post('/api/plan/chamfering-plans/move-from-chamfering', { chamfering_management_id: id })
    ElMessage.success('面取ロット一覧に戻しました')
    loadChamferingBatchList()
    loadChamferingManagement()
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '面取ロットへの戻しに失敗しました'
    ElMessage.error(String(msg))
  } finally {
    onChamferingDragEnd()
  }
}

async function onDropBatchList(e: DragEvent) {
  e.preventDefault()
  dragEnterCount.value = 0
  dragOverZone.value = null
  let payload: { source?: string; row?: CuttingManagementRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw) as { source?: string; row?: CuttingManagementRow }
  } catch {
    return
  }
  if (payload.source !== 'cuttingManagement' || !payload.row) return
  const row = payload.row
  const cuttingId = row.id
  if (cuttingId == null) {
    ElMessage.warning('このデータはロットに戻せません（IDがありません）')
    return
  }
  const productionMonth = String(row.production_month ?? '').slice(0, 7)
  if (!productionMonth || productionMonth.length < 7) {
    ElMessage.warning('生産月が不正です')
    return
  }
  try {
    await request.post('/api/plan/batch/move-from-cutting', {
      cutting_id: cuttingId,
      production_month: productionMonth,
      production_line: row.production_line ?? '',
      product_cd: row.product_cd ?? '',
      product_name: row.product_name ?? '',
      actual_production_quantity: row.actual_production_quantity ?? 0,
      material_name: row.material_name ?? null,
      management_code: row.management_code ?? null,
      production_day: row.production_day ? formatDateOnly(String(row.production_day)) : null,
      production_order: row.priority_order ?? null,
    })
    ElMessage.success('生産ロットに戻しました（切断・面取・カンバンを削除済み）')
    loadPlans()
    loadCuttingManagement()
    loadChamferingManagement()
    loadChamferingBatchList()
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? 'ロットへの戻しに失敗しました'
    ElMessage.error(String(msg))
  }
}

async function onDropCuttingManagement(e: DragEvent) {
  e.preventDefault()
  dragEnterCount.value = 0
  dragOverZone.value = null
  let payload: CuttingPlanRow | { source?: string; row?: CuttingManagementRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw) as CuttingPlanRow | { source?: string; row?: CuttingManagementRow }
  } catch {
    return
  }
  if (typeof payload === 'object' && payload !== null && 'source' in payload && payload.source === 'cuttingManagement') {
    return
  }
  const row = payload as CuttingPlanRow
  const planId = row.id
  if (planId == null) {
    ElMessage.warning('このロットは移行できません（IDがありません）')
    return
  }
  const productionMonth = String(row.production_month ?? '').slice(0, 7)
  if (!productionMonth || productionMonth.length < 7) {
    ElMessage.warning('生産月が不正です')
    return
  }
  moveToCuttingForm.production_day = (selectedDateToday.value ? String(selectedDateToday.value).slice(0, 10) : '') || getTodayString()
  const selectedInToday = (cuttingMachineFilter.value || '').trim()
  const opts = cuttingMachineOptionsFiltered.value
  const defaultMachine = opts.some((m) => m.machine_name === selectedInToday)
    ? selectedInToday
    : (opts[0]?.machine_name ?? '')
  moveToCuttingForm.cutting_machine = defaultMachine
  pendingBatchRow.value = row
  moveToCuttingDialogVisible.value = true
}

async function submitMoveToCutting() {
  const row = pendingBatchRow.value
  if (!row) return
  if (!moveToCuttingForm.cutting_machine?.trim()) {
    ElMessage.warning('切断機を選択してください')
    return
  }
  const productionDay = moveToCuttingForm.production_day?.trim()
  if (!productionDay || productionDay.length < 10) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  moveToCuttingSubmitting.value = true
  try {
    await request.post('/api/plan/cutting-management/move-from-batch', {
      plan_id: row.id,
      production_month: String(row.production_month ?? '').slice(0, 7),
      production_line: row.production_line ?? '',
      product_cd: row.product_cd ?? '',
      product_name: row.product_name ?? '',
      actual_production_quantity: row.actual_production_quantity ?? 0,
      material_name: row.material_name ?? null,
      management_code: row.management_code ?? null,
      production_day: productionDay.slice(0, 10),
      priority_order: row.priority_order ?? null,
      cutting_machine: moveToCuttingForm.cutting_machine.trim(),
      has_chamfering_process: !!(row.has_chamfering_process ?? 0),
    })
    moveToCuttingDialogVisible.value = false
    pendingBatchRow.value = null
    loadPlans()
    await loadCuttingManagement()
    loadChamferingManagement()
    loadChamferingBatchList()
    loadKanbanIssuance()
    const cm = moveToCuttingForm.cutting_machine.trim()
    const dayStr = productionDay.slice(0, 10)
    const isToday = dayStr === (selectedDateToday.value ? String(selectedDateToday.value).slice(0, 10) : '')
    const isTomorrow = dayStr === (selectedDateTomorrow.value ? String(selectedDateTomorrow.value).slice(0, 10) : '')
    const list = isToday ? cuttingManagementList.value : isTomorrow ? cuttingManagementListTomorrow.value : []
    const sameMachine = list.filter((r) => (r.cutting_machine || '').trim() === cm)
    if (sameMachine.length > 0) {
      const sorted = [...sameMachine].sort((a, b) => {
        const sa = (a.production_sequence ?? 0)
        const sb = (b.production_sequence ?? 0)
        if (sa !== sb) return sa - sb
        return (a.id ?? 0) - (b.id ?? 0)
      })
      const orderedIds = sorted.map((r) => r.id!).filter((id) => id != null)
      if (orderedIds.length > 0) {
        await request.post('/api/plan/cutting-management/reorder', { cutting_machine: cm, ordered_ids: orderedIds })
        await loadCuttingManagement()
      }
    }
    ElMessage.success('切断指示に登録しました（面取工程ありの場合は面取指示・カンバン待発行も登録）')
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '移行に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    moveToCuttingSubmitting.value = false
  }
}

function openPlanEditDialog(row: CuttingPlanRow) {
  if (isDragging.value || row.id == null) return
  editingChamferingPlanId.value = null
  editingPlanId.value = row.id
  planEditForm.production_month = row.production_month ? formatDateOnly(String(row.production_month)) : ''
  planEditForm.production_line = row.production_line ?? ''
  planEditForm.priority_order = row.priority_order ?? null
  planEditForm.product_cd = row.product_cd ?? ''
  planEditForm.product_name = row.product_name ?? ''
  planEditForm.planned_quantity = row.planned_quantity ?? null
  planEditForm.actual_production_quantity = row.actual_production_quantity ?? null
  planEditForm.start_date = row.start_date ? formatDateOnly(String(row.start_date)) : ''
  planEditForm.end_date = row.end_date ? formatDateOnly(String(row.end_date)) : ''
  planEditForm.production_lot_size = row.production_lot_size ?? null
  planEditForm.lot_number = row.lot_number != null ? String(row.lot_number) : (row.production_lot_size != null ? String(row.production_lot_size) : '')
  planEditForm.is_cutting_instructed = row.is_cutting_instructed ? 1 : 0
  planEditForm.has_chamfering_process = row.has_chamfering_process ? 1 : 0
  planEditForm.is_chamfering_instructed = row.is_chamfering_instructed ? 1 : 0
  planEditForm.has_sw_process = row.has_sw_process ? 1 : 0
  planEditForm.is_sw_instructed = row.is_sw_instructed ? 1 : 0
  planEditForm.management_code = row.management_code ?? ''
  planEditForm.take_count = row.take_count ?? null
  planEditForm.cutting_length = row.cutting_length != null ? Number(row.cutting_length) : null
  planEditForm.chamfering_length = row.chamfering_length != null ? Number(row.chamfering_length) : null
  planEditForm.developed_length = row.developed_length != null ? Number(row.developed_length) : null
  planEditForm.scrap_length = row.scrap_length != null ? Number(row.scrap_length) : null
  planEditForm.material_name = row.material_name ?? ''
  planEditForm.material_manufacturer = row.material_manufacturer ?? ''
  planEditForm.standard_specification = row.standard_specification ?? ''
  planEditForm.use_material_stock_sub = (row as { use_material_stock_sub?: number }).use_material_stock_sub === 1 ? 1 : 0
  const planUsage = (row as { usage_count?: number }).usage_count
  planEditForm.usage_count = planUsage != null && Number(planUsage) > 0 ? Number(planUsage) : 1
  planEditDialogVisible.value = true
}

/** 面取ロット一覧：双击でロット内容編集ダイアログを開く（同窗体で編集・保存は chamfering-plans API） */
function openChamferingPlanEditDialog(row: ChamferingBatchRow) {
  if (isDragging.value || row.id == null) return
  editingPlanId.value = null
  editingChamferingPlanId.value = row.id
  planEditForm.production_month = row.production_month ? formatDateOnly(String(row.production_month)) : ''
  planEditForm.production_line = row.production_line ?? ''
  planEditForm.priority_order = row.production_order ?? null
  planEditForm.product_cd = row.product_cd ?? ''
  planEditForm.product_name = row.product_name ?? ''
  planEditForm.planned_quantity = null
  planEditForm.actual_production_quantity = row.actual_production_quantity ?? null
  planEditForm.start_date = row.production_day ? formatDateOnly(String(row.production_day)) : ''
  planEditForm.end_date = ''
  planEditForm.production_lot_size = row.production_lot_size ?? null
  planEditForm.lot_number = row.lot_number != null ? String(row.lot_number) : ''
  planEditForm.is_cutting_instructed = 0
  planEditForm.has_chamfering_process = 1
  planEditForm.is_chamfering_instructed = 0
  planEditForm.has_sw_process = row.has_sw_process ? 1 : 0
  planEditForm.is_sw_instructed = 0
  planEditForm.management_code = row.management_code ?? ''
  planEditForm.take_count = null
  planEditForm.cutting_length = null
  planEditForm.chamfering_length = row.chamfering_length != null ? Number(row.chamfering_length) : null
  planEditForm.developed_length = null
  planEditForm.scrap_length = null
  planEditForm.material_name = row.material_name ?? ''
  planEditForm.material_manufacturer = ''
  planEditForm.standard_specification = ''
  planEditDialogVisible.value = true
}

async function savePlanEdit() {
  const chamferingId = editingChamferingPlanId.value
  if (chamferingId != null) {
    planEditSubmitting.value = true
    try {
      await request.put(`/api/plan/chamfering-plans/${chamferingId}/content`, {
        production_month: planEditForm.production_month || null,
        production_day: planEditForm.start_date || null,
        production_line: planEditForm.production_line || null,
        production_order: planEditForm.priority_order,
        product_cd: planEditForm.product_cd || null,
        product_name: planEditForm.product_name || null,
        actual_production_quantity: planEditForm.actual_production_quantity,
        production_lot_size: planEditForm.production_lot_size,
        lot_number: planEditForm.lot_number || null,
        chamfering_length: planEditForm.chamfering_length,
        material_name: planEditForm.material_name || null,
        has_sw_process: !!planEditForm.has_sw_process,
      })
      ElMessage.success('保存しました')
      planEditDialogVisible.value = false
      editingChamferingPlanId.value = null
      loadChamferingBatchList()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
        ?? (err as { message?: string })?.message
        ?? '保存に失敗しました'
      ElMessage.error(String(msg))
    } finally {
      planEditSubmitting.value = false
    }
    return
  }
  const id = editingPlanId.value
  if (id == null) return
  planEditSubmitting.value = true
  try {
    await request.patch(`/api/plan/batch/${id}`, {
      production_month: planEditForm.production_month || null,
      production_line: planEditForm.production_line || null,
      priority_order: planEditForm.priority_order,
      product_cd: planEditForm.product_cd || null,
      product_name: planEditForm.product_name || null,
      planned_quantity: planEditForm.planned_quantity,
      actual_production_quantity: planEditForm.actual_production_quantity,
      start_date: planEditForm.start_date || null,
      end_date: planEditForm.end_date || null,
      production_lot_size: planEditForm.production_lot_size,
      lot_number: planEditForm.lot_number || null,
      is_cutting_instructed: planEditForm.is_cutting_instructed,
      has_chamfering_process: planEditForm.has_chamfering_process,
      is_chamfering_instructed: planEditForm.is_chamfering_instructed,
      has_sw_process: planEditForm.has_sw_process,
      is_sw_instructed: planEditForm.is_sw_instructed,
      // management_code は instruction_plans のトリガーで自動生成・更新のため送信しない
      take_count: planEditForm.take_count,
      cutting_length: planEditForm.cutting_length,
      chamfering_length: planEditForm.chamfering_length,
      developed_length: planEditForm.developed_length,
      scrap_length: planEditForm.scrap_length,
      material_name: planEditForm.material_name || null,
      material_manufacturer: planEditForm.material_manufacturer || null,
      standard_specification: planEditForm.standard_specification || null,
      use_material_stock_sub: planEditForm.use_material_stock_sub,
      usage_count: planEditForm.usage_count,
    })
    ElMessage.success('保存しました')
    planEditDialogVisible.value = false
    editingPlanId.value = null
    loadPlans()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '保存に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    planEditSubmitting.value = false
  }
}

function onCuttingCardDragStart(e: DragEvent, row: CuttingManagementRow) {
  isDragging.value = true
  dragSourceRef.value = 'cuttingManagement'
  if (!e.dataTransfer) return
  e.dataTransfer.effectAllowed = 'move'
  e.dataTransfer.setData('application/json', JSON.stringify({ source: 'cuttingManagement', row }))
}

function onCuttingCardDragEnd() {
  isDragging.value = false
  dragSourceRef.value = null
  dragEnterCount.value = 0
  dragOverZone.value = null
}

/** 切断指示行を別の行にドロップして同一切断機内で並び替え（生産順更新） */
async function onDropCuttingRowForReorder(e: DragEvent, targetRow: CuttingManagementRow) {
  e.preventDefault()
  e.stopPropagation()
  let payload: { source?: string; row?: CuttingManagementRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw)
  } catch {
    return
  }
  if (payload?.source !== 'cuttingManagement' || !payload?.row) return
  const dragged = payload.row as CuttingManagementRow
  if (!dragged.id || !targetRow.id || dragged.id === targetRow.id) return
  const cm = (cuttingMachineFilter.value || dragged.cutting_machine || '').trim()
  if (!cm) {
    ElMessage.warning('切断機でフィルタを指定するか、同一切断機内で並び替えてください')
    return
  }
  const dayStr = String(targetRow.production_day ?? '').slice(0, 10)
  const isToday = dayStr === selectedDateToday.value
  const list = isToday ? cuttingManagementList.value : cuttingManagementListTomorrow.value
  const sameMachine = list.filter((r) => (r.cutting_machine || '').trim() === cm)
  const fromIdx = sameMachine.findIndex((r) => r.id === dragged.id)
  const toIdx = sameMachine.findIndex((r) => r.id === targetRow.id)
  if (fromIdx === -1 || toIdx === -1) return
  const reordered = [...sameMachine]
  reordered.splice(fromIdx, 1)
  reordered.splice(toIdx, 0, dragged)
  const orderedIds = reordered.map((r) => r.id!).filter((id) => id != null)
  try {
    await request.post('/api/plan/cutting-management/reorder', { cutting_machine: cm, ordered_ids: orderedIds })
    ElMessage.success('生産順を更新しました')
    loadCuttingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '並び替えに失敗しました'
    ElMessage.error(String(msg))
  }
}

/** 行上 dragover 时允许放置并显示 move 光标，确保表内拖拽排序可触发 drop */
function onDragoverCuttingRow(e: DragEvent) {
  e.preventDefault()
  e.stopPropagation()
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

/** 拖到表头前/表尾后的放置区：移动到第一位或最后一位 */
async function onDropCuttingRowToEdge(
  e: DragEvent,
  position: 'first' | 'last',
  context: 'today' | 'tomorrow'
) {
  e.preventDefault()
  e.stopPropagation()
  let payload: { source?: string; row?: CuttingManagementRow }
  try {
    const raw = e.dataTransfer?.getData('application/json')
    if (!raw) return
    payload = JSON.parse(raw)
  } catch {
    return
  }
  if (payload?.source !== 'cuttingManagement' || !payload?.row) return
  const dragged = payload.row as CuttingManagementRow
  if (!dragged.id) return
  const cm = (cuttingMachineFilter.value || dragged.cutting_machine || '').trim()
  if (!cm) {
    ElMessage.warning('切断機でフィルタを指定するか、同一切断機内で並び替えてください')
    return
  }
  const list = context === 'today' ? cuttingManagementList.value : cuttingManagementListTomorrow.value
  const sameMachine = list.filter((r) => (r.cutting_machine || '').trim() === cm)
  const fromIdx = sameMachine.findIndex((r) => r.id === dragged.id)
  if (fromIdx === -1) return
  const rest = sameMachine.filter((r) => r.id !== dragged.id).map((r) => r.id!).filter((id) => id != null)
  const orderedIds = position === 'first' ? [dragged.id!, ...rest] : [...rest, dragged.id!]
  try {
    await request.post('/api/plan/cutting-management/reorder', { cutting_machine: cm, ordered_ids: orderedIds })
    ElMessage.success('生産順を更新しました')
    loadCuttingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '並び替えに失敗しました'
    ElMessage.error(String(msg))
  }
}

/** 完了切替：切换后自动 PATCH 更新 */
async function toggleCuttingCompleted(row: CuttingManagementRow) {
  const id = row.id
  if (id == null) return
  const next = !row.production_completed_check
  cuttingCompletedLoading.value = id
  try {
    await request.patch(`/api/plan/cutting-management/${id}`, { production_completed_check: next })
    row.production_completed_check = next ? 1 : 0
    ElMessage.success(next ? '完了にしました' : '未完了に戻しました')
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '更新に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    cuttingCompletedLoading.value = 0
  }
}

/** 面取指示 完了切替 */
async function toggleChamferingCompleted(row: ChamferingManagementRow) {
  const id = row.id
  if (id == null) return
  const next = !row.production_completed_check
  chamferingCompletedLoading.value = id
  try {
    await request.patch(`/api/plan/chamfering-management/${id}`, { production_completed_check: !!next })
    row.production_completed_check = next ? 1 : 0
    ElMessage.success(next ? '完了にしました' : '未完了に戻しました')
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '更新に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingCompletedLoading.value = null
  }
}

/** 面取指示 カウント無切替 */
async function toggleChamferingNoCount(row: ChamferingManagementRow) {
  const id = row.id
  if (id == null) return
  const next = !row.no_count
  chamferingNoCountLoading.value = id
  try {
    await request.patch(`/api/plan/chamfering-management/${id}`, { no_count: !!next })
    row.no_count = next ? 1 : 0
    ElMessage.success(next ? 'カウント無にしました' : 'カウント無を解除しました')
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '更新に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingNoCountLoading.value = null
  }
}

function openCuttingEditDialog(row: CuttingManagementRow) {
  if (row.id == null) return
  editingCuttingId.value = row.id
  cuttingEditForm.cutting_machine = (row.cutting_machine ?? '') || ''
  cuttingEditForm.actual_production_quantity = row.actual_production_quantity != null ? String(row.actual_production_quantity) : ''
  cuttingEditForm.defect_qty = row.defect_qty != null ? String(row.defect_qty) : ''
  cuttingEditForm.production_lot_size = row.production_lot_size ?? null
  cuttingEditForm.lot_number = row.lot_number != null ? String(row.lot_number) : ''
  cuttingEditForm.production_sequence = row.production_sequence ?? 1
  cuttingEditForm.remarks = (row.remarks ?? '') || ''
  cuttingEditForm.use_material_stock_sub = (row as { use_material_stock_sub?: number }).use_material_stock_sub === 1 ? 1 : 0
  const rowUsage = (row as { usage_count?: number }).usage_count
  cuttingEditForm.usage_count = rowUsage != null && Number(rowUsage) > 0 ? Number(rowUsage) : 1
  cuttingEditDialogVisible.value = true
}

/** 備考にボタン名を追記 */
function appendCuttingRemark(label: string) {
  const s = (cuttingEditForm.remarks ?? '').trim()
  cuttingEditForm.remarks = s ? `${s} ${label}` : label
}

async function saveCuttingEdit() {
  const id = editingCuttingId.value
  if (id == null) return
  cuttingEditSubmitting.value = true
  try {
    const qty = cuttingEditForm.actual_production_quantity
    const qtyNum = qty === '' || qty === null || qty === undefined ? 0 : parseInt(String(qty).trim(), 10)
    const defectStr = cuttingEditForm.defect_qty
    const defectNum = defectStr === '' || defectStr === null || defectStr === undefined ? 0 : parseInt(String(defectStr).trim(), 10)
    await request.patch(`/api/plan/cutting-management/${id}`, {
      cutting_machine: cuttingEditForm.cutting_machine?.trim() || null,
      actual_production_quantity: Number.isNaN(qtyNum) ? 0 : qtyNum,
      defect_qty: Number.isNaN(defectNum) ? 0 : Math.max(0, defectNum),
      production_lot_size: cuttingEditForm.production_lot_size,
      lot_number: cuttingEditForm.lot_number?.trim() || null,
      production_sequence: cuttingEditForm.production_sequence,
      remarks: cuttingEditForm.remarks?.trim() || null,
      use_material_stock_sub: cuttingEditForm.use_material_stock_sub,
      usage_count: cuttingEditForm.usage_count,
    })
    ElMessage.success('保存しました')
    cuttingEditDialogVisible.value = false
    loadCuttingManagement()
    loadChamferingBatchList()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '保存に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    cuttingEditSubmitting.value = false
  }
}

function openChamferingEditDialog(row: ChamferingManagementRow) {
  if (row.id == null) return
  editingChamferingId.value = row.id
  const baseQty = row.actual_production_quantity != null ? Number(row.actual_production_quantity) : 0
  chamferingEditBaselineQuantity.value = Number.isNaN(baseQty) ? 0 : baseQty
  chamferingEditForm.chamfering_machine = (row.chamfering_machine ?? '') || ''
  chamferingEditForm.actual_production_quantity = row.actual_production_quantity != null ? String(row.actual_production_quantity) : ''
  chamferingEditForm.defect_qty = row.defect_qty != null ? String(row.defect_qty) : ''
  chamferingEditForm.production_lot_size = row.production_lot_size ?? null
  chamferingEditForm.lot_number = row.lot_number != null ? String(row.lot_number) : ''
  chamferingEditForm.production_sequence = row.production_sequence ?? 1
  chamferingEditForm.remarks = (row.remarks ?? '') || ''
  chamferingEditDialogVisible.value = true
}

/** 面取指示編集：生産数変更時、差（基準 - 生産数）を不良数に自動反映 */
function onChamferingEditProductionQuantityInput() {
  const raw = chamferingEditForm.actual_production_quantity
  const parsed = raw === '' || raw === null || raw === undefined ? 0 : parseInt(String(raw).trim(), 10)
  const qty = Number.isNaN(parsed) ? 0 : Math.max(0, parsed)
  const baseline = chamferingEditBaselineQuantity.value
  chamferingEditForm.defect_qty = String(Math.max(0, baseline - qty))
}

async function saveChamferingEdit() {
  const id = editingChamferingId.value
  if (id == null) return
  chamferingEditSubmitting.value = true
  try {
    const qty = chamferingEditForm.actual_production_quantity
    const qtyNum = qty === '' || qty === null || qty === undefined ? 0 : parseInt(String(qty).trim(), 10)
    const defectStr = chamferingEditForm.defect_qty
    const defectNum = defectStr === '' || defectStr === null || defectStr === undefined ? 0 : parseInt(String(defectStr).trim(), 10)
    await request.patch(`/api/plan/chamfering-management/${id}`, {
      chamfering_machine: chamferingEditForm.chamfering_machine?.trim() || null,
      actual_production_quantity: Number.isNaN(qtyNum) ? 0 : qtyNum,
      defect_qty: Number.isNaN(defectNum) ? 0 : Math.max(0, defectNum),
      production_lot_size: chamferingEditForm.production_lot_size,
      lot_number: chamferingEditForm.lot_number?.trim() || null,
      production_sequence: chamferingEditForm.production_sequence,
      remarks: chamferingEditForm.remarks?.trim() || null,
    })
    ElMessage.success('保存しました')
    chamferingEditDialogVisible.value = false
    loadChamferingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '保存に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingEditSubmitting.value = false
  }
}

function onChamferingNewProductChange(productCd: string) {
  const p = chamferingProductOptions.value.find((x) => x.product_cd === productCd)
  chamferingNewForm.product_name = p?.product_name ?? ''
}

async function openChamferingNewDialog() {
  chamferingNewForm.production_day = selectedChamferingDateToday.value || getTodayString()
  chamferingNewForm.production_line = ''
  chamferingNewForm.chamfering_machine = selectedChamferingMachineFilter.value || chamferingMachineOptions.value[0]?.machine_name || ''
  chamferingNewForm.product_cd = ''
  chamferingNewForm.product_name = ''
  chamferingNewForm.actual_production_quantity = ''
  chamferingNewForm.production_sequence = null
  chamferingNewForm.material_name = ''
  chamferingNewForm.management_code = ''
  await Promise.all([
    loadMachineOptions(),
    loadChamferingProductOptions(),
    loadChamferingMaterialOptions(),
  ])
  chamferingNewDialogVisible.value = true
}

function resetChamferingNewForm() {
  chamferingNewForm.production_day = ''
  chamferingNewForm.production_line = ''
  chamferingNewForm.chamfering_machine = ''
  chamferingNewForm.product_cd = ''
  chamferingNewForm.product_name = ''
  chamferingNewForm.actual_production_quantity = ''
  chamferingNewForm.production_sequence = null
  chamferingNewForm.material_name = ''
  chamferingNewForm.management_code = ''
}

async function submitChamferingNew() {
  const day = (chamferingNewForm.production_day || '').toString().trim()
  const machine = (chamferingNewForm.chamfering_machine || '').toString().trim()
  const productCd = (chamferingNewForm.product_cd || '').toString().trim()
  const productName = (chamferingNewForm.product_name || '').toString().trim()
  if (!day || day.length < 10) {
    ElMessage.warning('生産日を入力してください（YYYY-MM-DD）')
    return
  }
  if (!machine) {
    ElMessage.warning('面取機を選択してください')
    return
  }
  if (!productCd || !productName) {
    ElMessage.warning('製品CD・製品名は必須です')
    return
  }
  chamferingNewSubmitting.value = true
  try {
    const qty = parseInt(String(chamferingNewForm.actual_production_quantity || '0'), 10) || 0
    await request.post('/api/plan/chamfering-management', {
      production_day: day.slice(0, 10),
      production_line: chamferingNewForm.production_line?.trim() || '',
      chamfering_machine: machine,
      product_cd: productCd,
      product_name: productName,
      actual_production_quantity: qty,
      production_sequence: chamferingNewForm.production_sequence ?? undefined,
      material_name: chamferingNewForm.material_name?.trim() || undefined,
      management_code: chamferingNewForm.management_code?.trim() || undefined,
    })
    ElMessage.success('面取指示を登録しました')
    chamferingNewDialogVisible.value = false
    loadChamferingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '登録に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingNewSubmitting.value = false
  }
}

/** 生産日セル：双击でインライン編集開始 */
function startEditProductionDay(row: CuttingManagementRow) {
  if (row.id == null) return
  editingProductionDayId.value = row.id
  editingProductionDayValue.value = formatDateOnly(String(row.production_day ?? '')) || getTodayString()
}

/** 生産日を保存（PATCH）して編集終了。修改后日期＞修改前则自动排到该日同機種第一位，修改后＜修改前则排到最后一位 */
async function saveProductionDay(row: CuttingManagementRow, dateStr: string) {
  const id = row.id
  if (id == null) return
  const d = dateStr.slice(0, 10)
  if (!d) return
  const oldDate = formatDateOnly(String(row.production_day ?? '')) || ''
  const putFirst = !!oldDate && d > oldDate  // 修改后日期 > 修改前 → 该日内排第一位
  const putLast = !!oldDate && d < oldDate  // 修改后日期 < 修改前 → 该日内排最后一位
  try {
    await request.patch(`/api/plan/cutting-management/${id}`, { production_day: d })
    ;(row as { production_day?: string }).production_day = d
    ElMessage.success('生産日を更新しました')
    editingProductionDayId.value = null
    await loadCuttingManagement()
    loadChamferingBatchList()

    // 生産順：修改后日期在「今日」或「翌日」视图中时，自动排到该日期同一切断機的第一位或最后一位
    if (putFirst || putLast) {
      const todayStr = selectedDateToday.value ? String(selectedDateToday.value).slice(0, 10) : ''
      const tomorrowStr = selectedDateTomorrow.value ? String(selectedDateTomorrow.value).slice(0, 10) : ''
      if (d === todayStr || d === tomorrowStr) {
        const list = d === todayStr ? cuttingManagementList.value : cuttingManagementListTomorrow.value
        const cm = (row.cutting_machine || '').trim()
        if (cm) {
          const sameMachine = list.filter((r) => (r.cutting_machine || '').trim() === cm)
          const sorted = [...sameMachine].sort((a, b) => {
            const sa = (a.production_sequence ?? 0)
            const sb = (b.production_sequence ?? 0)
            if (sa !== sb) return sa - sb
            return (a.id ?? 0) - (b.id ?? 0)
          })
          const orderedIds = sorted.map((r) => r.id!).filter((rid) => rid != null)
          if (orderedIds.length > 0 && orderedIds.includes(id)) {
            const newOrderedIds = putFirst
              ? [id, ...orderedIds.filter((rid) => rid !== id)]
              : [...orderedIds.filter((rid) => rid !== id), id]
            await request.post('/api/plan/cutting-management/reorder', { cutting_machine: cm, ordered_ids: newOrderedIds })
            await loadCuttingManagement()
          }
        }
      }
    }
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '更新に失敗しました'
    ElMessage.error(String(msg))
  }
}

/** 生産日編集をキャンセル（未保存で閉じる） */
function cancelEditProductionDay() {
  editingProductionDayId.value = null
}

/** 面取指示：生産日セル双击でインライン編集開始 */
function startEditChamferingProductionDay(row: ChamferingManagementRow) {
  if (row.id == null) return
  editingChamferingProductionDayId.value = row.id
  editingChamferingProductionDayValue.value = formatDateOnly(String(row.production_day ?? '')) || getTodayString()
}

/** 面取指示：生産日を保存（PATCH）して編集終了。修改后日期＞修改前则自动排到该日同面取機第一位，修改后＜修改前则排到最后一位 */
async function saveChamferingProductionDay(row: ChamferingManagementRow, dateStr: string) {
  const id = row.id
  if (id == null) return
  const d = dateStr.slice(0, 10)
  if (!d) return
  const oldDate = formatDateOnly(String(row.production_day ?? '')) || ''
  const putFirst = !!oldDate && d > oldDate
  const putLast = !!oldDate && d < oldDate
  try {
    await request.patch(`/api/plan/chamfering-management/${id}`, { production_day: d })
    ;(row as { production_day?: string }).production_day = d
    ElMessage.success('生産日を更新しました')
    editingChamferingProductionDayId.value = null
    await loadChamferingManagement()

    if (putFirst || putLast) {
      const todayStr = selectedChamferingDateToday.value ? String(selectedChamferingDateToday.value).slice(0, 10) : ''
      const tomorrowStr = selectedChamferingDateTomorrow.value ? String(selectedChamferingDateTomorrow.value).slice(0, 10) : ''
      if (d === todayStr || d === tomorrowStr) {
        const list = d === todayStr ? chamferingManagementListToday.value : chamferingManagementListTomorrow.value
        const cm = (row.chamfering_machine || '').trim()
        if (cm) {
          const sameMachine = list.filter((r) => (r.chamfering_machine || '').trim() === cm)
          const sorted = [...sameMachine].sort((a, b) => {
            const sa = (a.production_sequence ?? 0)
            const sb = (b.production_sequence ?? 0)
            if (sa !== sb) return sa - sb
            return (a.id ?? 0) - (b.id ?? 0)
          })
          const orderedIds = sorted.map((r) => r.id!).filter((rid) => rid != null)
          if (orderedIds.length > 0 && orderedIds.includes(id)) {
            const newOrderedIds = putFirst
              ? [id, ...orderedIds.filter((rid) => rid !== id)]
              : [...orderedIds.filter((rid) => rid !== id), id]
            await request.post('/api/plan/chamfering-management/reorder', {
              chamfering_machine: cm,
              production_day: d,
              ordered_ids: newOrderedIds,
            })
            await loadChamferingManagement()
          }
        }
      }
    }
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '更新に失敗しました'
    ElMessage.error(String(msg))
  }
}

/** 面取指示：生産日編集をキャンセル */
function cancelEditChamferingProductionDay() {
  editingChamferingProductionDayId.value = null
}

/** 顺延：未完了分を翌日へ分割（当日完成数 + 翌日行を新規） */
const splitToNextDayDialogVisible = ref(false)
const splitDialogRow = ref<CuttingManagementRow | null>(null)
const splitTodayQuantityInput = ref('0')
const splitNextDay = ref('')
const splitToNextDaySubmitting = ref(false)
/** 順延ダイアログ：当日完成数入力にフォーカス用 */
const splitTodayQuantityInputRef = ref<{ focus: () => void } | null>(null)
const chamferingSplitTodayQuantityInputRef = ref<{ focus: () => void } | null>(null)
/** 面取指示 順延用 */
const chamferingSplitDialogVisible = ref(false)
const chamferingSplitDialogRow = ref<ChamferingManagementRow | null>(null)
const chamferingSplitTodayQuantityInput = ref('0')
const chamferingSplitNextDay = ref('')
const chamferingSplitSubmitting = ref(false)

/** 翌日順延の生産日：土日を選択不可にする */
function disabledWeekendDate(date: Date) {
  const d = date.getDay()
  return d === 0 || d === 6
}

/** 指定日から +1 日し、土日なら翌月曜にする（翌日順延の初期値用） */
function nextWeekdayFrom(dateStr: string): string {
  let s = shiftDate(dateStr, 1)
  const d = new Date(s.slice(0, 10) + 'T12:00:00')
  const day = d.getDay()
  if (day === 0) d.setDate(d.getDate() + 1)
  else if (day === 6) d.setDate(d.getDate() + 2)
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0')
}

function onSplitTodayQuantityInput(val: string) {
  const s = val.replace(/\D/g, '')
  splitTodayQuantityInput.value = s
}

function openSplitToNextDayDialog(row: CuttingManagementRow) {
  const total = row.actual_production_quantity ?? 0
  if (total <= 0) return
  splitDialogRow.value = row
  splitTodayQuantityInput.value = '0'
  splitNextDay.value = nextWeekdayFrom(String(row.production_day ?? ''))
  splitToNextDayDialogVisible.value = true
  nextTick(() => splitTodayQuantityInputRef.value?.focus())
}

async function confirmSplitToNextDay() {
  const row = splitDialogRow.value
  if (!row || row.id == null) return
  const todayQty = parseInt(splitTodayQuantityInput.value, 10) || 0
  const total = row.actual_production_quantity ?? 0
  if (todayQty < 0 || todayQty >= total) {
    ElMessage.warning('当日完成数は 0 以上、かつ現在の生産数より少なく入力してください')
    return
  }
  splitToNextDaySubmitting.value = true
  try {
    await request.post(`/api/plan/cutting-management/${row.id}/split-to-next-day`, {
      today_quantity: todayQty,
      next_day: splitNextDay.value || undefined,
    })
    // 順延後、元の行を自動的に「完了」に更新
    try {
      await request.patch(`/api/plan/cutting-management/${row.id}`, { production_completed_check: 1 })
      row.production_completed_check = 1
    } catch {
      // 完了フラグ更新が失敗してもメインの順延は成功扱い
    }
    ElMessage.success('順延しました（元の行を完了にしました）')
    splitToNextDayDialogVisible.value = false
    loadCuttingManagement()
    loadChamferingBatchList()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '順延に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    splitToNextDaySubmitting.value = false
  }
}

/** 複製：当行を直下に複製 */
async function duplicateCuttingRow(row: CuttingManagementRow) {
  const id = row.id
  if (id == null) return
  try {
    await request.post(`/api/plan/cutting-management/${id}/duplicate`)
    ElMessage.success('複製しました')
    loadCuttingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '複製に失敗しました'
    ElMessage.error(String(msg))
  }
}

/** 削除：確認後で当行を削除 */
async function deleteCuttingRow(row: CuttingManagementRow) {
  const id = row.id
  if (id == null) return
  try {
    await ElMessageBox.confirm(
      'この切断指示を削除しますか？紐づく面取指示・面取ロット一覧・カンバン発行も削除されます。',
      '削除の確認',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' }
    )
  } catch {
    return
  }
  try {
    await request.delete(`/api/plan/cutting-management/${id}`)
    ElMessage.success('削除しました')
    loadCuttingManagement()
    loadChamferingManagement()
    loadChamferingBatchList()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '削除に失敗しました'
    ElMessage.error(String(msg))
  }
}

/** 面取指示1件を削除（確認後） */
async function deleteChamferingRow(row: ChamferingManagementRow) {
  const id = row.id
  if (id == null) return
  try {
    await ElMessageBox.confirm(
      'この面取指示を削除しますか？紐づくカンバン発行も削除されます。',
      '削除の確認',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' }
    )
  } catch {
    return
  }
  try {
    await request.delete(`/api/plan/chamfering-management/${id}`)
    ElMessage.success('削除しました')
    loadChamferingManagement()
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '削除に失敗しました'
    ElMessage.error(String(msg))
  }
}

function onChamferingSplitTodayQuantityInput(val: string) {
  const s = val.replace(/\D/g, '')
  chamferingSplitTodayQuantityInput.value = s
}

function openChamferingSplitDialog(row: ChamferingManagementRow) {
  const total = row.actual_production_quantity ?? 0
  if (total <= 0) return
  chamferingSplitDialogRow.value = row
  chamferingSplitTodayQuantityInput.value = '0'
  chamferingSplitNextDay.value = nextWeekdayFrom(String(row.production_day ?? ''))
  chamferingSplitDialogVisible.value = true
  nextTick(() => chamferingSplitTodayQuantityInputRef.value?.focus())
}

async function confirmChamferingSplit() {
  const row = chamferingSplitDialogRow.value
  if (!row || row.id == null) return
  const todayQty = parseInt(chamferingSplitTodayQuantityInput.value, 10) || 0
  const total = row.actual_production_quantity ?? 0
  if (todayQty < 0 || todayQty >= total) {
    ElMessage.warning('当日完成数は 0 以上、かつ現在の生産数より少なく入力してください')
    return
  }
  chamferingSplitSubmitting.value = true
  try {
    await request.post(`/api/plan/chamfering-management/${row.id}/split-to-next-day`, {
      today_quantity: todayQty,
      next_day: chamferingSplitNextDay.value || undefined,
    })
    ElMessage.success('順延しました（元の行を完了にしました）')
    chamferingSplitDialogVisible.value = false
    loadChamferingManagement()
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '順延に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingSplitSubmitting.value = false
  }
}

/** 面取指示1件を複製 */
async function duplicateChamferingRow(row: ChamferingManagementRow) {
  const id = row.id
  if (id == null) return
  try {
    await request.post(`/api/plan/chamfering-management/${id}/duplicate`)
    ElMessage.success('複製しました')
    loadChamferingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '複製に失敗しました'
    ElMessage.error(String(msg))
  }
}

async function loadChamferingManagement() {
  chamferingManagementLoading.value = true
  const baseParams: Record<string, string> = {}
  const todayParam = selectedChamferingDateToday.value ? String(selectedChamferingDateToday.value).slice(0, 10) : ''
  const tomorrowParam = selectedChamferingDateTomorrow.value ? String(selectedChamferingDateTomorrow.value).slice(0, 10) : ''
  const chamferingMachineParam = selectedChamferingMachineFilter.value ? String(selectedChamferingMachineFilter.value).trim() : undefined
  try {
    const [resToday, resTomorrow] = await Promise.all([
      request.get<{ success?: boolean; data?: ChamferingManagementRow[] }>(
        '/api/plan/chamfering-management/list',
        { params: { ...baseParams, limit: 2000, ...(todayParam ? { production_day: todayParam } : {}), ...(chamferingMachineParam ? { chamfering_machine: chamferingMachineParam } : {}) } }
      ),
      request.get<{ success?: boolean; data?: ChamferingManagementRow[] }>(
        '/api/plan/chamfering-management/list',
        { params: { ...baseParams, limit: 2000, ...(tomorrowParam ? { production_day: tomorrowParam } : {}), ...(chamferingMachineParam ? { chamfering_machine: chamferingMachineParam } : {}) } }
      ),
    ])
    chamferingManagementListToday.value = (resToday as any)?.success ? ((resToday as any).data ?? []) : []
    chamferingManagementListTomorrow.value = (resTomorrow as any)?.success ? ((resTomorrow as any).data ?? []) : []
    chamferingManagementList.value = [...chamferingManagementListToday.value, ...chamferingManagementListTomorrow.value]
  } catch (e) {
    console.error('面取指示一覧の取得に失敗:', e)
    chamferingManagementListToday.value = []
    chamferingManagementListTomorrow.value = []
    chamferingManagementList.value = []
  } finally {
    chamferingManagementLoading.value = false
  }
}

async function loadChamferingBatchList() {
  chamferingBatchLoading.value = true
  try {
    const params: Record<string, string | number> = {}
    params.limit = 50000
    const result = await request.get<{ success?: boolean; data?: ChamferingBatchRow[] }>(
      '/api/plan/chamfering-plans/list',
      { params }
    )
    chamferingBatchList.value = (result as any)?.success ? ((result as any).data ?? []) : []
  } catch (e) {
    console.error('面取ロット一覧の取得に失敗:', e)
    chamferingBatchList.value = []
  } finally {
    chamferingBatchLoading.value = false
  }
}

async function updateChamferingPlanSw(row: ChamferingBatchRow, value: boolean) {
  const id = row.id
  if (id == null) return
  chamferingSwLoading.value = id
  try {
    await request.patch(`/api/plan/chamfering-plans/${id}`, { has_sw_process: value })
    row.has_sw_process = value ? 1 : 0
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? 'SWの更新に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingSwLoading.value = null
  }
}

async function copyChamferingPlan(row: ChamferingBatchRow) {
  const id = row.id
  if (id == null) return
  chamferingBatchActionLoading.value = id
  try {
    await request.post(`/api/plan/chamfering-plans/${id}/copy`)
    ElMessage.success('複製しました')
    loadChamferingBatchList()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '複製に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingBatchActionLoading.value = null
  }
}

async function deleteChamferingPlan(row: ChamferingBatchRow) {
  const id = row.id
  if (id == null) return
  try {
    await ElMessageBox.confirm(
      'この面取ロットを削除しますか？',
      '削除の確認',
      { type: 'warning', confirmButtonText: '削除', cancelButtonText: 'キャンセル' }
    )
  } catch {
    return
  }
  chamferingBatchActionLoading.value = id
  try {
    await request.delete(`/api/plan/chamfering-plans/${id}`)
    ElMessage.success('削除しました')
    loadChamferingBatchList()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '削除に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    chamferingBatchActionLoading.value = null
  }
}

function resetChamferingPlanNewForm() {
  chamferingPlanNewForm.production_month = ''
  chamferingPlanNewForm.production_day = ''
  chamferingPlanNewForm.production_line = ''
  chamferingPlanNewForm.production_order = null
  chamferingPlanNewForm.product_cd = ''
  chamferingPlanNewForm.product_name = ''
  chamferingPlanNewForm.actual_production_quantity = 0
  chamferingPlanNewForm.production_lot_size = null
  chamferingPlanNewForm.lot_number = ''
  chamferingPlanNewForm.chamfering_length = null
  chamferingPlanNewForm.material_name = ''
  chamferingPlanNewForm.has_sw_process = 0
}

function openChamferingPlanNewDialog() {
  resetChamferingPlanNewForm()
  chamferingPlanNewForm.production_month = getCurrentMonthYYYYMM()
  chamferingPlanNewForm.production_day = getTodayString()
  loadChamferingMachineOptions()
  loadChamferingProductOptions()
  chamferingPlanNewDialogVisible.value = true
}

async function onChamferingPlanNewProductChange(productCd: string) {
  if (!productCd) {
    chamferingPlanNewForm.product_name = ''
    chamferingPlanNewForm.material_name = ''
    chamferingPlanNewForm.chamfering_length = null
    return
  }
  const opt = chamferingProductOptions.value.find((p) => p.product_cd === productCd)
  if (opt) chamferingPlanNewForm.product_name = opt.product_name ?? ''
  try {
    const res = await request.get<{ success?: boolean; data?: Record<string, unknown> }>(
      `/api/master/products/batch-detail/${encodeURIComponent(productCd)}`
    )
    const data = (res as any)?.data
    if (data) {
      chamferingPlanNewForm.material_name = (data.material_name ?? '') as string
      chamferingPlanNewForm.chamfering_length = (data.chamfering_length ?? null) as number | null
    }
  } catch (e) {
    console.error('製品詳細取得失敗:', e)
  }
}

async function saveChamferingPlanNew() {
  const month = (chamferingPlanNewForm.production_month ?? '').toString().trim()
  const day = (chamferingPlanNewForm.production_day ?? '').toString().trim().slice(0, 10)
  const line = (chamferingPlanNewForm.production_line ?? '').toString().trim()
  const productCd = (chamferingPlanNewForm.product_cd ?? '').toString().trim()
  const productName = (chamferingPlanNewForm.product_name ?? '').toString().trim()
  if (!month || month.length < 7) {
    ElMessage.warning('生産月を選択してください')
    return
  }
  if (!day || day.length < 10) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  if (!line) {
    ElMessage.warning('ライン（面取機）を選択してください')
    return
  }
  if (!productCd || !productName) {
    ElMessage.warning('製品を選択してください')
    return
  }
  chamferingPlanNewSubmitting.value = true
  try {
    await request.post('/api/plan/chamfering-plans', {
      production_month: month,
      production_day: day,
      production_line: line,
      production_order: chamferingPlanNewForm.production_order ?? undefined,
      product_cd: productCd,
      product_name: productName,
      actual_production_quantity: chamferingPlanNewForm.actual_production_quantity ?? 0,
      production_lot_size: chamferingPlanNewForm.production_lot_size ?? undefined,
      lot_number: chamferingPlanNewForm.lot_number?.trim() || undefined,
      chamfering_length: chamferingPlanNewForm.chamfering_length ?? undefined,
      material_name: chamferingPlanNewForm.material_name?.trim() || undefined,
      has_sw_process: chamferingPlanNewForm.has_sw_process ?? 0,
    })
    ElMessage.success('登録しました')
    chamferingPlanNewDialogVisible.value = false
    loadChamferingBatchList()
  } catch (err: unknown) {
    const errResp = err as { response?: { data?: { detail?: string | unknown[] } }; message?: string }
    const detail = errResp.response?.data?.detail
    let msg: string
    if (typeof detail === 'string') msg = detail
    else if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string } | unknown
      msg = (first && typeof first === 'object' && 'msg' in first ? (first as { msg: string }).msg : String(first))
    } else msg = errResp.message ?? '登録に失敗しました'
    ElMessage.error(msg)
  } finally {
    chamferingPlanNewSubmitting.value = false
  }
}

async function loadKanbanIssuance() {
  kanbanIssuanceLoading.value = true
  try {
    const params: Record<string, string | number> = { limit: 2000 }
    if (kanbanFilterProductionDay.value) params.production_day = kanbanFilterProductionDay.value
    if (kanbanFilterStatus.value) params.status = kanbanFilterStatus.value
    if (kanbanFilterProductName.value) params.product_name = kanbanFilterProductName.value
    const result = await request.get<{ success?: boolean; data?: KanbanIssuanceRow[] }>(
      '/api/plan/kanban-issuance/list',
      { params }
    )
    kanbanIssuanceList.value = (result as any)?.success ? ((result as any).data ?? []) : []
    kanbanPage.value = 1
  } catch (e) {
    console.error('カンバン発行一覧の取得に失敗:', e)
    kanbanIssuanceList.value = []
  } finally {
    kanbanIssuanceLoading.value = false
    // フィルタ変更時などは全ページ一括選択フラグ・選択状態をクリア
    kanbanSelectAllAllPages.value = false
    kanbanIssuanceSelection.value = []
  }
}

async function loadKanbanProductNames() {
  try {
    const result = await request.get<{ success?: boolean; data?: string[] }>(
      '/api/plan/kanban-issuance/product-names',
      { params: { limit: 500 } }
    )
    kanbanIssuanceProductNameOptions.value = (result as any)?.success ? ((result as any).data ?? []) : []
  } catch (e) {
    console.error('カンバン製品名一覧の取得に失敗:', e)
    kanbanIssuanceProductNameOptions.value = []
  }
}

function setKanbanFilterToday() {
  kanbanFilterProductionDay.value = getTodayString()
  loadKanbanIssuance()
}

function shiftKanbanFilterDay(delta: number) {
  kanbanFilterProductionDay.value = shiftDate(
    kanbanFilterProductionDay.value || getTodayString(),
    delta
  )
  loadKanbanIssuance()
}

/** 1枚分の切断現品票HTML（上中下で同じ内容を3回使う） */
function buildOneKanbanTicketHtml(row: KanbanIssuanceRow, kanbanNo: string): string {
  const esc = (v: unknown) => String(v ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const fmtDate = (v: string | null | undefined) => (v ? String(v).slice(0, 10).replace(/-/g, '/') : '')
  const lotQty = row.actual_production_quantity != null ? row.actual_production_quantity : ''
  const lineDisplay = esc(row.production_line || '')
  const cuttingMachineDisplay = esc(row.cutting_machine || '')
  const lineShort = esc((row.production_line || '').replace(/号機$/, ''))
  const chamferDisplay = row.has_chamfering_process ? '有り' : '--'
  const chamferingLengthDisplay = (row.chamfering_length != null && Number(row.chamfering_length) !== 0) ? esc(row.chamfering_length) : '--'
  const hasDevelopedLength = row.developed_length != null && Number(row.developed_length) !== 0
  const developedLengthDisplay = hasDevelopedLength ? esc(row.developed_length) : '--'
  const lotNoFromMgmt = esc(String(row.management_code ?? '').slice(-5))
  const productCdForQr = encodeURIComponent(String(row.product_cd ?? ''))
  const qrSrc = productCdForQr ? `https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${productCdForQr}` : ''
  const managementCode = String(row.management_code ?? '').trim()
  const mgmtQrSrc = managementCode
    ? `https://api.qrserver.com/v1/create-qr-code/?size=80x80&data=${encodeURIComponent(managementCode)}`
    : ''
  return `
    <div class="ticket-top">
      <div>
        <div class="ticket-title">切断現品票</div>
        <div class="ticket-qr-wrap">
          <div class="ticket-qr">${qrSrc ? `<img src="${qrSrc}" alt="QR" width="32" height="32" />` : '<span>QR</span>'}</div>
          <span class="ticket-qr-label">製品CD</span>
        </div>
      </div>
      <div class="ticket-product">${esc(row.product_name)}</div>
      <div class="ticket-top-right">
        <div class="ticket-machine">${lineDisplay}</div>
        <div class="ticket-mgmt-qr-wrap">
          <div class="ticket-mgmt-qr">${mgmtQrSrc ? `<img src="${mgmtQrSrc}" alt="管理コードQR" width="32" height="32" />` : ''}</div>
          <span class="ticket-mgmt-qr-label">管理コード</span>
        </div>
      </div>
    </div>
    <table class="tbl">
      <tr>
        <th>規格</th>
        <td colspan="3">${esc(row.standard_specification)}</td>
        <th>管理コード</th>
        <td colspan="3">${esc(row.management_code)}</td>
      </tr>
      <tr>
        <th>原材料</th>
        <td colspan="3">${esc(row.material_name)}</td>
  
        <th>成型予定期間</th>
        <td colspan="1">${fmtDate(row.start_date)}</td>
        <th class="tbl-c">～</th>
        <td colspan="1">${fmtDate(row.end_date)}</td>
      </tr>
      <tr>
        <th>製造番号</th>
        <td colspan="3"></td>       
        <th class="tbl-th-normal">成型計画数</th>
        <td class="big tbl-c">${esc(row.planned_quantity)}</td>
        <th class="tbl-th-normal">ロットNo.</th>
        <td class="big tbl-c">${esc(row.production_lot_size)}</td>       
      </tr>
      <tr>
        <th>ロット本数</th>
        <td class="red tbl-c">${esc(lotQty)}</td>
        <th>取数</th>
        <td class="big tbl-c">${esc(row.take_count)}</td>
        <th>工程</th>
        <td class="tbl-c">切断工程</td>
        <td class="tbl-c">面取工程</td>
        <th class="tbl-c tbl-th-normal">成型ライン</th>
      </tr>
      <tr>
        <th>切断長</th>
        <td class="big tbl-c">${esc(row.cutting_length)}</td>
        <th>面取長</th>
        <td class="tbl-c">${chamferingLengthDisplay}</td>
        <th>設備No.</th>
        <td class="tbl-c">${cuttingMachineDisplay}</td>
        <td></td>
        <td class="tbl-c">${lineShort}</td>
      </tr>
      <tr>
        <th>展開長</th>
        <td class="tbl-c${hasDevelopedLength ? ' tbl-developed-val' : ''}">${developedLengthDisplay}</td>
        <th>面取</th>
        <td class="tbl-c">${chamferDisplay}</td>
        <th>実績数</th>
        <td></td>
        <td></td>
        <td></td>
      </tr>
      <tr class="tbl-row-lotno">
        <th>ロットNo</th>
        <td colspan="3" class="big tbl-c tbl-lotno-val">${lotNoFromMgmt}</td>
        <th>確認</th>
        <td></td>
        <td></td>
        <td></td>
      </tr>
    </table>
    <div class="kanban-no">カンバン番号: ${esc(kanbanNo)}　発行日: ${fmtDate(new Date().toISOString())}</div>
  `
}

/** 切断現品票HTMLを生成して印刷ウィンドウを開く（A4縦・上中下3枚・切断線あり） */
function printKanbanTicket(row: KanbanIssuanceRow, kanbanNo: string) {
  const oneTicket = buildOneKanbanTicketHtml(row, kanbanNo)
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>切断現品票</title><style>
    @page { size: A4 portrait; margin: 8mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; width: 100%; height: 100%; font-family: 'Yu Gothic','MS Gothic',sans-serif; font-size: 10px; }
    .page { width: 194mm; height: 281mm; margin: 0; padding: 0; }
    .ticket-sheet { width: 100%; height: 281mm; display: flex; flex-direction: column; margin: 0; padding: 0; position: relative; }
    .ticket-block { flex: 0 0 calc(281mm / 3); height: calc(281mm / 3); display: flex; flex-direction: column; padding: 4mm 6mm; margin: 0; overflow: hidden; }
    .ticket-sheet .ticket-block:nth-of-type(2) { margin-bottom: 15px; }
    .ticket-block .ticket { flex: 1; display: flex; flex-direction: column; min-height: 0; }
    .cut-line { position: absolute; left: 0; right: 0; height: 0; border: none; border-top: 2px dotted #999; pointer-events: none; }
    .cut-line-1 { top: calc(281mm / 3 - 15px); }
    .cut-line-2 { top: calc(281mm * 2 / 3 + 4px); }
    .ticket-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 3px; border: 1px solid #333; padding: 4px; }
    .ticket-title { font-size: 16px; font-weight: bold; }
    .ticket-product { font-size: 42px; font-weight: bold; text-align: center; flex: 1; }
    .ticket-top-right { display: flex; flex-direction: column; align-items: flex-end; min-width: 80px; }
    .ticket-machine { font-size: 20px; font-weight: bold; color: #cc0000; text-align: right; }
    .ticket-mgmt-qr-wrap { display: flex; flex-direction: column; align-items: center; margin-top: 4px; }
    .ticket-mgmt-qr { width: 30px; height: 30px; border: 1px solid #999; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .ticket-mgmt-qr img { display: block; width: 32px; height: 32px; object-fit: contain; }
    .ticket-mgmt-qr-label { font-size: 6px; color: #666; margin-top: 0px; }
    .ticket-qr-wrap { display: flex; flex-direction: column; align-items: flex-start; margin-top: 10px; margin-bottom: 1px; }
    .ticket-qr { width: 30px; height: 30px; border: 1px solid #999; display: flex; align-items: center; justify-content: center; font-size: 6px; color: #aaa; }
    .ticket-qr-label { font-size: 6px; color: #666; margin-top: 0px; }
    .tbl { width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }
    .tbl th, .tbl td { border: 1px solid #333; padding: 2.4px 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.6; }
    .tbl th { background: transparent; font-weight: bold; text-align: left; }
    .tbl th.tbl-th-normal { font-weight: normal; }
    .tbl .tbl-c { text-align: center; }
    /* 各列宽（第1～8列，px 可改） */
    .tbl th:nth-child(1), .tbl td:nth-child(1) { width: 60px; }
    .tbl th:nth-child(2), .tbl td:nth-child(2) { width: 110px; }
    .tbl th:nth-child(3), .tbl td:nth-child(3) { width: 60px; }
    .tbl th:nth-child(4), .tbl td:nth-child(4) { width: 150px; }
    .tbl th:nth-child(5), .tbl td:nth-child(5) { width: 70px; }
    .tbl th:nth-child(6), .tbl td:nth-child(6) { width: 95px; }
    .tbl th:nth-child(7), .tbl td:nth-child(7) { width: 85px; }
    .tbl th:nth-child(8), .tbl td:nth-child(8) { width: 95px; }
    .tbl .tbl-row-lotno th, .tbl .tbl-row-lotno td { line-height: 3.05; }
    .tbl .tbl-lotno-val { font-size: 14px; line-height: 1.1; }
    .red { color: #cc0000; font-weight: bold; font-size: 12px; }
    .big { font-size: 12px; font-weight: bold; }
    .tbl-developed-val {
      background-color: #555 !important;
      color: #ffffff !important;
      font-weight: bold !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .kanban-no { font-size: 8px; color: #666; text-align: right; margin-top: 2px; }
    @media print {
      html, body { margin: 0 !important; padding: 0 !important; width: 194mm !important; height: 281mm !important; }
      .page { width: 194mm !important; height: 281mm !important; margin: 0 !important; padding: 0 !important; }
      .ticket-sheet { height: 281mm !important; }
      .ticket-block { flex: 0 0 calc(281mm / 3) !important; height: calc(281mm / 3) !important; }
      .tbl-developed-val {
        background-color: #555 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
    }
  </style></head><body>
  <div class="page">
    <div class="ticket-sheet">
      <div class="cut-line cut-line-1"></div>
      <div class="cut-line cut-line-2"></div>
      <div class="ticket-block"><div class="ticket">${oneTicket}</div></div>
      <div class="ticket-block"><div class="ticket">${oneTicket}</div></div>
      <div class="ticket-block"><div class="ticket">${oneTicket}</div></div>
    </div>
  </div>
  <script>window.onload=()=>{setTimeout(()=>{window.print();window.onafterprint=()=>window.close();}, 400);}<\/script>
  </body></html>`
  const w = window.open('', '_blank', 'width=620,height=900')
  if (w) { w.document.write(html); w.document.close() }
}

/** 一括：複数枚を1つの印刷ウィンドウで連続印刷（選択したデータを循环打印） */
function printKanbanTicketsBatch(items: { row: KanbanIssuanceRow; kanbanNo: string }[]) {
  if (!items.length) return
  const pagesHtml = items
    .slice()
    .sort((a, b) => {
      const ad = String(a.row.production_day ?? '')
      const bd = String(b.row.production_day ?? '')
      if (ad && bd && ad !== bd) return ad.localeCompare(bd)
      const am = String(a.row.cutting_machine ?? '')
      const bm = String(b.row.cutting_machine ?? '')
      if (am !== bm) return am.localeCompare(bm)
      const asrc = a.row.source_id ?? a.row.id ?? 0
      const bsrc = b.row.source_id ?? b.row.id ?? 0
      return asrc - bsrc
    })
    .map(({ row, kanbanNo }) => {
      const oneTicket = buildOneKanbanTicketHtml(row, kanbanNo)
      return `<div class="page ticket-page">
    <div class="ticket-sheet">
      <div class="cut-line cut-line-1"></div>
      <div class="cut-line cut-line-2"></div>
      <div class="ticket-block"><div class="ticket">${oneTicket}</div></div>
      <div class="ticket-block"><div class="ticket">${oneTicket}</div></div>
      <div class="ticket-block"><div class="ticket">${oneTicket}</div></div>
    </div>
  </div>`
    })
    .join('\n')
  const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>切断現品票（${items.length}枚）</title><style>
    @page { size: A4 portrait; margin: 8mm; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; width: 100%; font-family: 'Yu Gothic','MS Gothic',sans-serif; font-size: 10px; }
    .page { width: 194mm; height: 281mm; margin: 0; padding: 0; page-break-after: always; }
    .page:last-child { page-break-after: auto; }
    .ticket-sheet { width: 100%; height: 281mm; display: flex; flex-direction: column; margin: 0; padding: 0; position: relative; }
    .ticket-block { flex: 0 0 calc(281mm / 3); height: calc(281mm / 3); display: flex; flex-direction: column; padding: 4mm 6mm; margin: 0; overflow: hidden; }
    .ticket-sheet .ticket-block:nth-of-type(2) { margin-bottom: 15px; }
    .ticket-block .ticket { flex: 1; display: flex; flex-direction: column; min-height: 0; }
    .cut-line { position: absolute; left: 0; right: 0; height: 0; border: none; border-top: 2px dotted #999; pointer-events: none; }
    .cut-line-1 { top: calc(281mm / 3 - 15px); }
    .cut-line-2 { top: calc(281mm * 2 / 3 + 4px); }
    .ticket-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 3px; border: 1px solid #333; padding: 4px; }
    .ticket-title { font-size: 16px; font-weight: bold; }
    .ticket-product { font-size: 42px; font-weight: bold; text-align: center; flex: 1; }
    .ticket-top-right { display: flex; flex-direction: column; align-items: flex-end; min-width: 80px; }
    .ticket-machine { font-size: 20px; font-weight: bold; color: #cc0000; text-align: right; }
    .ticket-mgmt-qr-wrap { display: flex; flex-direction: column; align-items: center; margin-top: 4px; }
    .ticket-mgmt-qr { width: 30px; height: 30px; border: 1px solid #999; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .ticket-mgmt-qr img { display: block; width: 32px; height: 32px; object-fit: contain; }
    .ticket-mgmt-qr-label { font-size: 6px; color: #666; margin-top: 2px; }
    .ticket-qr-wrap { display: flex; flex-direction: column; align-items: flex-start; margin-top: 10px; margin-bottom: 3px; }
    .ticket-qr { width: 30px; height: 30px; border: 1px solid #999; display: flex; align-items: center; justify-content: center; font-size: 6px; color: #aaa; }
    .ticket-qr-label { font-size: 6px; color: #666; margin-top: 2px; }
    .tbl { width: 100%; border-collapse: collapse; font-size: 14px; table-layout: fixed; }
    .tbl th, .tbl td { border: 1px solid #333; padding: 2.4px 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.6; }
    .tbl th { background: transparent; font-weight: bold; text-align: left; }
    .tbl th.tbl-th-normal { font-weight: normal; }
    .tbl .tbl-c { text-align: center; }
    .tbl th:nth-child(1), .tbl td:nth-child(1) { width: 60px; }
    .tbl th:nth-child(2), .tbl td:nth-child(2) { width: 110px; }
    .tbl th:nth-child(3), .tbl td:nth-child(3) { width: 60px; }
    .tbl th:nth-child(4), .tbl td:nth-child(4) { width: 150px; }
    .tbl th:nth-child(5), .tbl td:nth-child(5) { width: 70px; }
    .tbl th:nth-child(6), .tbl td:nth-child(6) { width: 95px; }
    .tbl th:nth-child(7), .tbl td:nth-child(7) { width: 85px; }
    .tbl th:nth-child(8), .tbl td:nth-child(8) { width: 95px; }
    .tbl .tbl-row-lotno th, .tbl .tbl-row-lotno td { line-height: 3.14; }
    .tbl .tbl-lotno-val { font-size: 14px; line-height: 1.1; }
    .red { color: #cc0000; font-weight: bold; font-size: 12px; }
    .big { font-size: 12px; font-weight: bold; }
    .tbl-developed-val {
      background-color: #555 !important;
      color: #ffffff !important;
      font-weight: bold !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .kanban-no { font-size: 8px; color: #666; text-align: right; margin-top: 2px; }
    @media print {
      html, body { margin: 0 !important; padding: 0 !important; }
      .page { width: 194mm !important; height: 281mm !important; margin: 0 !important; padding: 0 !important; page-break-after: always !important; }
      .page:last-child { page-break-after: auto !important; }
      .ticket-sheet { height: 281mm !important; }
      .ticket-block { flex: 0 0 calc(281mm / 3) !important; height: calc(281mm / 3) !important; }
      .tbl-developed-val {
        background-color: #555 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
    }
  </style></head><body>
${pagesHtml}
  <script>window.onload=()=>{setTimeout(()=>{window.print();window.onafterprint=()=>window.close();}, 400);}<\/script>
  </body></html>`
  const w = window.open('', '_blank', 'width=620,height=900')
  if (w) { w.document.write(html); w.document.close() }
}

/** 待発行カンバンを手動で発行 */
async function issuePendingKanban(kanbanId: number) {
  const row = kanbanIssuanceList.value.find((r) => r.id === kanbanId)
  kanbanIssuePendingLoading.value = kanbanId
  try {
    const res = await request.post<{ success?: boolean; kanban_no?: string }>(
      `/api/plan/kanban-issuance/${kanbanId}/issue`
    )
    const kno = (res as any)?.kanban_no ?? ''
    ElMessage.success(kno ? `カンバン発行: ${kno}` : 'カンバンを発行しました')
    loadKanbanIssuance()
    if (row) printKanbanTicket(row, kno)
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? 'カンバン発行に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    kanbanIssuePendingLoading.value = null
  }
}

/** 発行済カンバンを再発行（現場で紛失した場合など） */
async function reissueKanban(kanbanId: number) {
  const row = kanbanIssuanceList.value.find((r) => r.id === kanbanId)
  kanbanReissueLoading.value = kanbanId
  try {
    const res = await request.post<{ success?: boolean; kanban_no?: string }>(
      `/api/plan/kanban-issuance/${kanbanId}/reissue`
    )
    const kno = (res as any)?.kanban_no ?? ''
    ElMessage.success(kno ? `再発行: ${kno}` : 'カンバンを再発行しました')
    loadKanbanIssuance()
    if (row) printKanbanTicket(row, kno)
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? '再発行に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    kanbanReissueLoading.value = null
  }
}

/** カンバン発行：ヘッダの「全選択」チェックボックスの状態変更 */
function onKanbanSelectAll(selection: KanbanIssuanceRow[]) {
  // selection は「現在ページ」に表示されている行のみ
  // 1件以上選択された場合は「全ページ分を対象」とみなす
  kanbanSelectAllAllPages.value = selection.length > 0
}

/** 選択した待発行カンバンを一括発行 */
async function batchIssueKanban() {
  // ヘッダーのチェックボックスで「全選択」が有効な場合は、現在のフィルタに合致する
  // 全ページ分のカンバンを対象とする。それ以外は、手動選択された行のみ。
  const sourceList = kanbanSelectAllAllPages.value ? kanbanIssuanceList.value : kanbanIssuanceSelection.value
  const pending = sourceList.filter(
    (r) => (r.status === 'pending' || r.status === 'issued') && r.id != null
  )
  if (!pending.length) {
    ElMessage.warning('発行対象のカンバン（待発行・発行済）を選択してください')
    return
  }
  kanbanBatchIssueLoading.value = true
  try {
    const res = await request.post<{
      success?: boolean
      issued?: number
      skipped?: number
      errors?: string[]
      issued_items?: { id: number; kanban_no: string }[]
    }>('/api/plan/kanban-issuance/batch-issue', { kanban_ids: pending.map((r) => r.id!) })
    const issued = (res as any)?.issued ?? 0
    const errors = (res as any)?.errors as string[] | undefined
    const issuedItems = (res as any)?.issued_items as { id: number; kanban_no: string }[] | undefined
    if (issued > 0) ElMessage.success((res as any)?.message ?? `${issued} 件発行しました`)
    if (errors?.length) ElMessage.warning(errors.slice(0, 3).join('; '))
    kanbanIssuanceSelection.value = []
    // 選択したデータを循环打印：后端返回的 issued_items 与选中行匹配，单窗口多页打印（避免弹窗被拦截）
    if (issued > 0 && Array.isArray(issuedItems) && issuedItems.length > 0) {
      const toPrint: { row: KanbanIssuanceRow; kanbanNo: string }[] = []
      for (const p of pending) {
        const item = issuedItems.find((i) => i.id === p.id)
        if (item?.kanban_no) toPrint.push({ row: p, kanbanNo: item.kanban_no })
      }
      if (toPrint.length) printKanbanTicketsBatch(toPrint)
    }
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? '一括発行に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    kanbanBatchIssueLoading.value = false
  }
}

/** カンバン発行の生産日を cutting_management / chamfering_management から同期する */
async function syncKanbanProductionDay() {
  kanbanSyncProductionDayLoading.value = true
  try {
    const res = await request.post<{ success?: boolean; message?: string; updated?: number }>(
      '/api/plan/kanban-issuance/sync-production-day'
    )
    ElMessage.success((res as any)?.message ?? '生産日を更新しました')
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? '生産日の更新に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    kanbanSyncProductionDayLoading.value = false
  }
}

/** カンバン発行：双击打开编辑弹窗 */
function openKanbanEdit(row: KanbanIssuanceRow) {
  if (!row?.id) return
  kanbanEditRow.value = row
  kanbanEditForm.product_cd = row.product_cd ?? ''
  kanbanEditForm.product_name = row.product_name ?? ''
  kanbanEditForm.production_line = row.production_line ?? ''
  kanbanEditForm.cutting_machine = row.cutting_machine ?? ''
  kanbanEditForm.material_name = row.material_name ?? ''
  kanbanEditForm.standard_specification = row.standard_specification ?? ''
  kanbanEditForm.management_code = row.management_code ?? ''
  kanbanEditForm.start_date = row.start_date ? String(row.start_date).slice(0, 10) : ''
  kanbanEditForm.end_date = row.end_date ? String(row.end_date).slice(0, 10) : ''
  kanbanEditForm.planned_quantity = row.planned_quantity ?? null
  kanbanEditForm.production_lot_size = row.production_lot_size ?? null
  kanbanEditForm.actual_production_quantity = row.actual_production_quantity ?? null
  kanbanEditForm.take_count = row.take_count ?? null
  kanbanEditForm.cutting_length = row.cutting_length != null ? Number(row.cutting_length) : null
  kanbanEditForm.chamfering_length = row.chamfering_length != null ? Number(row.chamfering_length) : null
  kanbanEditForm.developed_length = row.developed_length != null ? Number(row.developed_length) : null
  kanbanEditForm.has_chamfering_process = !!row.has_chamfering_process
  kanbanEditForm.lot_number = row.lot_number ?? ''
  kanbanEditForm.production_day = row.production_day ? String(row.production_day).slice(0, 10) : ''
  kanbanEditDialogVisible.value = true
}

/** カンバン発行：保存编辑 */
async function saveKanbanEdit() {
  const id = kanbanEditRow.value?.id
  if (!id) return
  kanbanEditSubmitting.value = true
  try {
    const body: Record<string, unknown> = {
      product_cd: kanbanEditForm.product_cd || undefined,
      product_name: kanbanEditForm.product_name || undefined,
      production_line: kanbanEditForm.production_line || undefined,
      cutting_machine: kanbanEditForm.cutting_machine || undefined,
      material_name: kanbanEditForm.material_name || undefined,
      standard_specification: kanbanEditForm.standard_specification || undefined,
      management_code: kanbanEditForm.management_code || undefined,
      start_date: kanbanEditForm.start_date || undefined,
      end_date: kanbanEditForm.end_date || undefined,
      planned_quantity: kanbanEditForm.planned_quantity ?? undefined,
      production_lot_size: kanbanEditForm.production_lot_size ?? undefined,
      actual_production_quantity: kanbanEditForm.actual_production_quantity ?? undefined,
      take_count: kanbanEditForm.take_count ?? undefined,
      cutting_length: kanbanEditForm.cutting_length ?? undefined,
      chamfering_length: kanbanEditForm.chamfering_length ?? undefined,
      developed_length: kanbanEditForm.developed_length ?? undefined,
      has_chamfering_process: kanbanEditForm.has_chamfering_process,
      lot_number: kanbanEditForm.lot_number || undefined,
      production_day: kanbanEditForm.production_day || undefined,
    }
    await request.patch<{ success?: boolean; message?: string }>(
      `/api/plan/kanban-issuance/${id}`,
      body
    )
    ElMessage.success('更新しました')
    kanbanEditDialogVisible.value = false
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? '更新に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    kanbanEditSubmitting.value = false
  }
}

async function loadCuttingManagement() {
  cuttingManagementLoading.value = true
  const baseParams: Record<string, string> = {}
  if (cuttingMachineFilter.value) baseParams.cutting_machine = cuttingMachineFilter.value
  const todayParam = normalizeDateStr(selectedDateToday.value)
  const tomorrowParam = normalizeDateStr(selectedDateTomorrow.value)
  try {
    const [resToday, resTomorrow] = await Promise.all([
      request.get<{ success?: boolean; data?: CuttingManagementRow[]; message?: string }>(
        '/api/plan/cutting-management/list',
        { params: { ...baseParams, limit: 2000, ...(todayParam ? { production_day: todayParam } : {}) } }
      ),
      request.get<{ success?: boolean; data?: CuttingManagementRow[]; message?: string }>(
        '/api/plan/cutting-management/list',
        { params: { ...baseParams, limit: 2000, ...(tomorrowParam ? { production_day: tomorrowParam } : {}) } }
      ),
    ])
    cuttingManagementList.value = (resToday as any)?.success ? ((resToday as any).data ?? []) as CuttingManagementRow[] : []
    cuttingManagementListTomorrow.value = (resTomorrow as any)?.success ? ((resTomorrow as any).data ?? []) as CuttingManagementRow[] : []
  } catch (e) {
    console.error('切断指示一覧の取得に失敗:', e)
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '切断指示データの取得に失敗しました'
    ElMessage.error(String(msg))
    cuttingManagementList.value = []
    cuttingManagementListTomorrow.value = []
  } finally {
    cuttingManagementLoading.value = false
    fetchUsageReflectedStatus()
  }
}
const confirmCuttingActualLoading = ref(false)
const confirmActualResultVisible = ref(false)
const confirmActualResultCount = ref(0)
const confirmActualResultTotalQty = ref(0)
async function confirmCuttingActual() {
  const day = selectedDateToday.value ? String(selectedDateToday.value).slice(0, 10) : ''
  if (!day) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  confirmCuttingActualLoading.value = true
  try {
    // 指定日付の全設備の合計で実績確定（当前選択の切断機に限定しない）
    const params: Record<string, string> = { production_day: day }
    const res = await request.post<{ success?: boolean; message?: string; inserted?: number; total_quantity?: number }>(
      '/api/plan/cutting-management/confirm-actual',
      null,
      { params }
    )
    confirmActualResultCount.value = (res as any)?.inserted ?? 0
    confirmActualResultTotalQty.value = (res as any)?.total_quantity ?? 0
    confirmActualResultVisible.value = true
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? '実績確定に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    confirmCuttingActualLoading.value = false
  }
}

/** 面取指示-今日：実績確定（chamfering_management → stock_transaction_logs）。当前日期的全设备数据を対象とする（面取機筛选に依存しない） */
const confirmChamferingActualLoading = ref(false)
async function confirmChamferingActual() {
  const day = selectedChamferingDateToday.value ? String(selectedChamferingDateToday.value).slice(0, 10) : ''
  if (!day) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  confirmChamferingActualLoading.value = true
  try {
    const params: Record<string, string> = { production_day: day }
    const res = await request.post<{ success?: boolean; message?: string; inserted?: number; total_quantity?: number }>(
      '/api/plan/chamfering-management/confirm-actual',
      null,
      { params }
    )
    confirmActualResultCount.value = (res as any)?.inserted ?? 0
    confirmActualResultTotalQty.value = (res as any)?.total_quantity ?? 0
    confirmActualResultVisible.value = true
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? '実績確定に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    confirmChamferingActualLoading.value = false
  }
}

/** 指示書発行：指定日の全データを切断機ごとに1ページずつ A5 横向で印刷 */
const issueCuttingInstructionSheetLoading = ref(false)
const printCuttingPlanLoading = ref(false)
/** 切断計画リスト印刷：指定日の各切断機データ＋材料在庫・材料バラ在庫（A4縦・余白小） */
async function printCuttingPlanList() {
  const day = selectedDateToday.value ? String(selectedDateToday.value).slice(0, 10) : ''
  if (!day) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  printCuttingPlanLoading.value = true
  try {
    const [cuttingRes, stockRes] = await Promise.all([
      request.get<{ success?: boolean; data?: CuttingManagementRow[] }>(
        '/api/plan/cutting-management/list',
        { params: { production_day: day, limit: 2000 } }
      ),
      request.get<{ success?: boolean; data?: { list?: { supplier_name?: string; material_name?: string; current_stock?: number }[] } }>(
        '/api/material/stock',
        { params: { target_date: day, page: 1, pageSize: 10000 } }
      ),
    ])
    type StockSubPrintRow = {
      supplier_name?: string
      material_name?: string
      current_stock?: number
      order_bundle_quantity?: number
      planned_usage?: number
    }
    const stockSubListRaw: StockSubPrintRow[] = []
    const subPageSize = 500
    for (let subPage = 1; subPage < 200; subPage += 1) {
      const stockSubRes = await request.get<{ success?: boolean; data?: { list?: StockSubPrintRow[]; total?: number } }>(
        '/api/material/stock/sub',
        { params: { page: subPage, pageSize: subPageSize } }
      )
      const chunk = (stockSubRes as any)?.success ? ((stockSubRes as any).data?.list ?? []) as StockSubPrintRow[] : []
      stockSubListRaw.push(...chunk)
      if (chunk.length < subPageSize) break
    }
    const rows = (cuttingRes as any)?.success ? ((cuttingRes as any).data ?? []) as CuttingManagementRow[] : []
    const stockListRaw = (stockRes as any)?.success ? ((stockRes as any).data?.list ?? []) : []
    const stockList = [...stockListRaw].sort((a: { supplier_name?: string; material_name?: string }, b: { supplier_name?: string; material_name?: string }) => {
      const sa = String(a.supplier_name ?? '')
      const sb = String(b.supplier_name ?? '')
      if (sa !== sb) return sa.localeCompare(sb)
      return String(a.material_name ?? '').localeCompare(String(b.material_name ?? ''))
    })
    // order_bundle_quantity>0 かつ「計画使用数が正でない」行。planned_usage は DB 上ほぼ 0〜正のため、<0 だけだと一致ゼロになりがち → <=0（未設定は 0 扱い）
    const stockSubList = stockSubListRaw.filter((r: StockSubPrintRow) => {
      const ob = Number(r.order_bundle_quantity) || 0
      if (ob <= 0) return false
      const pu = r.planned_usage == null ? 0 : Number(r.planned_usage)
      if (Number.isNaN(pu)) return false
      return pu <= 0
    })

    const byMachine = new Map<string, CuttingManagementRow[]>()
    for (const r of rows) {
      const key = (r.cutting_machine || '').trim() || '（未設定）'
      if (!byMachine.has(key)) byMachine.set(key, [])
      byMachine.get(key)!.push(r)
    }
    for (const [, list] of byMachine) {
      list.sort((a, b) => (a.production_sequence ?? 0) - (b.production_sequence ?? 0))
    }
    const machineNames = Array.from(byMachine.keys()).sort()

    const dayDisplay = day.replace(/-/g, '/')
    const leftBlocks: string[] = []
    for (const machineName of machineNames) {
      const list = byMachine.get(machineName)!
      const trs = list.map((r) => `
        <tr>
          <td>${escapeHtml(String(r.cd ?? ''))}</td>
          <td>${escapeHtml(String(r.product_name ?? ''))}</td>
          <td>${escapeHtml(String(r.material_name ?? ''))}</td>
          <td>${r.production_sequence ?? ''}</td>
          <td>${r.actual_production_quantity ?? ''}</td>
          <td>${r.production_time ?? ''}</td>
          <td>${escapeHtml(String(r.production_line ?? ''))}</td>
          <td>${escapeHtml(String(r.remarks ?? ''))}</td>
        </tr>`).join('')
      leftBlocks.push(`
        <div class="print-cut-block">
          <div class="print-cut-block-title">${escapeHtml(machineName)}</div>
          <table class="print-cut-table"><thead><tr>
            <th>コード</th><th>製品名</th><th>原材料</th><th>順位</th><th>生産数</th><th>時間</th><th>ライン</th><th>備考</th>
          </tr></thead><tbody>${trs}</tbody></table>
        </div>`)
    }

    const stockRows = stockList.map((r: { supplier_name?: string; material_name?: string; current_stock?: number }) =>
      `<tr><td>${escapeHtml(String(r.supplier_name ?? ''))}</td><td>${escapeHtml(String(r.material_name ?? ''))}</td><td>${r.current_stock ?? ''}</td></tr>`
    ).join('')
    const stockSubRows = stockSubList.map(
      (r: { supplier_name?: string; material_name?: string; order_bundle_quantity?: number }) =>
        `<tr><td>${escapeHtml(String(r.supplier_name ?? ''))}</td><td>${escapeHtml(String(r.material_name ?? ''))}</td><td>${r.order_bundle_quantity ?? ''}</td></tr>`
    ).join('')

    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>切断計画リスト</title><style>
      @page { size: A4 portrait; margin: 8mm; }
      body { font-family: 'MS Gothic', 'Yu Gothic', sans-serif; font-size: 10px; margin: 0; padding: 6px; }
      .print-layout { display: flex; gap: 12px; width: 100%; min-height: 100vh; box-sizing: border-box; }
      .print-left { flex: 1; min-width: 0; }
      .print-right { width: 220px; flex-shrink: 0; display: flex; flex-direction: column; gap: 12px; }
      .print-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 6px; font-size: 14px; border-bottom: 1px solid #333; }
      .print-header-row .print-title { font-weight: bold; }
      .print-header-row .print-date { }
      .print-cut-block { margin-bottom: 10px; break-inside: avoid; }
      .print-cut-block-title { font-weight: bold; margin-bottom: 4px; font-size: 11px; }
      .print-cut-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
      .print-cut-table th, .print-cut-table td { border: 1px solid #333; padding: 4px 2px; text-align: center; font-size: 11px; line-height: 1.2; }
      .print-cut-table th { background: #f0f0f0; }
      .print-cut-table th:nth-child(1), .print-cut-table td:nth-child(1) { width: 8%; }
      .print-cut-table th:nth-child(2), .print-cut-table td:nth-child(2) { width: 18%; }
      .print-cut-table th:nth-child(3), .print-cut-table td:nth-child(3) { width: 19%; }
      .print-cut-table th:nth-child(4), .print-cut-table td:nth-child(4) { width: 6%; }
      .print-cut-table th:nth-child(5), .print-cut-table td:nth-child(5) { width: 8%; }
      .print-cut-table th:nth-child(6), .print-cut-table td:nth-child(6) { width: 6%; }
      .print-cut-table th:nth-child(7), .print-cut-table td:nth-child(7) { width: 8%; }
      .print-cut-table th:nth-child(8), .print-cut-table td:nth-child(8) { width: 12%; }
      .print-cut-table td:nth-child(2), .print-cut-table td:nth-child(3), .print-cut-table td:nth-child(8) { text-align: left; }
      .print-stock-section { break-inside: avoid; }
      .print-stock-section h3 { margin: 0 0 6px; font-size: 11px; }
      .print-stock-table { width: 100%; border-collapse: collapse; font-size: 10px; table-layout: fixed; }
      .print-stock-table th, .print-stock-table td { border: 1px solid #333; padding: 2.5px 4px; line-height: 1.44; }
      .print-stock-table th { background: #f0f0f0; }
      .print-stock-table th:nth-child(1), .print-stock-table td:nth-child(1) { width: 40%; }
      .print-stock-table th:nth-child(2), .print-stock-table td:nth-child(2) { width: 46%; text-align: center;}
      .print-stock-table th:nth-child(3), .print-stock-table td:nth-child(3) { width: 16%; text-align: center; }
      @media print { .print-layout { min-height: auto; } }
    </style></head><body>
      <div class="print-header-row"><span class="print-title">切断計画リスト</span><span class="print-date">生産日 ${escapeHtml(dayDisplay)}</span></div>
      <div class="print-layout">
        <div class="print-left">${leftBlocks.join('')}</div>
        <div class="print-right">
          <div class="print-stock-section">
            <h3>材料在庫</h3>
            <table class="print-stock-table"><thead><tr><th>仕入先</th><th>材料名</th><th>在庫</th></tr></thead><tbody>${stockRows || '<tr><td colspan="3">-</td></tr>'}</tbody></table>
          </div>
          <div class="print-stock-section">
            <h3>材料バラ在庫</h3>
            <table class="print-stock-table"><thead><tr><th>仕入先</th><th>材料名</th><th>在庫</th></tr></thead><tbody>${stockSubRows || '<tr><td colspan="3">-</td></tr>'}</tbody></table>
          </div>
        </div>
      </div>
    </body></html>`

    const w = window.open('', '_blank')
    if (!w) {
      ElMessage.warning('弹窗被拦截，请允许弹窗后重试')
      return
    }
    w.document.write(html)
    w.document.close()
    w.focus()
    setTimeout(() => { w.print(); w.close() }, 300)
    ElMessage.success('印刷用ウィンドウを開きました')
  } catch (e) {
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '印刷データの取得に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    printCuttingPlanLoading.value = false
  }
}

async function issueCuttingInstructionSheet() {
  const day = selectedDateToday.value ? String(selectedDateToday.value).slice(0, 10) : ''
  if (!day) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  issueCuttingInstructionSheetLoading.value = true
  try {
    const res = await request.get<{ success?: boolean; data?: CuttingManagementRow[] }>(
      '/api/plan/cutting-management/list',
      { params: { production_day: day, limit: 2000 } }
    )
    const rows = (res as any)?.success ? ((res as any).data ?? []) as CuttingManagementRow[] : []
    const byMachine = new Map<string, CuttingManagementRow[]>()
    for (const r of rows) {
      const key = (r.cutting_machine || '').trim() || '（未設定）'
      if (!byMachine.has(key)) byMachine.set(key, [])
      byMachine.get(key)!.push(r)
    }
    for (const [, list] of byMachine) {
      list.sort((a, b) => (a.production_sequence ?? 0) - (b.production_sequence ?? 0))
    }
    const dayDisplay = day.replace(/-/g, '/')
    const pages: string[] = []
    const machineNames = Array.from(byMachine.keys()).sort()
    for (const machineName of machineNames) {
      const list = byMachine.get(machineName)!
      let totalQty = 0
      const trs = list.map((r) => {
        const qty = r.actual_production_quantity ?? 0
        totalQty += qty
        return `<tr>
          <td>${escapeHtml(r.cd ?? '')}</td>
          <td>${escapeHtml(r.product_name ?? '')}</td>
          <td>${r.production_sequence ?? ''}</td>
          <td>${escapeHtml(r.material_name ?? '')}</td>
          <td>${r.actual_production_quantity ?? ''}</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
          <td>${escapeHtml(r.remarks ?? '')}</td>
        </tr>`
      }).join('')
      pages.push(`
        <div class="instruction-sheet-page">
          <div class="instruction-sheet-header">
            <span class="instruction-sheet-title">切断生産指示書</span>
            <span class="instruction-sheet-machine">${escapeHtml(machineName)}</span>
            <span class="instruction-sheet-date">生産日 ${dayDisplay}</span>
          </div>
          <div class="instruction-sheet-table-wrap">
            <table class="instruction-sheet-table">
              <thead><tr>
                <th>CD</th><th>製品名</th><th>順位</th><th>原材料</th><th>生産数</th><th>実績数</th><th>不良</th><th>段取</th><th>開始</th><th>終了</th><th>作業者</th><th>備考</th>
              </tr></thead>
              <tbody>${trs}</tbody>
            </table>
          </div>
          <div class="instruction-sheet-footer">
            <span>合計 ${totalQty.toLocaleString()}</span>
          </div>
        </div>
      `)
    }
    if (pages.length === 0) {
      ElMessage.warning('該当日のデータがありません')
      return
    }
    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>切断生産指示書</title><style>
      @page { size: A5 landscape; margin: 10mm 0cm; }
      body { font-family: 'MS Gothic', 'Yu Gothic', sans-serif; font-size: 11px; margin: 0; padding: 8px 0.6cm; }
      .instruction-sheet-page { page-break-after: always; width: 100%; box-sizing: border-box; }
      .instruction-sheet-page:last-child { page-break-after: auto; }
      .instruction-sheet-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 6px 0; border-bottom: 1px solid #999; }
      .instruction-sheet-title { font-weight: bold; font-size: 22px; }
      .instruction-sheet-machine { font-size: 22px; }
      .instruction-sheet-date { font-size: 22px; }
      .instruction-sheet-table-wrap { overflow: auto; }
      .instruction-sheet-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
      .instruction-sheet-table th:nth-child(1), .instruction-sheet-table td:nth-child(1) { width: 4%; }
      .instruction-sheet-table th:nth-child(2), .instruction-sheet-table td:nth-child(2) { width: 15%; }
      .instruction-sheet-table th:nth-child(3), .instruction-sheet-table td:nth-child(3) { width: 4%; }
      .instruction-sheet-table th:nth-child(4), .instruction-sheet-table td:nth-child(4) { width: 15%; }
      .instruction-sheet-table th:nth-child(5), .instruction-sheet-table td:nth-child(5) { width: 5%; }
      .instruction-sheet-table th:nth-child(6), .instruction-sheet-table td:nth-child(6) { width: 5%; }
      .instruction-sheet-table th:nth-child(7), .instruction-sheet-table td:nth-child(7) { width: 4%; }
      .instruction-sheet-table th:nth-child(8), .instruction-sheet-table td:nth-child(8) { width: 4%; }
      .instruction-sheet-table th:nth-child(9), .instruction-sheet-table td:nth-child(9) { width: 4%; }
      .instruction-sheet-table th:nth-child(10), .instruction-sheet-table td:nth-child(10) { width: 4%; }
      .instruction-sheet-table th:nth-child(11), .instruction-sheet-table td:nth-child(11) { width: 5%; }
      .instruction-sheet-table th:nth-child(12), .instruction-sheet-table td:nth-child(12) { width: 10%; }
      .instruction-sheet-table th, .instruction-sheet-table td { border: 1px solid #999; padding: 3px 7px; text-align: center; line-height: 1.8; }
      .instruction-sheet-table th { background: #fff; font-weight: bold; font-size: 10px; }
      .instruction-sheet-table td { font-size: 14px; }
      .instruction-sheet-table td:nth-child(1), .instruction-sheet-table td:nth-child(12) { font-size: 10px; }
      .instruction-sheet-table th:nth-child(12), .instruction-sheet-table td:nth-child(12) { color: #d00; }
      .instruction-sheet-table td:nth-child(2), .instruction-sheet-table td:nth-child(4), .instruction-sheet-table td:nth-child(12) { text-align: left; }
      .instruction-sheet-footer { margin-top: 12px; padding-top: 8px; display: flex; justify-content: flex-end; gap: 24px; font-weight: bold; }
      @media print {
        .instruction-sheet-page { overflow: hidden; }
      }
    </style></head><body>${pages.join('')}</body></html>`
    const w = window.open('', '_blank')
    if (!w) {
      ElMessage.warning('ポップアップがブロックされています。印刷用ウィンドウを許可してください。')
      return
    }
    w.document.write(html)
    w.document.close()
    w.focus()
    setTimeout(() => { w.print(); w.close() }, 300)
    ElMessage.success('指示書を印刷ウィンドウで開きました')
  } catch (e) {
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '指示書の取得に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    issueCuttingInstructionSheetLoading.value = false
  }
}

/** 面取計画リスト印刷：指定日の各面取機データ（A4縦・余白小・样式参考切断計画） */
const printChamferingPlanLoading = ref(false)
async function printChamferingPlanList() {
  const day = selectedChamferingDateToday.value ? String(selectedChamferingDateToday.value).slice(0, 10) : ''
  if (!day) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  printChamferingPlanLoading.value = true
  try {
    const res = await request.get<{ success?: boolean; data?: ChamferingManagementRow[] }>(
      '/api/plan/chamfering-management/list',
      { params: { production_day: day, limit: 2000 } }
    )
    const rows = (res as any)?.success ? ((res as any).data ?? []) as ChamferingManagementRow[] : []
    const byMachine = new Map<string, ChamferingManagementRow[]>()
    for (const r of rows) {
      const key = (r.chamfering_machine || '').trim() || '（未設定）'
      if (!byMachine.has(key)) byMachine.set(key, [])
      byMachine.get(key)!.push(r)
    }
    for (const [, list] of byMachine) {
      list.sort((a, b) => (a.production_sequence ?? 0) - (b.production_sequence ?? 0))
    }
    const machineNames = Array.from(byMachine.keys()).sort()
    const dayDisplay = day.replace(/-/g, '/')
    const blocks: string[] = []
    for (const machineName of machineNames) {
      const list = byMachine.get(machineName)!
      const trs = list.map((r) => {
        const noCountDisplay = r.no_count ? 'Yes' : 'No'
        return `
        <tr>
          <td>${escapeHtml(String(r.cd ?? r.management_code ?? ''))}</td>
          <td>${escapeHtml(String(r.product_name ?? ''))}</td>
          <td>${r.production_sequence ?? ''}</td>
          <td>${r.actual_production_quantity ?? ''}</td>
          <td>${noCountDisplay}</td>
          <td>${r.production_time ?? ''}</td>
          <td>${escapeHtml(String(r.production_line ?? ''))}</td>
        </tr>`
      }).join('')
      blocks.push(`
        <div class="print-chamfer-block">
          <div class="print-chamfer-block-title">${escapeHtml(machineName)}</div>
          <table class="print-chamfer-table"><thead><tr>
            <th>コード</th><th>製品名</th><th>順位</th><th>生産数</th><th>カ無</th><th>時間</th><th>ライン</th>
          </tr></thead><tbody>${trs}</tbody></table>
        </div>`)
    }
    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>面取計画リスト</title><style>
      @page { size: A4 portrait; margin: 8mm; }
      body { font-family: 'MS Gothic', 'Yu Gothic', sans-serif; font-size: 10px; margin: 0; padding: 6px; }
      .print-chamfer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 6px; font-size: 14px; border-bottom: 1px solid #333; }
      .print-chamfer-header .print-title { font-weight: bold; }
      .print-chamfer-body { display: flex; flex-wrap: wrap; gap: 12px 16px; width: 100%; }
      .print-chamfer-block { width: calc(50% - 8px); min-width: 280px; break-inside: avoid; margin-bottom: 4px; }
      .print-chamfer-block-title { font-weight: bold; margin-bottom: 4px; font-size: 11px; }
      .print-chamfer-table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 10px; }
      .print-chamfer-table th, .print-chamfer-table td { border: 1px solid #333; padding: 4px 2px; text-align: center; line-height: 1.2; }
      .print-chamfer-table th { background: #f0f0f0; font-size: 11px; }
      .print-chamfer-table th:nth-child(1), .print-chamfer-table td:nth-child(1) { width: 11%; }
      .print-chamfer-table th:nth-child(2), .print-chamfer-table td:nth-child(2) { width: 20%; }
      .print-chamfer-table th:nth-child(3), .print-chamfer-table td:nth-child(3) { width: 8%; }
      .print-chamfer-table th:nth-child(4), .print-chamfer-table td:nth-child(4) { width: 11%; }
      .print-chamfer-table th:nth-child(5), .print-chamfer-table td:nth-child(5) { width: 8%; }
      .print-chamfer-table th:nth-child(6), .print-chamfer-table td:nth-child(6) { width: 8%; }
      .print-chamfer-table th:nth-child(7), .print-chamfer-table td:nth-child(7) { width: 16%;text-align: center; }
      .print-chamfer-table td:nth-child(2) { text-align: left; }
      .print-chamfer-table td:nth-child(7) { text-align: left; }
      @media print { .print-chamfer-block { break-inside: avoid; } }
    </style></head><body>
      <div class="print-chamfer-header"><span class="print-title">面取計画リスト</span><span class="print-date">生産日 ${escapeHtml(dayDisplay)}</span></div>
      <div class="print-chamfer-body">${blocks.join('')}</div>
    </body></html>`
    const w = window.open('', '_blank')
    if (!w) {
      ElMessage.warning('弹窗被拦截，请允许弹窗后重试')
      return
    }
    w.document.write(html)
    w.document.close()
    w.focus()
    setTimeout(() => { w.print(); w.close() }, 300)
    ElMessage.success('印刷用ウィンドウを開きました')
  } catch (e) {
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '印刷データの取得に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    printChamferingPlanLoading.value = false
  }
}

/** 面取指示書発行：指定日の今日分を面取機ごとに1ページずつ A5 横向で印刷 */
const issueChamferingInstructionSheetLoading = ref(false)
async function issueChamferingInstructionSheet() {
  const day = selectedChamferingDateToday.value ? String(selectedChamferingDateToday.value).slice(0, 10) : ''
  if (!day) {
    ElMessage.warning('生産日を選択してください')
    return
  }
  issueChamferingInstructionSheetLoading.value = true
  try {
    // 指示書発行は選択日の全面取機を対象とする（当前面取機筛选に依存しない）
    const params: Record<string, string> = { production_day: day, limit: '2000' }
    const res = await request.get<{ success?: boolean; data?: ChamferingManagementRow[] }>(
      '/api/plan/chamfering-management/list',
      { params }
    )
    const rows = (res as any)?.success ? ((res as any).data ?? []) as ChamferingManagementRow[] : []
    const byMachine = new Map<string, ChamferingManagementRow[]>()
    for (const r of rows) {
      const key = (r.chamfering_machine || '').trim() || '（未設定）'
      if (!byMachine.has(key)) byMachine.set(key, [])
      byMachine.get(key)!.push(r)
    }
    for (const [, list] of byMachine) {
      list.sort((a, b) => (a.production_sequence ?? 0) - (b.production_sequence ?? 0))
    }
    const dayDisplay = day.replace(/-/g, '/')
    const pages: string[] = []
    const machineNames = Array.from(byMachine.keys()).sort()
    for (const machineName of machineNames) {
      const list = byMachine.get(machineName)!
      let totalQty = 0
      const trs = list.map((r) => {
        const qty = r.actual_production_quantity ?? 0
        totalQty += qty
        const noCountDisplay = r.no_count ? 'あり' : '--'
        return `<tr>
          <td>${escapeHtml(r.cd ?? r.management_code ?? '')}</td>
          <td>${escapeHtml(r.production_line ?? '')}</td>
          <td>${escapeHtml(r.product_name ?? '')}</td>
          <td>${r.production_sequence ?? ''}</td>
          <td>${r.actual_production_quantity ?? ''}</td>
          <td></td>
          <td>${noCountDisplay}</td>
          <td></td>
          <td></td>
          <td></td>
          <td></td>
        </tr>`
      }).join('')
      pages.push(`
        <div class="instruction-sheet-page">
          <div class="instruction-sheet-header">
            <span class="instruction-sheet-title">面取生産指示書</span>
            <span class="instruction-sheet-machine">${escapeHtml(machineName)}</span>
            <span class="instruction-sheet-date">生産日 ${dayDisplay}</span>
          </div>
          <div class="instruction-sheet-table-wrap">
            <table class="instruction-sheet-table chamfering-sheet-table">
              <thead><tr>
                <th>CD</th><th>ライン</th><th>製品名</th><th>順位</th><th>計画数</th><th>実績数</th><th>カ無</th><th>運転時間</th><th>停止時間</th><th>1直</th><th>2直</th>
              </tr></thead>
              <tbody>${trs}</tbody>
            </table>
          </div>
          <div class="instruction-sheet-footer">
            <span>合計 ${totalQty.toLocaleString()}</span>
          </div>
        </div>
      `)
    }
    if (pages.length === 0) {
      ElMessage.warning('該当日のデータがありません')
      return
    }
    const html = `<!DOCTYPE html><html><head><meta charset="UTF-8"><title>面取生産指示書</title><style>
      @page { size: A5 landscape; margin: 10mm 0cm; }
      body { font-family: 'MS Gothic', 'Yu Gothic', sans-serif; font-size: 11px; margin: 0; padding: 8px 0.6cm; }
      .instruction-sheet-page { page-break-after: always; width: 100%; box-sizing: border-box; }
      .instruction-sheet-page:last-child { page-break-after: auto; }
      .instruction-sheet-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 6px 0; border-bottom: 1px solid #999; }
      .instruction-sheet-title { font-weight: bold; font-size: 22px; }
      .instruction-sheet-machine { font-size: 22px; }
      .instruction-sheet-date { font-size: 22px; }
      .instruction-sheet-table-wrap { overflow: auto; }
      .instruction-sheet-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
      .chamfering-sheet-table th:nth-child(1), .chamfering-sheet-table td:nth-child(1) { width: 6%; }
      .chamfering-sheet-table th:nth-child(2), .chamfering-sheet-table td:nth-child(2) { width: 7%; }
      .chamfering-sheet-table th:nth-child(3), .chamfering-sheet-table td:nth-child(3) { width: 18%; }
      .chamfering-sheet-table th:nth-child(4), .chamfering-sheet-table td:nth-child(4) { width: 5%; }
      .chamfering-sheet-table th:nth-child(5), .chamfering-sheet-table td:nth-child(5) { width: 6%; }
      .chamfering-sheet-table th:nth-child(6), .chamfering-sheet-table td:nth-child(6) { width: 6%; }
      .chamfering-sheet-table th:nth-child(7), .chamfering-sheet-table td:nth-child(7) { width: 5%; }
      .chamfering-sheet-table th:nth-child(8), .chamfering-sheet-table td:nth-child(8) { width: 8%; }
      .chamfering-sheet-table th:nth-child(9), .chamfering-sheet-table td:nth-child(9) { width: 8%; }
      .chamfering-sheet-table th:nth-child(10), .chamfering-sheet-table td:nth-child(10) { width: 8%; }
      .chamfering-sheet-table th:nth-child(11), .chamfering-sheet-table td:nth-child(11) { width: 8%; }
      .instruction-sheet-table th, .instruction-sheet-table td { border: 1px solid #999; padding: 3px 7px; text-align: center; line-height: 1.8; }
      .instruction-sheet-table th { background: #fff; font-weight: bold; font-size: 11px; }
      .instruction-sheet-table td { font-size: 14px; }
      .chamfering-sheet-table td:nth-child(1), .chamfering-sheet-table td:nth-child(2), .chamfering-sheet-table td:nth-child(3) { font-size: 14px; text-align: left; }
      .instruction-sheet-footer { margin-top: 12px; padding-top: 8px; display: flex; justify-content: flex-end; gap: 24px; font-weight: bold; }
      @media print { .instruction-sheet-page { overflow: hidden; } }
    </style></head><body>${pages.join('')}</body></html>`
    const w = window.open('', '_blank')
    if (!w) {
      ElMessage.warning('ポップアップがブロックされています。印刷用ウィンドウを許可してください。')
      return
    }
    w.document.write(html)
    w.document.close()
    w.focus()
    setTimeout(() => { w.print(); w.close() }, 300)
    ElMessage.success('指示書を印刷ウィンドウで開きました')
  } catch (e) {
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '指示書の取得に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    issueChamferingInstructionSheetLoading.value = false
  }
}

function escapeHtml(s: string): string {
  const div = document.createElement('div')
  div.textContent = s
  return div.innerHTML
}

function onProductionDayEditorKeydown(e: KeyboardEvent) {
  if (e.key !== 'Escape') return
  if (editingProductionDayId.value != null) {
    cancelEditProductionDay()
  }
  if (editingChamferingProductionDayId.value != null) {
    cancelEditChamferingProductionDay()
  }
}

onMounted(() => {
  loadMachineOptions()
  loadCuttingMachineOptions()
  loadChamferingMachineOptions()
  loadScheduleMonths()
  loadPlans()
  loadCuttingManagement()
  loadChamferingManagement()
  loadChamferingBatchList()
  loadKanbanProductNames()
  loadKanbanIssuance()
  window.addEventListener('keydown', onProductionDayEditorKeydown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onProductionDayEditorKeydown)
})
</script>
 
<style scoped>
/* ========== 主题色变量 ========== */
.cutting-instruction-container {
  --cutting-accent: #4f46e5;
  --cutting-bg: rgba(79, 70, 229, 0.06);
  --chamfering-accent: #059669;
  --chamfering-bg: rgba(5, 150, 105, 0.06);
  --kanban-accent: #d97706;
  --kanban-bg: rgba(217, 119, 6, 0.06);
  --batch-accent: #2563eb;
  --batch-bg: rgba(37, 99, 235, 0.06);
}

.cutting-instruction-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 20px 24px;
  background: linear-gradient(160deg, #f0f4ff 0%, #f8fafc 35%, #f1f5f9 100%);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px 24px;
  background: linear-gradient(135deg, #ffffff 0%, #fafbff 100%);
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.06), 0 2px 4px -2px rgba(79, 70, 229, 0.04);
}

.page-header-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: #4f46e5;
  background: rgba(79, 70, 229, 0.12);
  padding: 4px 10px;
  border-radius: 6px;
  margin-bottom: 8px;
  letter-spacing: 0.04em;
}

.header-title h1 {
  font-size: 22px;
  font-weight: 700;
  color: #1e1b4b;
  margin: 0;
  letter-spacing: -0.03em;
  line-height: 1.3;
}

.header-title .header-desc {
  font-size: 13px;
  color: #64748b;
  margin: 8px 0 0 0;
  font-weight: 400;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-right .done-list-btn {
  height: 30px;
  padding: 0 14px;
  border-radius: 999px;
  border-width: 1px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}
.header-right .done-list-btn:hover {
  transform: translateY(-1px);
  filter: saturate(1.06);
}
.header-right .done-list-btn:active {
  transform: translateY(0);
}
.header-right .done-list-btn:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.45);
  outline-offset: 1px;
}

.header-right .done-list-btn--cutting {
  border-color: #2563eb;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 55%, #1d4ed8 100%);
  box-shadow: 0 8px 18px -8px rgba(37, 99, 235, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.28);
}
.header-right .done-list-btn--cutting:hover {
  box-shadow: 0 12px 22px -10px rgba(37, 99, 235, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.header-right .done-list-btn--chamfering {
  border-color: #059669;
  background: linear-gradient(135deg, #10b981 0%, #059669 55%, #047857 100%);
  box-shadow: 0 8px 18px -8px rgba(5, 150, 105, 0.72), inset 0 1px 0 rgba(255, 255, 255, 0.26);
}
.header-right .done-list-btn--chamfering:hover {
  box-shadow: 0 12px 22px -10px rgba(5, 150, 105, 0.78), inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.plan-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
  align-items: stretch;
}

.plan-section-left {
  flex: 6 1 0;
  min-width: 0;
}

.plan-section-right {
  flex: 4 1 0;
  min-width: 0;
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

/* 右侧製品情報容器：与生産ロット一覧（左列）同高で stretch。左：右＝6：4 を維持 */
.right-panel {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: row;
  gap: 10px;
  background: linear-gradient(135deg, #fafbff 0%, #f8fafc 100%);
  border: 1px solid #e0e7ff;
  border-radius: 12px;
  padding: 12px 14px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.04);
}

/* 同一要素が plan-section-right + right-panel のため、列幅は 6:4 を強制（.right-panel の flex:1 で上書きされないように） */
.plan-row > .plan-section-right.right-panel {
  flex: 3.65 1 0;
}

.right-panel-top,
.right-panel-bottom {
  flex: 1 1 0;
  min-width: 0;
  background: #fff;
  border: 1px solid #eef2ff;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.chamfering-right-panel {
  background: linear-gradient(135deg, #f0fdf4 0%, #f8fafc 100%);
  border-color: #d1fae5;
}

.chamfering-right-panel .right-panel-top,
.chamfering-right-panel .right-panel-bottom {
  border-color: #d1fae5;
}

.right-panel-top {
  min-height: 0;
}

.right-panel-bottom {
  min-height: 0;
}

.right-panel-title {
  font-size: 12px;
  font-weight: 700;
  color: #334155;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e2e8f0;
}

.chamfering-right-panel .right-panel-title {
  color: #047857;
  border-bottom-color: #d1fae5;
}

.right-panel-placeholder {
  font-size: 11px;
  color: #94a3b8;
  padding: 8px 0;
}

.product-detail-body {
  flex: 1;
  overflow-y: auto;
  font-size: 11px;
}

/* 製品情報：列表式（1行1項目） */
.product-detail-list {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}
.product-detail-list--chamfering {
  border-color: #bbf7d0;
  background: #f0fdf4;
}
.product-detail-list-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  border-bottom: 1px solid #f1f5f9;
  min-height: 28px;
}
.product-detail-list-item:last-child {
  border-bottom: none;
}
.product-detail-list--chamfering .product-detail-list-item {
  border-bottom-color: #dcfce7;
}
.product-detail-list-item .detail-label {
  flex: 0 0 72px;
  font-size: 11px;
  color: #64748b;
}
.product-detail-list-item .detail-value {
  flex: 1;
  min-width: 0;
  font-size: 11px;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 製品情報カード（旧レイアウト・参照用） */
.product-detail-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.product-detail-card--chamfering {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-color: #bbf7d0;
}
.product-detail-header {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-bottom: 10px;
  margin-bottom: 10px;
  border-bottom: 1px solid #e2e8f0;
}
.product-detail-card--chamfering .product-detail-header {
  border-bottom-color: #bbf7d0;
}
.product-detail-cd {
  font-size: 11px;
  font-weight: 600;
  color: #475569;
  letter-spacing: 0.02em;
}
.product-detail-name {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.35;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}
.product-detail-group {
  margin-bottom: 10px;
}
.product-detail-group:last-child {
  margin-bottom: 0;
}
.product-detail-group-title {
  font-size: 10px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}
.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 12px;
}
.detail-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  min-width: 0;
}
.detail-label {
  flex: 0 0 64px;
  font-size: 10px;
  color: #64748b;
  flex-shrink: 0;
}
.detail-value {
  flex: 1;
  min-width: 0;
  font-size: 11px;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
}
.detail-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 2px 0;
}

.equipment-efficiency-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.equipment-efficiency-body :deep(.el-table),
.equipment-efficiency-body :deep(.efficiency-table) {
  font-size: 11px;
}
.equipment-efficiency-body :deep(.efficiency-table .el-table__header th) {
  background: #f1f5f9;
  color: #475569;
  font-weight: 600;
}
.equipment-efficiency-body :deep(.efficiency-table .el-table__body td) {
  color: #334155;
}
.equipment-efficiency-body :deep(.efficiency-table .el-table__row:hover > td) {
  background-color: #f8fafc !important;
}


.plan-section .section-card {
  border-radius: 12px;
  border: 1px solid #e0e7ff;
  box-shadow: 0 4px 12px -2px rgba(37, 99, 235, 0.1), 0 2px 8px -1px rgba(37, 99, 235, 0.06);
  overflow: hidden;
  border-left: 4px solid var(--batch-accent);
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.plan-section .section-card:hover {
  box-shadow: 0 8px 20px -4px rgba(37, 99, 235, 0.16), 0 4px 12px -2px rgba(37, 99, 235, 0.10);
  transform: translateY(-1px);
}

.plan-section .section-card :deep(.el-card__header) {
  padding: 8px 12px;
  font-size: 13px;
  border-bottom: 1px solid #eef2ff;
  background: linear-gradient(90deg, rgba(37, 99, 235, 0.06) 0%, transparent 100%);
}

.plan-section .section-card :deep(.el-card__body) {
  padding: 8px 12px;
}

/* 下部：第1行＝切断指示（左|右）、第2行＝面取指示|カンバン発行 */
.instruction-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.instruction-row.instruction-two-cols {
  display: flex;
  gap: 12px;
  align-items: stretch;
}

/* 今日|翌日：左右 6:4，区域高度一致且比原高增加 40%（320→448px），表格右侧无 padding/margin，背景纯白 */
.instruction-row.instruction-cols-6-4 .instruction-col:nth-child(1),
.instruction-row.instruction-cols-6-4 .instruction-col:nth-child(2) {
  min-height: 448px;
  padding-right: 6px;
  margin-right: 6px;
  background: #ffffff;
}
/* 今日 59% : 翌日 41%（今日比原 6:4 缩小 1%） */
.instruction-row.instruction-cols-6-4 .instruction-col:nth-child(1) {
  flex: 6.6;
  min-width: 0;
  min-height: 440px;
}
.instruction-row.instruction-cols-6-4 .instruction-col:nth-child(2) {
  flex: 4.1;
  min-width: 0;
  min-height: 440px;
}

.instruction-row .instruction-col {
  flex: 1;
  min-width: 0;
  min-height: 240px;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  transition: shadow 0.25s ease, transform 0.25s ease, background 0.2s ease;
}
.instruction-row .instruction-col.instruction-col-full {
  flex: 1 1 100%;
}

/* 面取指示-今日・翌日：容器高さは切断指示-今日と同じ（448px） */
.chamfering-management-section {
  height: 100%;
  min-height: 448px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #ffffff 0%, #f9fefb 100%);
}

.kanban-issuance-section {
  height: 100%;
  min-height: 260px;
  display: flex;
  flex-direction: column;
}

.cutting-management-section {
  height: 100%;
  min-height: 448px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  border-left: 4px solid var(--cutting-accent);
  border-color: #e0e7ff;
  box-shadow: 0 4px 12px -2px rgba(79, 70, 229, 0.1), 0 2px 8px -1px rgba(79, 70, 229, 0.06);
  border-radius: 10px;
  transition: box-shadow 0.25s ease;
}

.cutting-management-section:hover {
  box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.15), 0 4px 12px -2px rgba(79, 70, 229, 0.10);
}

.cutting-management-section .cutting-mgmt-header {
  padding: 6px 0 10px;
  margin-bottom: 6px;
  border-bottom: 1px solid #eef2ff;
}

.instruction-col.chamfering-management-section {
  border-left: 4px solid var(--chamfering-accent);
  border-color: #d1fae5;
  box-shadow: 0 4px 12px -2px rgba(5, 150, 105, 0.1), 0 2px 8px -1px rgba(5, 150, 105, 0.06);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  border-radius: 10px;
}
.instruction-col.chamfering-management-section:hover {
  box-shadow: 0 8px 20px -4px rgba(5, 150, 105, 0.16), 0 4px 12px -2px rgba(5, 150, 105, 0.10);
  transform: translateY(-1px);
}

.instruction-col.chamfering-management-section .cutting-mgmt-header {
  border-bottom-color: #d1fae5;
  padding: 4px 0 6px;
  margin-bottom: 4px;
}

.instruction-col.kanban-issuance-section {
  border-left: 4px solid var(--kanban-accent);
  border-color: #ffedd5;
  box-shadow: 0 4px 12px -2px rgba(217, 119, 6, 0.1), 0 2px 8px -1px rgba(217, 119, 6, 0.06);
  transition: box-shadow 0.25s ease;
  background: linear-gradient(135deg, #ffffff 0%, #fffbeb 100%);
  border-radius: 10px;
}

.instruction-col.kanban-issuance-section:hover {
  box-shadow: 0 8px 20px -4px rgba(217, 119, 6, 0.15), 0 4px 12px -2px rgba(217, 119, 6, 0.10);
}

.instruction-col.kanban-issuance-section .cutting-mgmt-header {
  border-bottom-color: #ffedd5;
}

.kanban-pagination {
  margin-top: 10px;
  justify-content: flex-end;
}

.cutting-mgmt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
  gap: 8px;
}
/* 切断指示-今日：左側＝标题+日期+切断機 横並び、右側＝指示書発行・実績確定 */
.cutting-mgmt-header-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  min-width: 0;
}
.cutting-mgmt-header-right {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
/* 切断指示-今日：右側3按钮 间距缩小・样式统一・颜色区分 */
.cutting-mgmt-header-actions {
  gap: 4px;
}
.cutting-mgmt-header-actions :deep(.el-button) {
  margin: 0;
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 6px;
  min-height: 28px;
  transition: opacity 0.2s, box-shadow 0.2s;
}
.cutting-mgmt-header-actions :deep(.el-button:hover) {
  opacity: 0.92;
}
/* 計画印刷：灰底描边，次要操作 */
.cutting-mgmt-header-actions :deep(.el-button--default) {
  color: #ffffff;
  border-color: #c0c4cc;
  background-color: #e49604;
}
.cutting-mgmt-header-actions :deep(.el-button--default:hover) {
  color: #409eff;
  border-color: #b3d8ff;
  background-color: #ecf5ff;
}
/* 指示書発行：蓝色主按钮 */
.cutting-mgmt-header-actions :deep(.el-button--primary) {
  color: #fff;
  border-color: #409eff;
  background-color: #409eff;
  font-weight: 500;
}
.cutting-mgmt-header-actions :deep(.el-button--primary:hover) {
  border-color: #66b1ff;
  background-color: #66b1ff;
}
/* 実績確定：绿色成功按钮 */
.cutting-mgmt-header-actions :deep(.el-button--success) {
  color: #fff;
  border-color: #67c23a;
  background-color: #67c23a;
  font-weight: 500;
}
.cutting-mgmt-header-actions :deep(.el-button--success:hover) {
  border-color: #85ce61;
  background-color: #85ce61;
}

/* 面取指示-今日：第一排＝标题左、日期在标题右侧、指示書発行・実績確定最右侧；第二排＝面取機按钮居中 */
.chamfering-mgmt-header-two-rows {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  align-self: stretch;
}
.chamfering-mgmt-header-two-rows .chamfering-mgmt-header-row1 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: nowrap;
  gap: 8px;
  width: 100%;
}
.chamfering-mgmt-header-two-rows .chamfering-mgmt-header-row1 .cutting-mgmt-header-left {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.chamfering-mgmt-header-two-rows .chamfering-mgmt-header-row1 .cutting-mgmt-header-right {
  flex: 0 0 auto;
  margin-left: auto;
}
.chamfering-mgmt-header-two-rows .chamfering-mgmt-header-row2 {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 2px 0;
  border-top: 1px solid rgba(5, 150, 105, 0.08);
}
.chamfering-mgmt-header-two-rows .chamfering-mgmt-header-row2 .chamfering-machine-btns {
  margin-right: 0;
}

.cutting-mgmt-drop-hint {
  font-size: 11px;
  color: #3b82f6;
  padding: 6px 8px;
  margin-bottom: 6px;
  background: #eff6ff;
  border-radius: 4px;
  border: 1px dashed #3b82f6;
}

.chamfering-mgmt-drop-wrap {
  position: relative;
}

.chamfering-drag-handle {
  cursor: grab;
  color: #94a3b8;
  font-size: 14px;
}
.chamfering-drag-handle:active {
  cursor: grabbing;
}

.cutting-mgmt-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.02em;
}

.cutting-management-section .cutting-mgmt-title {
  color: #3730a3;
}

.chamfering-management-section .cutting-mgmt-title {
  color: #047857;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.01em;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.chamfering-management-section .cutting-mgmt-title::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 14px;
  border-radius: 2px;
  background: linear-gradient(180deg, #10b981 0%, #059669 100%);
  flex-shrink: 0;
}

.kanban-issuance-section .cutting-mgmt-title {
  color: #b45309;
}

.cutting-mgmt-date-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-right: 8px;
}
/* 生産日：组件根与内部 el-date-editor 均需限制宽度，用 :deep 穿透 + !important 覆盖 EP 默认 */
.cutting-mgmt-date-wrap :deep(.cutting-mgmt-date-picker),
.cutting-mgmt-date-wrap :deep(.el-date-editor) {
  width: 103px !important;
  min-width: 103px !important;
  max-width: 103px !important;
}
.cutting-mgmt-date-wrap :deep(.el-date-editor .el-input__wrapper) {
  padding-left: 8px;
  padding-right: 8px;
}

.cutting-mgmt-machine-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
  margin-right: 6px;
}
.cutting-mgmt-machine-btns :deep(.el-button) {
  min-height: 24px;
  padding: 2px 8px;
  font-size: 11px;
}
.cutting-mgmt-machine-btns :deep(.el-button + .el-button) {
  margin-left: 0;
}

.cutting-mgmt-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

/* 切断指示：表形式（ヘッダ固定・データ行）、高さ 40% 増（320→448px）。
   面取指示と同様に、カード高さ固定＋ヘッダ固定＋内容区域のみスクロール＋合計行固定下部。 */
.cutting-management-section .cutting-mgmt-table-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  max-height: 448px;
  position: relative;
  overflow-y: hidden;
  overflow-x: hidden;
}

.cutting-management-section .cutting-mgmt-h-scroll {
  flex: 1;
  min-height: 0;
  width: 100%;
  overflow-x: auto;
  overflow-y: auto;
}

.cutting-management-section .cutting-mgmt-table-inner {
  overflow: visible;
  flex: 0 0 auto;
}

/* 面取指示-今日・翌日：表ラップの高さを切断指示と同じ（448px）に統一 */
.cutting-mgmt-table-inner {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-gutter: stable;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
}

.cutting-management-section .cutting-mgmt-table-inner {
  border-color: #c7d2fe;
}

.chamfering-management-section .cutting-mgmt-table-inner {
  border-color: #a7f3d0;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(5, 150, 105, 0.06);
}

/* 面取指示：卡片高度固定，表头固定，内容区域可滚动，合計行固定在卡片底部 */
.chamfering-management-section .cutting-mgmt-table-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  max-height: 448px;
  position: relative;
  overflow-y: hidden;
  overflow-x: hidden;
}

.chamfering-management-section .cutting-mgmt-table-inner {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: auto;
}

.cutting-mgmt-thead {
  flex-shrink: 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 10;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}
.cutting-management-section .cutting-mgmt-thead {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border-bottom-color: #c7d2fe;
  box-shadow: 0 3px 6px rgba(79, 70, 229, 0.06);
}

.cutting-management-section .cutting-mgmt-thead .cutting-mgmt-tr {
  color: #3730a3;
  font-weight: 800;
}

.chamfering-management-section .cutting-mgmt-thead {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
  border-bottom: 2px solid #6ee7b7;
  z-index: 10;
  backdrop-filter: blur(4px);
  box-shadow: 0 3px 6px rgba(5, 150, 105, 0.08);
}

.chamfering-management-section .cutting-mgmt-thead .cutting-mgmt-tr {
  color: #047857;
  font-size: 10.5px;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: none;
}

/* ロット→切断のドロップゾーン（切断指示-今日/翌日：縦スクロールは wrap で行うためここでは高さは内容に合わせる） */
.cutting-mgmt-tbody-drop-zone {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
  border-radius: 0 0 6px 6px;
}
.cutting-management-section .cutting-mgmt-tbody-drop-zone {
  height: auto;
  min-height: 0;
  overflow: visible;
}
.cutting-mgmt-tbody-drop-zone.drop-zone-active {
  border-radius: 0 0 5px 5px;
  box-shadow: inset 0 0 0 2px #3b82f6;
}
.cutting-mgmt-tbody-drop-zone .cutting-mgmt-drop-hint {
  flex-shrink: 0;
}
.cutting-mgmt-tbody-drop-zone .cutting-mgmt-tbody {
  flex: 1;
  min-height: 0;
}

.cutting-mgmt-tbody {
  flex: 1;
  min-height: 0;
}

/* 切断指示-今日：表下の合計行（表格外、下方） */
.cutting-mgmt-tfoot-wrap {
  flex-shrink: 0;
  width: 100%;
}
.cutting-mgmt-tfoot {
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
}
/* 合計行：生産数合計・不良合計・生産時間合計（字段不对齐，仅展示三项合计） */
.cutting-mgmt-tfoot-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px 24px;
}
.cutting-mgmt-tfoot-summary .cutting-mgmt-tfoot-item {
  white-space: nowrap;
  color: #475569;
}

/* 表头下・表尾上的放置区：拖到第一位/最后位 */
.cutting-mgmt-drop-edge {
  flex-shrink: 0;
  min-height: 8px;
  width: 100%;
}

.cutting-mgmt-tr {
  display: flex;
  align-items: center;
  min-width: 795px;
  width: 100%;
  font-size: 11px;
}

.cutting-mgmt-thead .cutting-mgmt-tr {
  font-weight: 600;
  color: #475569;
  box-sizing: border-box;
}

.cutting-mgmt-th,
.cutting-mgmt-td {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-right: 1px solid #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  box-sizing: border-box;
}

.cutting-mgmt-th:last-child,
.cutting-mgmt-td:last-child {
  border-right: none;
}

/* 切断指示-今日：13列 min-width 795px */
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-tr {
  min-width: 795px;
}

/* 13列: CD, ライン, 生産日, 切断機, 製品名, 原材料, 生産数, 不良, 完了, 生産順, 生産時間, 備考, 操作 */
.cutting-mgmt-th:nth-child(1),
.cutting-mgmt-td:nth-child(1) { flex: 0 0 42px; }
.cutting-mgmt-th:nth-child(2),
.cutting-mgmt-td:nth-child(2) { flex: 0 0 46px; }
.cutting-mgmt-th:nth-child(3),
.cutting-mgmt-td:nth-child(3) { flex: 0 0 75px; }
.cutting-mgmt-th:nth-child(4),
.cutting-mgmt-td:nth-child(4) { flex: 0 0 46px; }
.cutting-mgmt-th:nth-child(5),
.cutting-mgmt-td:nth-child(5) { flex: 1 1 0; min-width: 60px; }
.cutting-mgmt-th:nth-child(6),
.cutting-mgmt-td:nth-child(6) { flex: 0 0 100px; }
.cutting-mgmt-th:nth-child(7),
.cutting-mgmt-td:nth-child(7) { flex: 0 0 50px; }
.cutting-mgmt-th:nth-child(8),
.cutting-mgmt-td:nth-child(8) { flex: 0 0 44px; }
.cutting-mgmt-th:nth-child(9),
.cutting-mgmt-td:nth-child(9) { flex: 0 0 45px; }
.cutting-mgmt-th:nth-child(10),
.cutting-mgmt-td:nth-child(10) { flex: 0 0 46px; }
.cutting-mgmt-th:nth-child(11),
.cutting-mgmt-td:nth-child(11) { flex: 0 0 50px; }
.cutting-mgmt-th:nth-child(12),
.cutting-mgmt-td:nth-child(12) { flex: 0 0 75px; }
.cutting-mgmt-th:nth-child(13),
.cutting-mgmt-td:nth-child(13) { flex: 0 0 90px; }

/* 翌日テーブル：8列（CD, 生産日, 切断機, 製品名, 生産数, 不良, 生産順, 生産時間） */
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-tr {
  min-width: 444px;
}
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(1),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(1) { flex: 0 0 41px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(2),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(2) { flex: 0 0 75px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(3),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(3) { flex: 0 0 50px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(4),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(4) { flex: 1 1 0; min-width: 90px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(5),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(5) { flex: 0 0 52px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(6) { flex: 0 0 44px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(7),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(7) { flex: 0 0 52px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(8),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(8) { flex: 0 0 62px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(5),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(7),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(8),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(5),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(7),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(8) {
  justify-content: center;
  text-align: center;
}

/* 面取指示-今日：13列（CD, ライン, 生産日, 面取機, 製品名, 原材料, 生産数, 不良, 完了, カ無, 生産順, 生産時間, 操作） */
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-tr {
  min-width: 772px;
}
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(1),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(1) { flex: 0 0 44px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(2),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(2) { flex: 0 0 48px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(3),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(3) { flex: 0 0 72px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(4),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(4) { flex: 0 0 52px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(5),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(5) { flex: 1 1 0; min-width: 60px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(6),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(6) { flex: 0 0 100px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(7) { flex: 0 0 52px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(8),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(8) { flex: 0 0 44px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(9),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(9) { flex: 0 0 42px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(10),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(10) { flex: 0 0 42px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(11),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(11) { flex: 0 0 44px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(12),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(12) { flex: 0 0 56px; }
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(13),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(13) { flex: 0 0 110px; }

/* 面取指示-翌日：8列（CD, 生産日, 面取機, 製品名, 生産数, 不良, 生産順, 生産時間） */
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-tr {
  min-width: 504px;
}
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(1),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(1) { flex: 0 0 45px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(2),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(2) { flex: 0 0 75px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(3),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(3) { flex: 0 0 55px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(4),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(4) { flex: 1 1 0; min-width: 90px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(5),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(5) { flex: 0 0 55px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(6),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(6) { flex: 0 0 44px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(7) { flex: 0 0 45px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(8),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(8) { flex: 0 0 60px; }
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(5),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(6),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(8),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(5),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(6),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(8) {
  justify-content: center;
  text-align: center;
}

/* 面取指示-今日：生産数(7)、不良(8)、完了(9)、カ無(10)、生産順(11)、生産時間(12)、操作(13) 居中 */
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(8),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(9),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(10),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(11),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(12),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(13),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(8),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(9),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(10),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(11),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(12),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(13) {
  justify-content: center;
  text-align: center;
}

.cutting-mgmt-th-actions,
.cutting-mgmt-td-actions {
  justify-content: center;
  gap: 0;
}

/* 操作列：横向滚动时固定在右侧 */
.cutting-management-section .cutting-mgmt-th-actions,
.cutting-management-section .cutting-mgmt-td-actions,
.chamfering-management-section .cutting-mgmt-th-actions,
.chamfering-management-section .cutting-mgmt-td-actions {
  position: sticky;
  right: 0;
  z-index: 2;
  flex-shrink: 0;
  box-shadow: -2px 0 6px rgba(0, 0, 0, 0.06);
}
.cutting-management-section .cutting-mgmt-thead .cutting-mgmt-th-actions {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
}
.cutting-management-section .cutting-mgmt-td-actions {
  background: #fff;
}
.chamfering-management-section .cutting-mgmt-thead .cutting-mgmt-th-actions {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
}
.chamfering-management-section .cutting-mgmt-td-actions {
  background: #fff;
}

/* ── 面取指示-今日：データ行ホバー効果強化 ── */
.chamfering-management-section .cutting-mgmt-data-row {
  transition: background 0.18s ease, box-shadow 0.18s ease;
  border-bottom: 1px solid #ecfdf5;
}
.chamfering-management-section .cutting-mgmt-data-row:hover {
  background: linear-gradient(90deg, #f0fdf4 0%, #ecfdf5 40%, #ffffff 100%) !important;
  box-shadow: inset 3px 0 0 #10b981;
}
.chamfering-management-section .cutting-mgmt-data-row:nth-child(even) {
  background: rgba(236, 253, 245, 0.35);
}

/* ── 面取指示-今日：合計行スタイル強化 ── */
.chamfering-management-section .cutting-mgmt-tfoot {
  background: linear-gradient(90deg, #ecfdf5 0%, #d1fae5 100%);
  border-top: 2px solid #6ee7b7;
  padding: 6px 10px;
  font-size: 11px;
}
.chamfering-management-section .cutting-mgmt-tfoot-summary .cutting-mgmt-tfoot-item {
  color: #047857;
  font-weight: 700;
  background: rgba(255, 255, 255, 0.65);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

/* ── 面取指示-今日：面取機ボタン美化 ── */
.chamfering-management-section .chamfering-machine-btns :deep(.el-button) {
  border-radius: 6px;
  font-size: 10.5px;
  font-weight: 600;
  padding: 2px 10px;
  min-height: 22px;
  transition: all 0.18s ease;
}
.chamfering-management-section .chamfering-machine-btns :deep(.el-button--primary) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  border-color: #059669 !important;
  color: #fff !important;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.30);
}
.chamfering-management-section .chamfering-machine-btns :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #34d399 0%, #10b981 100%) !important;
  box-shadow: 0 3px 10px rgba(16, 185, 129, 0.40);
  transform: translateY(-1px);
}
.chamfering-management-section .chamfering-machine-btns :deep(.el-button--default) {
  background: #fff !important;
  border-color: #d1fae5 !important;
  color: #047857 !important;
}
.chamfering-management-section .chamfering-machine-btns :deep(.el-button--default:hover) {
  border-color: #10b981 !important;
  background: #ecfdf5 !important;
  color: #059669 !important;
}

/* ── 面取指示-今日：ヘッダー4按钮 间距・颜色区分 ── */
.chamfering-mgmt-header-actions {
  gap: 4px;
}
.chamfering-mgmt-header-actions :deep(.el-button) {
  margin: 0;
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 6px;
  min-height: 28px;
  transition: opacity 0.2s;
}
.chamfering-mgmt-header-actions :deep(.el-button:hover) {
  opacity: 0.92;
}
/* 新規追加：灰底描边 */
.chamfering-mgmt-header-actions :deep(.el-button--default:nth-child(1)) {
  color: #fdfdfd;
  border-color: #c0c4cc;
  background-color: #f83e47;
}
.chamfering-mgmt-header-actions :deep(.el-button--default:nth-child(1):hover) {
  color: #409eff;
  border-color: #b3d8ff;
  background-color: #fffeec;
}
/* 計画印刷：浅蓝描边 */
.chamfering-mgmt-header-actions :deep(.el-button--default:nth-child(2)) {
  color: #fcfcfc;
  border-color: #b3d8ff;
  background-color: #fdc407;
}
.chamfering-mgmt-header-actions :deep(.el-button--default:nth-child(2):hover) {
  color: #66b1ff;
  border-color: #66b1ff;
  background-color: #d9ecff;
}
/* 指示書発行：蓝色主按钮 */
.chamfering-mgmt-header-actions :deep(.el-button--primary) {
  color: #fff;
  border-color: #409eff;
  background-color: #409eff;
  font-weight: 500;
}
.chamfering-mgmt-header-actions :deep(.el-button--primary:hover) {
  border-color: #66b1ff;
  background-color: #66b1ff;
}
/* 実績確定：绿色成功按钮 */
.chamfering-mgmt-header-actions :deep(.el-button--success) {
  color: #fff;
  border-color: #67c23a;
  background-color: #67c23a;
  font-weight: 500;
}
.chamfering-mgmt-header-actions :deep(.el-button--success:hover) {
  border-color: #85ce61;
  background-color: #85ce61;
}

/* ── 面取指示-今日：空状態美化 ── */
.chamfering-management-section .cutting-mgmt-empty {
  padding: 20px 16px;
  font-size: 12px;
  color: #6ee7b7;
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border: 1px dashed #a7f3d0;
  border-radius: 8px;
  text-align: center;
  margin: 6px;
  font-weight: 500;
}

/* ── 面取指示-今日：セル内スイッチ compact ── */
.chamfering-management-section .cutting-mgmt-td-switch {
  padding: 2px 4px;
}
.chamfering-management-section .cutting-mgmt-td-switch :deep(.el-switch) {
  --el-switch-on-color: #10b981;
  height: 18px;
}

.cutting-mgmt-td-actions .el-button {
  padding: 2px 4px;
  min-width: auto;
}
.cutting-mgmt-td-actions .el-button + .el-button {
  margin-left: 0;
}

/* ========== 4表共通：列对齐（表头・数据・合計一致） ========== */
/* 切断指示-今日：13列 — 左: 製品名(5), 原材料(6), 備考(12)；右: 生産数(7)；中: 其余 */
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(5),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(5),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(6),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(6),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(12),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(12) {
  justify-content: flex-start;
  text-align: left;
}
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(7),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(7) {
  justify-content: flex-end;
  text-align: right;
}
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(1),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(2),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(3),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(4),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(8),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(9),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(10),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(11),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(12),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(13),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(1),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(2),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(3),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(4),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(8),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(9),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(10),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(11),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(12),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(13) {
  justify-content: center;
  text-align: center;
}
/* 切断指示-翌日：8列 — 左: 製品名(4)；右: 生産数(5)、生産時間(8)；中: 其余 */
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(4),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(4) {
  justify-content: flex-start;
  text-align: left;
}
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(5),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(5) {
  justify-content: flex-end;
  text-align: right;
}
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(1),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(2),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(3),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(7),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(8),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(1),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(2),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(3),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(7),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(8) {
  justify-content: center;
  text-align: center;
}
/* 面取指示-今日：13列 — 左: 製品名(5), 原材料(6)；右: 生産数(7)；中: 其余 */
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(5),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(5),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(6),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(6) {
  justify-content: flex-start;
  text-align: left;
}
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(7) {
  justify-content: flex-end;
  text-align: right;
}
/* 面取指示-翌日：8列 — 左: 製品名(4)；右: 生産数(5)、生産時間(8)；中: 其余 */
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(4),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(4) {
  justify-content: flex-start;
  text-align: left;
}
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(5),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(5) {
  justify-content: flex-end;
  text-align: right;
}
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(1),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(2),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(3),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(6),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-th:nth-child(8),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(1),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(2),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(3),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(6),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(7),
.chamfering-management-section .cutting-mgmt-table-inner--chamfering-tomorrow .cutting-mgmt-td:nth-child(8) {
  justify-content: center;
  text-align: center;
}
/* 生産数(7)、生産順(9)、生産時間(10)：切断今日 表头与数据居中（与上不冲突，7 已设为右） */
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(9),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-th:nth-child(10),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(9),
.cutting-management-section .cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-td:nth-child(10) {
  justify-content: center;
  text-align: center;
}

/* 切断指示-今日：数据行高缩小约 10%（padding 6px→5px） */
.cutting-mgmt-table-inner:not(.cutting-mgmt-table-inner--tomorrow) .cutting-mgmt-data-row .cutting-mgmt-td {
  padding-top: 3px;
  padding-bottom: 3px;
}

.cutting-mgmt-data-row {
  border-bottom: 1px solid #f1f5f9;
  cursor: grab;
  transition: background 0.15s;
  height: 30px;
  min-height: 30px;
  flex-shrink: 0;
}
.cutting-mgmt-data-row:hover {
  background: #f8fafc;
}
.cutting-mgmt-data-row:active {
  cursor: grabbing;
}
.cutting-mgmt-data-row .cutting-mgmt-td {
  color: #1e293b;
}
.cutting-mgmt-td-switch {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 生産日セル：双击でインライン編集（◀ 日期 ▶） */
.cutting-mgmt-td-production-day {
  min-width: 0;
}
.cutting-mgmt-td-production-day.is-editing-production-day {
  min-width: 260px;
}
.production-day-editor {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
}
.production-day-editor .el-button.is-circle { padding: 4px; width: 24px; height: 24px; }
.production-day-editor .production-day-picker-inline { width: 160px; }
.production-day-editor :deep(.el-date-editor) { width: 160px !important; }

.cutting-mgmt-table :deep(.el-table__header th),
.cutting-mgmt-table :deep(.el-table__body td) {
  font-size: 11px;
}

.kanban-issuance-section .cutting-mgmt-table-wrap :deep(.el-table__header-wrapper) {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
}
.kanban-issuance-section .cutting-mgmt-table-wrap :deep(.el-table th.el-table__cell) {
  background: transparent !important;
  color: #92400e;
  font-weight: 600;
}

.cutting-mgmt-empty {
  padding: 32px 24px;
  text-align: center;
  color: #64748b;
  font-size: 13px;
  background: #f8fafc;
  border-radius: 10px;
  margin: 8px;
  border: 1px dashed #e2e8f0;
}

.cutting-row-drag-handle {
  cursor: grab;
  padding: 2px;
  color: #94a3b8;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.cutting-row-drag-handle:hover {
  color: #64748b;
}

.cutting-row-drag-handle:active {
  cursor: grabbing;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  font-weight: 700;
  color: #1d4ed8;
  letter-spacing: -0.02em;
  flex: 1;
  min-width: 0;
}
.section-title .section-title-label {
  flex-shrink: 0;
}
.card-header .section-title .title-toolbar-btn--data {
  margin-left: auto;
}
.title-toolbar-btn {
  margin: 0 !important;
  height: 28px !important;
  padding: 0 12px !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  border-radius: 7px !important;
  letter-spacing: 0.02em !important;
}
.title-toolbar-btn--data {
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%) !important;
  border-color: #c7d2fe !important;
  color: #3730a3 !important;
  box-shadow: 0 1px 2px rgba(49, 46, 129, 0.08) !important;
}
.title-toolbar-btn--data:hover {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%) !important;
  border-color: #818cf8 !important;
  color: #2563eb !important;
}
.title-toolbar-btn--sync {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important;
  border-color: #6ee7b7 !important;
  color: #047857 !important;
  box-shadow: 0 1px 2px rgba(5, 150, 105, 0.1) !important;
}
.title-toolbar-btn--sync:hover {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
  border-color: #34d399 !important;
  color: #065f46 !important;
}
.title-toolbar-sync-icon {
  margin-right: 4px;
  font-size: 13px;
  vertical-align: -2px;
}

.search-section {
  margin-bottom: 10px;
}

/* ============================
   ロット編集ダイアログ (ped-*)
   el-dialog overrides → グローバル style に移動済み
   ============================ */

/* Header内容 */
.ped-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
}
.ped-header-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.ped-header-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.ped-title {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
}
.ped-badge {
  margin-left: 8px;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255,255,255,0.25);
  color: #fff;
  vertical-align: middle;
}
.ped-subtitle {
  font-size: 11px;
  color: rgba(255,255,255,0.7);
  line-height: 1.3;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Body */
.ped-body {
  padding: 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Section */
.ped-section {
  background: #f8fafc;
  border: 1px solid #e8edf3;
  border-radius: 8px;
  padding: 8px 12px 10px;
}
.ped-section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid currentColor;
  line-height: 1;
}
.ped-sec-blue  { color: #2563eb; }
.ped-sec-green { color: #16a34a; }
.ped-sec-amber { color: #d97706; }
.ped-sec-purple{ color: #7c3aed; }

/* Grid layouts */
.ped-grid {
  display: grid;
  gap: 6px 10px;
}
.ped-grid-3 { grid-template-columns: repeat(3, 1fr); }
.ped-grid-4 { grid-template-columns: repeat(4, 1fr); }

.ped-field {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}
.ped-field-span2 {
  grid-column: span 2;
}
.ped-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
  white-space: nowrap;
}
.ped-field :deep(.el-input__wrapper),
.ped-field :deep(.el-input-number .el-input__wrapper) {
  border-radius: 6px;
  transition: box-shadow 0.15s;
}
.ped-field :deep(.el-date-editor.el-input__wrapper) {
  border-radius: 6px;
}

/* Switch row (工程フラグ) */
.ped-switch-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
}
.ped-switch-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.ped-switch-label {
  font-size: 12px;
  color: #334155;
  white-space: nowrap;
}

/* Footer */
.ped-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: #f8fafc;
}
.ped-footer :deep(.el-button--primary) {
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  border-color: #2563eb;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.ped-footer :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #1d4ed8, #1e40af);
  border-color: #1d4ed8;
}

@media (max-width: 700px) {
  .ped-grid-3 { grid-template-columns: repeat(2, 1fr); }
  .ped-grid-4 { grid-template-columns: repeat(2, 1fr); }
  .ped-field-span2 { grid-column: span 2; }
}
@media (max-width: 480px) {
  .ped-grid-3, .ped-grid-4 { grid-template-columns: 1fr; }
  .ped-field-span2 { grid-column: span 1; }
}

/* データ管理ダイアログ */
.data-management-dialog :deep(.el-dialog__body) {
  padding: 12px 16px 16px;
}
.data-management-toolbar {
  margin-bottom: 12px;
}
.data-management-toolbar .filter-form :deep(.el-form-item) {
  margin-bottom: 8px;
  margin-right: 12px;
}
.data-management-table-wrap {
  min-height: 200px;
}
.data-management-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
  font-size: 12px;
  color: #64748b;
}
.data-management-footer .total-text {
  font-weight: 500;
  white-space: nowrap;
}

.cutting-done-dialog :deep(.el-dialog__body) {
  padding: 10px 12px 12px;
  background: linear-gradient(180deg, #fbfdff 0%, #f8fafc 100%);
}
.cutting-done-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #dbeafe;
  box-shadow: 0 16px 36px rgba(30, 64, 175, 0.14);
}
.cutting-done-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 10px 14px 8px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
}
.cutting-done-dialog :deep(.el-dialog__title) {
  font-size: 14px;
  font-weight: 700;
  color: #1e3a8a;
  letter-spacing: 0.01em;
}
.cutting-done-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
}
.cutting-done-toolbar {
  margin-bottom: 8px;
  padding: 8px 10px 4px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.85);
}
.cutting-done-toolbar .filter-form :deep(.el-form-item) {
  margin-bottom: 6px;
  margin-right: 10px;
}
.cutting-done-toolbar .filter-form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  padding-right: 6px;
}
.cutting-done-toolbar .filter-form :deep(.el-input__wrapper),
.cutting-done-toolbar .filter-form :deep(.el-select__wrapper),
.cutting-done-toolbar .filter-form :deep(.el-range-editor) {
  min-height: 28px;
}
.cutting-done-toolbar .filter-form :deep(.el-button) {
  min-height: 28px;
  padding: 0 10px;
}
.cutting-done-table-wrap {
  min-height: 200px;
  border: 1px solid #dbeafe;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
}
.cutting-done-table-wrap :deep(.el-table) {
  --el-table-header-bg-color: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
}
.cutting-done-table-wrap :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  color: #1e3a8a;
  font-size: 11px;
  font-weight: 700;
  padding: 6px 0;
}
.cutting-done-table-wrap :deep(.el-table td.el-table__cell) {
  padding: 5px 0;
  font-size: 11px;
}
.cutting-done-table-wrap :deep(.el-table--small .cell) {
  line-height: 1.3;
}
.cutting-done-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding: 6px 2px 0;
  border-top: 1px solid #e2e8f0;
  font-size: 11px;
  color: #475569;
}
.cutting-done-footer .total-text {
  font-weight: 600;
}
.cutting-done-footer :deep(.el-pagination) {
  --el-pagination-font-size: 11px;
}
.cutting-done-footer :deep(.el-pagination button),
.cutting-done-footer :deep(.el-pagination .el-pager li) {
  min-width: 24px;
  height: 24px;
  line-height: 24px;
}

.chamfering-done-dialog :deep(.el-dialog__body) {
  padding: 10px 12px 12px;
  background: linear-gradient(180deg, #fbfffd 0%, #f8fafc 100%);
}
.chamfering-done-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #d1fae5;
  box-shadow: 0 16px 36px rgba(5, 150, 105, 0.14);
}
.chamfering-done-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 10px 14px 8px;
  border-bottom: 1px solid #d1fae5;
  background: linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
}
.chamfering-done-dialog :deep(.el-dialog__title) {
  font-size: 14px;
  font-weight: 700;
  color: #065f46;
  letter-spacing: 0.01em;
}
.chamfering-done-dialog :deep(.el-dialog__headerbtn) {
  top: 10px;
  right: 10px;
}
.chamfering-done-toolbar {
  margin-bottom: 8px;
  padding: 8px 10px 4px;
  border: 1px solid #d1fae5;
  border-radius: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%);
  box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.85);
}
.chamfering-done-toolbar .filter-form :deep(.el-form-item) {
  margin-bottom: 6px;
  margin-right: 10px;
}
.chamfering-done-toolbar .filter-form :deep(.el-form-item__label) {
  font-size: 11px;
  font-weight: 600;
  color: #334155;
  padding-right: 6px;
}
.chamfering-done-toolbar .filter-form :deep(.el-input__wrapper),
.chamfering-done-toolbar .filter-form :deep(.el-select__wrapper),
.chamfering-done-toolbar .filter-form :deep(.el-range-editor) {
  min-height: 28px;
}
.chamfering-done-toolbar .filter-form :deep(.el-button) {
  min-height: 28px;
  padding: 0 10px;
}
.chamfering-done-table-wrap {
  min-height: 200px;
  border: 1px solid #d1fae5;
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
}
.chamfering-done-table-wrap :deep(.el-table) {
  --el-table-header-bg-color: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
}
.chamfering-done-table-wrap :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
  color: #065f46;
  font-size: 11px;
  font-weight: 700;
  padding: 6px 0;
}
.chamfering-done-table-wrap :deep(.el-table td.el-table__cell) {
  padding: 5px 0;
  font-size: 11px;
}
.chamfering-done-table-wrap :deep(.el-table--small .cell) {
  line-height: 1.3;
}
.chamfering-done-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding: 6px 2px 0;
  border-top: 1px solid #d1fae5;
  font-size: 11px;
  color: #475569;
}
.chamfering-done-footer .total-text {
  font-weight: 600;
}
.chamfering-done-footer :deep(.el-pagination) {
  --el-pagination-font-size: 11px;
}
.chamfering-done-footer :deep(.el-pagination button),
.chamfering-done-footer :deep(.el-pagination .el-pager li) {
  min-width: 24px;
  height: 24px;
  line-height: 24px;
}

.data-management-table-wrap .editable-cell {
  cursor: pointer;
  min-height: 1em;
  display: inline-block;
}
.data-management-table-wrap .editable-cell:hover {
  background: var(--el-fill-color-light);
  border-radius: 2px;
}

/* (plan-edit-form クラスは新 ped-* 設計に置き換えました) */

.compact-form :deep(.el-form-item) {
  margin-bottom: 8px;
  margin-right: 16px;
}

.compact-form :deep(.el-form-item .el-form-item__label) {
  font-size: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* 試作追加按钮：与 新規追加 区分，试作专用样式 */
.btn-trial-add {
  border-radius: 6px;
  font-weight: 500;
  color: #b45309;
  border-color: #d97706;
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  box-shadow: 0 1px 2px rgba(217, 119, 6, 0.08);
}
.btn-trial-add:hover {
  color: #fff;
  border-color: #d97706;
  background: linear-gradient(180deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 2px 6px rgba(217, 119, 6, 0.3);
}
.btn-trial-add:active {
  background: linear-gradient(180deg, #d97706 0%, #b45309 100%);
}

.instruction-column-picker {
  max-height: 280px;
  overflow-y: auto;
  padding: 4px 0;
}

.instruction-column-picker .picker-item {
  padding: 2px 0;
}

.instruction-column-picker .picker-item :deep(.el-checkbox__label) {
  font-size: 12px;
}

/* 生産ロット一覧：表头固定・数据行表格模式 */
.plan-batch-table-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  max-height: 288px;
  position: relative;
  overflow: hidden;
}

.plan-batch-drop-hint {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  font-size: 12px;
  color: #3b82f6;
  padding: 6px 12px;
  background: #eff6ff;
  border-radius: 6px;
  border: 1px dashed #3b82f6;
  white-space: nowrap;
}

.plan-batch-table-inner {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #e0e7ff;
  border-radius: 10px;
  overflow-x: auto;
  overflow-y: auto;
  scrollbar-gutter: stable;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02);
}

.plan-batch-thead {
  flex-shrink: 0;
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border-bottom: 2px solid #c7d2fe;
  position: sticky;
  top: 0;
  z-index: 1;
  box-shadow: 0 3px 6px rgba(79, 70, 229, 0.06);
}

.plan-batch-tbody {
  flex: 1;
  min-height: 0;
}

.plan-batch-tr {
  display: flex;
  align-items: center;
  min-width: 620px;
  width: 100%;
  font-size: 11px;
}

.plan-batch-thead .plan-batch-tr {
  font-weight: 600;
  color: #475569;
}

.chamfering-batch-section-card .plan-batch-thead {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
  border-bottom-color: #a7f3d0;
}

.plan-batch-th,
.plan-batch-td {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 8px;
  border-right: 1px solid #e2e8f0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
}

.plan-batch-th:last-child,
.plan-batch-td:last-child {
  border-right: none;
}

/* 製品名のみ左寄せ */
.plan-batch-th:nth-child(4),
.plan-batch-td:nth-child(4) {
  justify-content: flex-start;
  text-align: left;
}

/* 12列: 生産月, ライン, 順位, 製品名, 計画数, 原材料, ロット数, ロットNo, 生産数, 在庫区分, 材料使用数, 操作 */
.plan-batch-th:nth-child(1),
.plan-batch-td:nth-child(1) { flex: 0 0 72px; }
.plan-batch-th:nth-child(2),
.plan-batch-td:nth-child(2) { flex: 0 0 52px; }
.plan-batch-th:nth-child(3),
.plan-batch-td:nth-child(3) { flex: 0 0 40px; }
.plan-batch-th:nth-child(4),
.plan-batch-td:nth-child(4) { flex: 1 1 0; min-width: 110px; }
.plan-batch-th:nth-child(5),
.plan-batch-td:nth-child(5) { flex: 0 0 55px; }
.plan-batch-th:nth-child(6),
.plan-batch-td:nth-child(6) { flex: 0 0 110px; }
.plan-batch-th:nth-child(7),
.plan-batch-td:nth-child(7) { flex: 0 0 55px; }
.plan-batch-th:nth-child(8),
.plan-batch-td:nth-child(8) { flex: 0 0 40px; }
.plan-batch-th:nth-child(9),
.plan-batch-td:nth-child(9) { flex: 0 0 55px; }
.plan-batch-th:nth-child(10),
.plan-batch-td:nth-child(10) { flex: 0 0 70px; }
.plan-batch-th:nth-child(11),
.plan-batch-td:nth-child(11) { flex: 0 0 80px; }
.plan-batch-th:nth-child(12),
.plan-batch-td:nth-child(12) { flex: 0 0 60px; }

.plan-batch-th-actions,
.plan-batch-td-actions {
  justify-content: center;
  gap: 0;
}

.plan-batch-data-row {
  cursor: grab;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.15s;
}

/* 順位別の浅色背景（0〜4 で循環） */
.plan-batch-priority-none { background: #fff; }
.plan-batch-priority-0 { background: #eff6ff; }  /* 順位1,6,11… 青系 */
.plan-batch-priority-1 { background: #f0fdf4; }  /* 順位2,7,12… 緑系 */
.plan-batch-priority-2 { background: #fffbeb; }  /* 順位3,8,13… 黄系 */
.plan-batch-priority-3 { background: #faf5ff; }  /* 順位4,9,14… 紫系 */
.plan-batch-priority-4 { background: #ecfeff; }  /* 順位5,10,15… 水色系 */

.plan-batch-data-row:hover {
  filter: brightness(0.97);
}

.plan-batch-data-row:active {
  cursor: grabbing;
}

.plan-batch-row-selected {
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
}

.plan-batch-empty {
  padding: 32px 24px;
  text-align: center;
  color: #64748b;
  font-size: 13px;
  background: #f8fafc;
  border: 1px dashed #e2e8f0;
  border-radius: 10px;
  margin: 8px;
}

/* 面取ロット一覧：生産ロット一覧と同じレイアウト（plan-row + 右パネル） */
.chamfering-plan-row {
  align-items: stretch;
}

.chamfering-batch-section-card {
  height: 100%;
  min-height: 288px;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
  border: 1px solid #d1fae5;
  border-left: 4px solid var(--chamfering-accent);
  border-radius: 12px;
  padding: 10px 12px;
  box-shadow: 0 4px 12px -2px rgba(5, 150, 105, 0.1), 0 2px 8px -1px rgba(5, 150, 105, 0.06);
  transition: box-shadow 0.25s ease;
}

.chamfering-batch-section-card:hover {
  box-shadow: 0 8px 20px -4px rgba(5, 150, 105, 0.15), 0 4px 12px -2px rgba(5, 150, 105, 0.10);
}

.chamfering-batch-section-card .cutting-mgmt-header {
  margin-bottom: 8px;
  flex-shrink: 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #d1fae5;
}

.chamfering-batch-section-card .cutting-mgmt-title {
  color: #047857;
}

.chamfering-batch-table-wrap {
  flex: 1;
  min-height: 0;
  max-height: 288px;
}

/* 面取ロット一覧：10列（CD, 生産月, ライン, 製品名, 原材料, 生産数, ロット数, ロットNo, SW, 操作） */
.chamfering-batch-table-wrap .plan-batch-tr {
  min-width: 620px;
}

.chamfering-batch-table-wrap .plan-batch-th:nth-child(1),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(1) { flex: 0 0 56px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(2),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(2) { flex: 0 0 72px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(3),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(3) { flex: 0 0 52px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(4),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(4) { flex: 1 1 0; min-width: 110px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(5),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(5) { flex: 0 0 110px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(6),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(6) { flex: 0 0 55px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(7),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(7) { flex: 0 0 55px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(8),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(8) { flex: 0 0 48px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(9),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(9) { flex: 0 0 36px; }
.chamfering-batch-table-wrap .plan-batch-th:nth-child(10),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(10) { flex: 0 0 90px; }

.chamfering-batch-table-wrap .plan-batch-th:nth-child(4),
.chamfering-batch-table-wrap .plan-batch-td:nth-child(4) {
  justify-content: flex-start;
  text-align: left;
}

.chamfering-batch-table-wrap .plan-batch-data-row {
  cursor: pointer;
}

/* 面取行右パネルも左列（面取ロット一覧）と同高で stretch（.right-panel の flex:1 を継承） */

/* 放置区 */
.drop-zone {
  display: flex;
  flex-direction: column;
  min-height: 160px;
  transition: background 0.2s, border-color 0.2s;
}

.drop-zone .drop-zone-label {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 8px;
}

.drop-zone-active {
  background: #eff6ff !important;
  border-color: #3b82f6 !important;
}

.dropped-cards {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow-y: auto;
}

.dropped-mini-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 12px;
}

.mini-card-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.mini-card-remove {
  flex-shrink: 0;
  padding: 2px;
}

.pagination-wrap {
  display: none; /* 分页组件隐藏不显示 */
  justify-content: center;
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}

.pagination-wrap :deep(.el-pagination) {
  font-size: 12px;
}

.pagination-wrap :deep(.el-pagination .el-pager li),
.pagination-wrap :deep(.el-pagination .el-select .el-input__inner) {
  min-width: 28px;
  height: 28px;
  line-height: 28px;
  font-size: 12px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1200px) {
  .cutting-instruction-container {
    padding: 12px 16px;
  }
  .page-header {
    padding: 10px 14px;
    margin-bottom: 10px;
  }
  .header-title h1 {
    font-size: 16px;
  }
}

/* 切断指示-今日・翌日：响应式（中屏以下左右改为上下堆叠，小屏进一步优化） */
@media (max-width: 1024px) {
  .instruction-row.instruction-cols-6-4 {
    flex-direction: column;
  }
  .instruction-row.instruction-cols-6-4 .instruction-col:nth-child(1),
  .instruction-row.instruction-cols-6-4 .instruction-col:nth-child(2) {
    flex: 1 1 auto;
    width: 100%;
    min-height: 380px;
    max-width: 100%;
  }
  .cutting-management-section .cutting-mgmt-table-wrap {
    max-height: 380px;
  }
}

@media (max-width: 768px) {
  .instruction-row.instruction-cols-6-4 .instruction-col:nth-child(1),
  .instruction-row.instruction-cols-6-4 .instruction-col:nth-child(2) {
    min-height: 300px;
  }
  .cutting-management-section {
    min-height: 300px;
  }
  .cutting-management-section .cutting-mgmt-table-wrap {
    max-height: 320px;
    overflow-y: auto;
    overflow-x: hidden;
  }
  .cutting-mgmt-table-wrap {
    overflow-x: auto;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }
  .cutting-mgmt-header-left {
    flex: 1 1 100%;
  }
  .cutting-mgmt-header-right {
    width: 100%;
    justify-content: flex-start;
  }
}

@media (max-width: 480px) {
  .instruction-row.instruction-cols-6-4 .instruction-col:nth-child(1),
  .instruction-row.instruction-cols-6-4 .instruction-col:nth-child(2) {
    min-height: 260px;
    padding: 10px 12px;
  }
  .cutting-management-section {
    min-height: 260px;
  }
  .cutting-management-section .cutting-mgmt-table-wrap {
    max-height: 280px;
    overflow-y: auto;
    overflow-x: hidden;
  }
  .cutting-management-section .cutting-mgmt-tbody-drop-zone {
    height: auto;
    min-height: 0;
  }
  .cutting-mgmt-tbody-drop-zone {
    height: 280px;
    min-height: 280px;
  }
  .cutting-mgmt-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .cutting-mgmt-header-right {
    width: 100%;
  }
  .cutting-mgmt-machine-btns {
    flex-wrap: wrap;
  }
  .cutting-mgmt-machine-btns .el-button {
    margin-bottom: 4px;
  }
}

/* 未完了分を翌日へ順延 ダイアログ：スコープ内スタイル（基本レイアウト） */
.snd-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.snd-info-card {
  background: linear-gradient(135deg, #eff6ff 0%, #f0f9ff 100%);
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.snd-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.snd-info-label {
  color: #64748b;
  min-width: 52px;
  flex-shrink: 0;
}
.snd-info-value {
  color: #1e293b;
  font-weight: 500;
}
.snd-info-qty {
  color: #2563eb;
  font-weight: 700;
  font-size: 14px;
}
.snd-form-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
}
.snd-section-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #f59e0b;
  border-left: 3px solid #f59e0b;
  padding-left: 6px;
  margin-bottom: 10px;
  line-height: 1;
}
.snd-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 8px;
}
.snd-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.snd-field-full {
  grid-column: span 2;
}
.snd-field-label {
  font-size: 11px;
  color: #64748b;
  font-weight: 500;
}
.snd-required {
  color: #ef4444;
  margin-left: 2px;
}
.snd-qty-input {
  width: 100%;
}
.snd-input-suffix {
  font-size: 11px;
  color: #94a3b8;
}
.snd-remainder-badge {
  display: flex;
  align-items: baseline;
  gap: 4px;
  background: #fff7ed;
  border: 1px solid #fed7aa;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 18px;
  font-weight: 700;
  color: #ea580c;
  min-height: 32px;
}
.snd-remainder-unit {
  font-size: 11px;
  color: #c2410c;
  font-weight: 500;
}
.snd-hint {
  margin: 0;
  font-size: 11px;
  color: #78716c;
  display: flex;
  align-items: center;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .cutting-instruction-container {
    padding: 10px 12px;
  }
  .plan-row {
    flex-direction: column;
  }
  .plan-section-left,
  .plan-section-right {
    flex: 0 0 auto;
    width: 100%;
  }
  .plan-section-right {
    min-height: 120px;
  }
  .instruction-row.instruction-two-cols {
    flex-direction: column;
  }
  .instruction-row .instruction-col {
    flex: 0 0 auto;
    width: 100%;
    min-height: 200px;
  }
  .page-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
    padding: 10px 12px;
  }
  .card-header .section-title .title-toolbar-btn--data {
    margin-left: 0;
  }
  .section-title {
    font-size: 13px;
  }
}
</style>

<!-- 設備・データ管理製品名下拉選項字體縮小（popper 掛在 body，需單獨樣式） -->
<style>
.equipment-select-dropdown.el-select-dropdown .el-select-dropdown__item {
  font-size: 12px;
}
.data-management-product-select-dropdown.el-select-dropdown .el-select-dropdown__item {
  font-size: 11px;
}

/* ============================================================
   切断指示・面取指示 登録ダイアログ (.mt-dialog)
   ============================================================ */
.mt-dialog .el-dialog {
  border-radius: 12px !important;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15) !important;
  overflow: hidden !important;
}
.mt-dialog .el-dialog__header {
  padding: 0 !important;
  margin-right: 0 !important;
  border-bottom: 1px solid #e8edf3 !important;
}
.mt-dialog .el-dialog__headerbtn {
  top: 12px !important;
  right: 14px !important;
  z-index: 10;
}
.mt-dialog .el-dialog__headerbtn .el-icon {
  color: rgba(255, 255, 255, 0.8) !important;
}
.mt-dialog .el-dialog__headerbtn:hover .el-icon {
  color: #ffffff !important;
}
.mt-dialog .el-dialog__body {
  padding: 16px 20px !important;
  background: #fafbfc;
}
.mt-dialog-header {
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.mt-dialog-header--cutting {
  background: linear-gradient(135deg, #3730a3 0%, #4f46e5 100%);
}
.mt-dialog-header--chamfering {
  background: linear-gradient(135deg, #065f46 0%, #059669 100%);
}
.mt-dialog-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.mt-dialog-title {
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.02em;
}
.mt-dialog-subtitle {
  font-size: 10.5px;
  color: rgba(255, 255, 255, 0.75);
}
.mt-field-row {
  margin-bottom: 16px;
}
.mt-field-row:last-child {
  margin-bottom: 0;
}
.mt-field-col {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mt-field-label {
  font-size: 11.5px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
}
.mt-field-col .mt-field-label {
  margin-bottom: 0; /* for column layout, gap handles it */
}
.mt-date-control {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #ffffff;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);
}
.mt-date-picker {
  flex: 1;
}
.mt-date-picker .el-input__wrapper {
  box-shadow: none !important;
  background: transparent !important;
  padding: 0 4px !important;
}
.mt-date-picker .el-input__inner {
  text-align: center;
  font-weight: 600;
  color: #1e293b;
}
.mt-today-btn {
  font-size: 11px !important;
  padding: 4px 10px !important;
  height: 24px !important;
  border-radius: 4px !important;
}
.mt-machine-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);
}
.mt-machine-btn {
  margin-left: 0 !important;
  border-radius: 6px !important;
  font-size: 11.5px !important;
  padding: 6px 14px !important;
  min-height: 30px !important;
  transition: all 0.2s ease !important;
}
.mt-machine-btn.el-button--default {
  background: #f8fafc !important;
  border-color: #cbd5e1 !important;
  color: #475569 !important;
}
.mt-machine-btn.el-button--default:hover {
  background: #f1f5f9 !important;
  border-color: #94a3b8 !important;
  color: #1e293b !important;
}
.mt-select-full {
  width: 100% !important;
}
.mt-select-full .el-input__wrapper {
  border-radius: 6px !important;
  box-shadow: 0 0 0 1px #e2e8f0 !important;
}
.mt-select-full .el-input__wrapper:focus-within {
  box-shadow: 0 0 0 2px #3b82f6 !important;
}
.mt-dialog-footer {
  padding: 12px 20px 14px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  background: #ffffff;
  border-top: 1px solid #f1f5f9;
}
.mt-dialog-footer .el-button {
  border-radius: 6px !important;
  padding: 8px 16px !important;
}
.mt-submit-btn--chamfering {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
  border-color: #059669 !important;
}
.mt-submit-btn--chamfering:hover {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
}

/* 切断指示の編集：现代精美UI（body 直下 teleport のため global） */
.cutting-edit-dialog .el-dialog {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(30, 58, 95, 0.18), 0 4px 12px rgba(0, 0, 0, 0.06);
}
.cutting-edit-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
  border: none;
}
.cutting-edit-dialog .el-dialog__headerbtn {
  top: 10px;
  right: 12px;
  width: 28px;
  height: 28px;
  color: rgba(255, 255, 255, 0.85);
}
.cutting-edit-dialog .el-dialog__headerbtn:hover {
  color: #fff;
}
.cutting-edit-dialog__header {
  padding: 10px 14px 10px 16px;
  background: linear-gradient(135deg, #334155 0%, #475569 50%, #64748b 100%);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.cutting-edit-dialog__title {
  opacity: 0.98;
}
.cutting-edit-dialog .el-dialog__body {
  padding: 10px 14px 12px;
  background: #fafbfc;
}
.cutting-edit-form .el-form-item.cutting-edit-form-item {
  margin-bottom: 8px;
}
.cutting-edit-form .cutting-edit-form-row {
  margin-bottom: 8px;
}
.cutting-edit-form .cutting-edit-form-row .cutting-edit-form-item {
  margin-bottom: 0;
}
.cutting-edit-form .el-form-item:last-child {
  margin-bottom: 0;
}
.cutting-edit-form .el-form-item__label {
  font-size: 12px;
  color: #64748b;
  padding-right: 10px;
}
.cutting-edit-form .el-input__wrapper,
.cutting-edit-form .el-textarea__inner {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0;
}
.cutting-edit-form .el-input__wrapper:hover,
.cutting-edit-form .el-textarea__inner:hover {
  box-shadow: 0 0 0 1px #94a3b8;
}
.cutting-edit-form .el-input__wrapper.is-focus,
.cutting-edit-form .el-textarea__inner:focus {
  box-shadow: 0 0 0 2px #3b82f6;
}
/* 生産数：青系で区別 */
.cutting-edit-form-item--qty .el-input__wrapper {
  background-color: #eff6ff;
  box-shadow: 0 0 0 1px #bfdbfe;
}
.cutting-edit-form-item--qty .el-input__wrapper:hover {
  background-color: #dbeafe;
  box-shadow: 0 0 0 1px #93c5fd;
}
.cutting-edit-form-item--qty .el-input__wrapper.is-focus {
  background-color: #fff;
  box-shadow: 0 0 0 2px #3b82f6;
}
/* 不良数：琥珀系で区別 */
.cutting-edit-form-item--defect .el-input__wrapper {
  background-color: #fffbeb;
  box-shadow: 0 0 0 1px #fde68a;
}
.cutting-edit-form-item--defect .el-input__wrapper:hover {
  background-color: #fef3c7;
  box-shadow: 0 0 0 1px #fcd34d;
}
.cutting-edit-form-item--defect .el-input__wrapper.is-focus {
  background-color: #fff;
  box-shadow: 0 0 0 2px #d97706;
}
.cutting-edit-remarks .el-form-item__content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.cutting-edit-remarks-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.cutting-edit-remarks-btns .el-button {
  margin-left: 0;
}
.cutting-edit-tag-btn {
  --el-button-bg-color: #eff6ff;
  --el-button-border-color: #bfdbfe;
  --el-button-text-color: #1d4ed8;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 6px;
}
.cutting-edit-tag-btn:hover {
  --el-button-bg-color: #dbeafe;
  --el-button-border-color: #93c5fd;
  --el-button-text-color: #1d4ed8;
}
.cutting-edit-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 14px 10px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

/* 面取指示編集：同レイアウト＋緑テーマで区別・入力しやすく */
.chamfering-edit-dialog .el-dialog__header {
  padding: 0;
}
.chamfering-edit-dialog .cutting-edit-dialog__header {
  background: linear-gradient(135deg, #047857 0%, #059669 50%, #10b981 100%);
}
.chamfering-edit-dialog .el-dialog__body {
  padding: 14px 16px 16px;
  background: #f0fdf4;
}
.chamfering-edit-dialog .cutting-edit-form .el-form-item__label {
  color: #065f46;
  font-weight: 500;
}
.chamfering-edit-dialog .cutting-edit-form .el-input__wrapper,
.chamfering-edit-dialog .cutting-edit-form .el-textarea__inner {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #a7f3d0;
  min-height: 32px;
}
.chamfering-edit-dialog .cutting-edit-form .el-input__wrapper:hover,
.chamfering-edit-dialog .cutting-edit-form .el-textarea__inner:hover {
  box-shadow: 0 0 0 1px #6ee7b7;
}
.chamfering-edit-dialog .cutting-edit-form .el-input__wrapper.is-focus,
.chamfering-edit-dialog .cutting-edit-form .el-textarea__inner:focus {
  box-shadow: 0 0 0 2px #059669;
}
.chamfering-edit-dialog .cutting-edit-form-item--qty .el-input__wrapper {
  background-color: #eff6ff;
  box-shadow: 0 0 0 1px #93c5fd;
}
.chamfering-edit-dialog .cutting-edit-form-item--qty .el-input__wrapper:hover {
  background-color: #dbeafe;
  box-shadow: 0 0 0 1px #60a5fa;
}
.chamfering-edit-dialog .cutting-edit-form-item--qty .el-input__wrapper.is-focus {
  background-color: #fff;
  box-shadow: 0 0 0 2px #2563eb;
}
.chamfering-edit-dialog .cutting-edit-form-item--defect .el-input__wrapper {
  background-color: #fffbeb;
  box-shadow: 0 0 0 1px #fcd34d;
}
.chamfering-edit-dialog .cutting-edit-form-item--defect .el-input__wrapper:hover {
  background-color: #fef3c7;
  box-shadow: 0 0 0 1px #f59e0b;
}
.chamfering-edit-dialog .cutting-edit-form-item--defect .el-input__wrapper.is-focus {
  background-color: #fff;
  box-shadow: 0 0 0 2px #d97706;
}
.chamfering-edit-dialog .cutting-edit-form-row {
  margin-bottom: 10px;
}
.chamfering-edit-dialog .cutting-edit-form .cutting-edit-form-row .cutting-edit-form-item {
  margin-bottom: 0;
}
.chamfering-edit-save-btn {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
  border-color: #059669 !important;
}
.chamfering-edit-save-btn:hover {
  background: linear-gradient(135deg, #047857 0%, #34d399 100%) !important;
  border-color: #047857 !important;
}

/* 面取指示 新規追加ダイアログ：紧凑・现代UI */
.chamfering-new-dialog .el-dialog {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 20px 40px -12px rgba(5, 150, 105, 0.15);
}
.chamfering-new-dialog .el-dialog__header {
  padding: 12px 16px 10px;
  border-bottom: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f0fdf4 0%, #fff 100%);
}
.chamfering-new-dialog .el-dialog__title {
  font-size: 15px;
  font-weight: 600;
  color: #047857;
}
.chamfering-new-dialog .el-dialog__body {
  padding: 12px 16px 14px;
  background: #fafbfc;
}
.chamfering-new-form .el-form-item {
  margin-bottom: 10px;
}
.chamfering-new-form .el-form-item:last-child {
  margin-bottom: 0;
}
.chamfering-new-form .el-form-item__label {
  font-size: 12px;
  color: #64748b;
  padding-right: 8px;
}
.chamfering-new-form .el-row {
  margin-bottom: 0;
}
.chamfering-new-form .el-row + .el-form-item {
  margin-top: 2px;
}
.chamfering-new-form .el-input__wrapper,
.chamfering-new-form .el-textarea__inner {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #e2e8f0;
}
.chamfering-new-form .el-input.is-disabled .el-input__wrapper {
  background: #f1f5f9;
  color: #475569;
}
.chamfering-new-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px 16px 12px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
}

.confirm-actual-result-dialog .el-dialog__header {
  padding: 16px 20px 12px;
  margin-right: 0;
}
.confirm-actual-result-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.confirm-actual-result-icon {
  font-size: 24px;
  color: var(--el-color-success);
}
.confirm-actual-result-title {
  font-size: 17px;
  font-weight: 600;
  color: #1e293b;
  letter-spacing: 0.02em;
}
.confirm-actual-result-dialog .el-dialog__body {
  padding: 8px 20px 20px;
}
.confirm-actual-result-body {
  font-size: 14px;
}
.confirm-actual-result-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.confirm-actual-result-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 14px 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.confirm-actual-result-card:hover {
  border-color: #cbd5e1;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}
.confirm-actual-result-card--highlight {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-color: #a7f3d0;
}
.confirm-actual-result-card--highlight:hover {
  border-color: #6ee7b7;
  box-shadow: 0 1px 3px rgba(34, 197, 94, 0.12);
}
.confirm-actual-result-card-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  letter-spacing: 0.02em;
}
.confirm-actual-result-card-value {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
}
.confirm-actual-result-card--highlight .confirm-actual-result-card-value {
  color: #047857;
  font-size: 22px;
}
.confirm-actual-result-footer {
  display: flex;
  justify-content: flex-end;
  padding: 4px 0 0;
}
.confirm-actual-result-footer .el-button {
  min-width: 88px;
  border-radius: 8px;
}
.cutting-edit-save-btn {
  --el-button-bg-color: #2563eb;
  --el-button-border-color: #2563eb;
  --el-button-hover-bg-color: #1d4ed8;
  --el-button-hover-border-color: #1d4ed8;
  border-radius: 6px;
}

/* ==================================================
   ロット編集ダイアログ: el-dialog overrides (global)
   ダイアログは body 直下にテレポートされるため
   scoped の :deep() が効かない → global style で上書き
   ================================================== */
.plan-edit-dialog .el-dialog {
  border-radius: 12px !important;
  box-shadow: 0 16px 56px rgba(0, 0, 0, 0.15) !important;
  overflow: hidden !important;
}
.plan-edit-dialog .el-dialog__header {
  padding: 0 !important;
  margin-right: 0 !important;
  border-bottom: 1px solid #e8edf3 !important;
  background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%) !important;
}
.plan-edit-dialog .el-dialog__headerbtn {
  top: 12px !important;
  right: 16px !important;
}
.plan-edit-dialog .el-dialog__headerbtn .el-icon {
  color: rgba(255,255,255,0.75) !important;
}
.plan-edit-dialog .el-dialog__headerbtn:hover .el-icon {
  color: #fff !important;
}
.plan-edit-dialog .el-dialog__body {
  padding: 0 !important;
}
.plan-edit-dialog .el-dialog__footer {
  padding: 0 !important;
  border-top: 1px solid #e8edf3 !important;
}

/* ============================================================
   新規ロット追加 / 試作ロット追加 ダイアログ（global styles）
   ============================================================ */
.new-record-dialog .el-dialog {
  border-radius: 12px !important;
  overflow: hidden !important;
  box-shadow: 0 16px 48px rgba(0,0,0,0.16), 0 4px 12px rgba(0,0,0,0.07) !important;
}
.new-record-dialog .el-dialog__header {
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
}
.new-record-dialog .el-dialog__body {
  padding: 0 !important;
  max-height: 74vh;
  overflow-y: auto;
}
.new-record-dialog .el-dialog__footer {
  padding: 0 !important;
  border-top: 1px solid #e8edf3 !important;
}
/* ── Header ── */
.nr-header {
  display: flex; align-items: center; gap: 10px; padding: 11px 16px;
}
.nr-header--normal { background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 55%, #3b82f6 100%); }
.nr-header--trial  { background: linear-gradient(135deg, #4c1d95 0%, #7c3aed 55%, #a78bfa 100%); }
.nr-header-icon {
  width: 32px; height: 32px; border-radius: 8px;
  background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.25);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; color: #fff;
}
.nr-header-text { display: flex; flex-direction: column; gap: 1px; flex: 1; min-width: 0; }
.nr-title   { font-size: 14px; font-weight: 700; color: #fff; line-height: 1.3; }
.nr-subtitle { font-size: 10px; color: rgba(255,255,255,0.70); line-height: 1.3; }
.nr-close-btn {
  color: rgba(255,255,255,0.7) !important;
  border: none !important; background: transparent !important;
  padding: 3px !important; min-height: unset !important; border-radius: 5px !important;
}
.nr-close-btn:hover { color:#fff !important; background: rgba(255,255,255,0.14) !important; }
/* ── Body ── */
.nr-body { padding: 0; }
.nr-section {
  padding: 8px 14px 6px;
  border-bottom: 1px solid #f1f5f9;
}
.nr-section--last { border-bottom: none; }
.nr-sec-hd {
  display: flex; align-items: center; gap: 5px;
  font-size: 10px; font-weight: 700; color: #64748b;
  letter-spacing: 0.07em; text-transform: uppercase;
  margin-bottom: 5px;
}
.nr-sec-dot {
  width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0;
}
.nr-dot-blue  { background: #2563eb; }
.nr-dot-green { background: #16a34a; }
.nr-dot-amber { background: #d97706; }
/* 3-col row */
.nr-row3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 4px 8px;
  margin-bottom: 4px;
}
.nr-row3:last-child { margin-bottom: 0; }
/* 1-col full row */
.nr-row1 {
  display: grid;
  grid-template-columns: 1fr;
  gap: 4px;
  margin-bottom: 4px;
}
.nr-row-align-end { align-items: end; }
.nr-col {
  display: flex; flex-direction: column; gap: 2px; min-width: 0;
}
.nr-lbl {
  font-size: 10.5px; color: #64748b; font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.nr-lbl em { font-style: normal; color: #ef4444; margin-left: 1px; }
/* Switch pair */
.nr-switches { display: flex; align-items: center; gap: 10px; padding-top: 3px; }
.nr-sw-item {
  display: flex; align-items: center; gap: 5px; cursor: pointer;
  font-size: 11px; color: #374151; font-weight: 500;
}
/* ── Footer ── */
.nr-footer {
  display: flex; align-items: center; justify-content: flex-end;
  gap: 8px; padding: 8px 14px 10px; background: #f8fafc;
}
.nr-save-btn {
  border-radius: 6px !important; font-weight: 600 !important; min-width: 76px !important;
}
/* ==================================================
   未完了順延ダイアログ シェル（global スタイル）
   ダイアログは body 直下にテレポートされるため global で上書き
   ================================================== */
.split-to-next-day-dialog .el-dialog {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(30, 58, 95, 0.18), 0 4px 12px rgba(0, 0, 0, 0.06);
}
.split-to-next-day-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
  border: none;
}
.split-to-next-day-dialog .el-dialog__headerbtn {
  top: 10px;
  right: 12px;
  width: 28px;
  height: 28px;
  color: rgba(255, 255, 255, 0.85);
}
.split-to-next-day-dialog .el-dialog__headerbtn:hover {
  color: #fff;
}
.split-to-next-day-dialog .el-dialog__body {
  padding: 14px 16px 12px;
  background: #fff;
}
.split-to-next-day-dialog .el-dialog__footer {
  padding: 0;
  border-top: 1px solid #e2e8f0;
}
.snd-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px;
  background: linear-gradient(135deg, #78350f 0%, #d97706 60%, #f59e0b 100%);
  color: #fff;
}
.snd-header-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.snd-header-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
  min-width: 0;
}
.snd-title {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
}
.snd-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.78);
  line-height: 1.3;
  max-width: 340px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.snd-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 10px;
  background: #fafbfc;
}

/* ============================================================
   ページ全体美化 – コンパクト・フォント・アニメーション
   ============================================================ */

/* ── コンテナ余白を縮小 ── */
.cutting-instruction-container {
  padding: 8px 12px !important;
  font-feature-settings: 'tnum' on, 'lnum' on;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
}

/* ── ページヘッダー compact ── */
.page-header {
  margin-bottom: 8px !important;
  padding: 10px 14px !important;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid #e0e7ff;
  box-shadow: 0 2px 8px rgba(37,99,235,0.08),inset 0 1px 2px rgba(255,255,255,0.5);
}
.header-title h1 { font-size: 16px !important; letter-spacing: -0.04em !important; font-weight: 800 !important; }
.header-title .header-desc { font-size: 11px !important; margin: 3px 0 0 !important; color: #64748b !important; }
.page-header-badge { font-size: 9px !important; padding: 2px 6px !important; margin-bottom: 4px !important; background: linear-gradient(135deg, #3b82f6, #2563eb); color: #fff !important; border-radius: 6px !important; font-weight: 700 !important; }

/* ── カード padding compact ── */
.plan-section .section-card :deep(.el-card__header) { padding: 8px 12px !important; }
.plan-section .section-card :deep(.el-card__body)   { padding: 8px 12px !important; }

/* ── カード hover lift ── */
.plan-section .section-card {
  transition: box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1), transform 0.25s ease !important;
  background: linear-gradient(135deg, #ffffff 0%, #f9fafb 100%);
}
.plan-section .section-card:hover {
  box-shadow: 0 12px 24px -6px rgba(37,99,235,0.18), 0 4px 12px -2px rgba(37,99,235,0.12) !important;
  transform: translateY(-2px);
}

/* ── instruction-col hover lift ── */
.instruction-row .instruction-col {
  padding: 8px 10px !important;
  transition: box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1), transform 0.25s ease, background 0.2s ease !important;
}
.instruction-row .instruction-col:hover {
  box-shadow: 0 8px 20px -4px rgba(0,0,0,0.12) !important;
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.95) !important;
}

/* ── gap compact ── */
.plan-row { gap: 8px !important; margin-bottom: 8px !important; }
.instruction-section { gap: 8px !important; margin-bottom: 8px !important; }
.instruction-row.instruction-two-cols { gap: 8px !important; }
.cutting-mgmt-header { margin-bottom: 4px !important; gap: 4px !important; }
.search-section { padding: 0 !important; }
.search-section :deep(.el-form--inline .el-form-item) { margin-bottom: 4px !important; }

/* ── ロット行 hover ── */
.plan-batch-data-row {
  transition: background-color 0.15s ease, box-shadow 0.15s ease !important;
}
.plan-batch-data-row:hover {
  background: linear-gradient(90deg, #eff6ff 0%, #f3f4f6 100%) !important;
  box-shadow: inset 3px 0 0 #2563eb !important;
}

/* ── 切断指示行 hover ── */
.cutting-mgmt-data-row { transition: background-color 0.15s ease, box-shadow 0.12s ease !important; }
.cutting-mgmt-data-row:hover { background: linear-gradient(90deg, #f8faff 0%, #f3f4f6 100%) !important; box-shadow: inset 2px 0 0 #3b82f6; }

/* ── table header 強化 ── */
.plan-batch-th, .cutting-mgmt-th {
  background: linear-gradient(180deg, #f1f5f9 0%, #e8edf5 100%) !important;
  color: #3730a3 !important;
  font-size: 10px !important;
  font-weight: 700 !important;
  letter-spacing: 0.03em !important;
  border-bottom: 2px solid #c7d2fe !important;
}

/* ── ボタン カラーコーディング & アニメーション ── */
.cutting-instruction-container :deep(.el-button) {
  transition: background-color 0.18s ease, border-color 0.18s ease,
              box-shadow 0.18s ease, transform 0.15s ease !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
}
.cutting-instruction-container :deep(.el-button:not(:disabled)):hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}
.cutting-instruction-container :deep(.el-button:not(:disabled)):active {
  transform: translateY(0) scale(0.97) !important;
}

/* primary – 青 */
.cutting-instruction-container :deep(.el-button--primary) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
  border-color: #1d4ed8 !important;
  box-shadow: 0 3px 8px rgba(37,99,235,0.32) !important;
  color: #fff !important;
}
.cutting-instruction-container :deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  box-shadow: 0 6px 16px rgba(37,99,235,0.45) !important;
}

/* success – 緑 */
.cutting-instruction-container :deep(.el-button--success) {
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%) !important;
  border-color: #15803d !important;
  box-shadow: 0 3px 8px rgba(22,163,74,0.30) !important;
  color: #fff !important;
}
.cutting-instruction-container :deep(.el-button--success:hover) {
  background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%) !important;
  box-shadow: 0 6px 16px rgba(22,163,74,0.40) !important;
}

/* danger – 赤 */
.cutting-instruction-container :deep(.el-button--danger) {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
  border-color: #b91c1c !important;
  box-shadow: 0 3px 8px rgba(220,38,38,0.28) !important;
  color: #fff !important;
}
.cutting-instruction-container :deep(.el-button--danger:hover) {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
  box-shadow: 0 6px 16px rgba(220,38,38,0.38) !important;
}

/* warning – オレンジ */
.cutting-instruction-container :deep(.el-button--warning) {
  background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important;
  border-color: #b45309 !important;
  box-shadow: 0 3px 8px rgba(217,119,6,0.32) !important;
  color: #fff !important;
}
.cutting-instruction-container :deep(.el-button--warning:hover) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
  box-shadow: 0 6px 16px rgba(217,119,6,0.40) !important;
}

/* default – グレー */
.cutting-instruction-container :deep(.el-button--default) {
  background: linear-gradient(135deg, #fff 0%, #f9fafb 100%) !important;
  border-color: #e5e7eb !important;
  color: #374151 !important;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08) !important;
}
.cutting-instruction-container :deep(.el-button--default:hover) {
  border-color: #4f46e5 !important;
  color: #2563eb !important;
  background: linear-gradient(135deg, #f3f4f6 0%, #eff6ff 100%) !important;
  box-shadow: 0 4px 12px rgba(37,99,235,0.18) !important;
}

/* 生産ロット card タイトル：上記 default 上書きを打ち消し */
.cutting-instruction-container .section-title :deep(.el-button.title-toolbar-btn--data) {
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%) !important;
  border-color: #c7d2fe !important;
  color: #3730a3 !important;
  box-shadow: 0 1px 2px rgba(49, 46, 129, 0.08) !important;
}
.cutting-instruction-container .section-title :deep(.el-button.title-toolbar-btn--data:hover) {
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%) !important;
  border-color: #818cf8 !important;
  color: #2563eb !important;
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.15) !important;
}
.cutting-instruction-container .section-title :deep(.el-button.title-toolbar-btn--sync) {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%) !important;
  border-color: #6ee7b7 !important;
  color: #047857 !important;
  box-shadow: 0 1px 2px rgba(5, 150, 105, 0.1) !important;
}
.cutting-instruction-container .section-title :deep(.el-button.title-toolbar-btn--sync:hover) {
  background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%) !important;
  border-color: #34d399 !important;
  color: #065f46 !important;
  box-shadow: 0 2px 6px rgba(16, 185, 129, 0.2) !important;
}

/* 試作追加ボタン */
.btn-trial-add {
  background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%) !important;
  border-color: #6d28d9 !important;
  color: #fff !important;
  box-shadow: 0 3px 8px rgba(124,58,237,0.32) !important;
}
.btn-trial-add:hover {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%) !important;
  box-shadow: 0 6px 16px rgba(124,58,237,0.40) !important;
}

/* ── card section-title（生産ロット一覧：タイトル + ツールバー） ── */
.card-header .section-title {
  font-size: 12px !important;
  font-weight: 700 !important;
  color: #1e1b4b !important;
  display: flex !important;
  align-items: center !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
  row-gap: 6px !important;
  letter-spacing: 0.01em !important;
  flex: 1 1 auto !important;
  min-width: 0 !important;
}
/* ── right-panel hover ── */
.right-panel { transition: box-shadow 0.22s ease !important; }
.right-panel:hover { box-shadow: 0 6px 16px rgba(37,99,235,0.12) !important; }

/* ── 製品詳細リスト compact & hover ── */
.product-detail-list-item {
  transition: background-color 0.12s ease !important;
  padding: 3px 6px !important;
  min-height: 22px !important;
}
.product-detail-list-item:hover { background: #f0f9ff !important; }
.product-detail-list-item .detail-label { font-size: 10px !important; font-weight: 700 !important; }
.product-detail-list-item .detail-value { font-size: 10px !important; font-weight: 500 !important; }

/* ── ページネーション compact ── */
.pagination-wrap { padding: 4px 0 0 !important; }
.pagination-wrap :deep(.el-pagination) { font-size: 10px !important; }

/* ── セクションタイトルアンダーライン ── */
.cutting-mgmt-title { position: relative; padding-bottom: 2px; display: flex; align-items: center; }
.cutting-mgmt-title::after {
  content: '';
  display: block;
  position: absolute;
  bottom: -2px; left: 0;
  width: 100%; height: 2px;
  border-radius: 1px;
  background: currentColor;
  opacity: 0.18;
}

/* ── right-panel-title compact ── */
.right-panel-title { margin-bottom: 6px !important; padding-bottom: 4px !important; font-size: 11px !important; }

/* ── el-table global polish ── */
.cutting-instruction-container :deep(.el-table th.el-table__cell) {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%) !important;
  font-weight: 700 !important;
  font-size: 10px !important;
  color: #3730a3 !important;
  padding: 4px 0 !important;
  letter-spacing: 0.02em !important;
}
.cutting-instruction-container :deep(.el-table td.el-table__cell) {
  padding: 3px 0 !important;
  font-size: 10px !important;
}
.cutting-instruction-container :deep(.el-table .el-table__row:hover > td) {
  background: linear-gradient(90deg, #f0f9ff 0%, #f3f4f6 100%) !important;
  transition: background-color 0.15s ease !important;
}

/* ── input/select focus glow ── */
.cutting-instruction-container :deep(.el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 2px rgba(37,99,235,0.25) !important;
  transition: box-shadow 0.18s ease !important;
}
.cutting-instruction-container :deep(.el-select .el-input__wrapper:focus-within) {
  box-shadow: 0 0 0 2px rgba(37,99,235,0.25) !important;
}

/* ── drop-zone ── */
.drop-zone-active {
  outline: 2px dashed #2563eb !important;
  outline-offset: -2px;
  background: rgba(37,99,235,0.06) !important;
  transition: background 0.15s ease !important;
}

/* ── 使用材料数 汇总表 ── */
.usage-count-item {
  color: #dc2626;
  font-weight: 700;
  background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
  padding: 2px 6px;
  border-radius: 4px;
}
.usage-summary-row {
  margin-top: 0;
}
.usage-summary-col {
  padding: 0;
}
.usage-summary-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  flex-shrink: 0;
}
.usage-summary-title-row--with-date {
  flex-wrap: wrap;
  gap: 8px;
}
.usage-summary-date-wrap {
  display: flex;
  align-items: center;
  gap: 4px;
}
.usage-summary-date-wrap .el-date-editor { width: 120px; }
.usage-summary-table-wrap {
  min-height: 48px;
  overflow-x: auto;
  overflow-y: auto;
  height: 340px;
  flex-shrink: 0;
}
.usage-summary-table--list th,
.usage-summary-table--list td {
  min-width: 70px;
}
.usage-summary-table--list th:first-child,
.usage-summary-table--list td:first-child { min-width: 80px; }
.usage-summary-table--list th:nth-child(2),
.usage-summary-table--list td:nth-child(2) { min-width: 100px; }
.usage-summary-table--list th:nth-child(3),
.usage-summary-table--list td:nth-child(3) { min-width: 100px; }
.usage-summary-table--list th:nth-child(4),
.usage-summary-table--list td:nth-child(4) { min-width: 80px; }
.usage-summary-table--list th:nth-child(5),
.usage-summary-table--list td:nth-child(5) { min-width: 80px; }
.usage-summary-table--list th:nth-child(6),
.usage-summary-table--list td:nth-child(6) { min-width: 100px; }
.usage-summary-table--list td.usage-mgmt-empty {
  color: #999;
  font-style: italic;
}
.usage-summary-empty {
  padding: 8px 0;
  color: #888;
  font-size: 12px;
}
.usage-summary-footer {
  display: flex;
  gap: 12px;
  padding: 6px 0 4px;
  font-size: 12px;
  color: #555;
  flex-shrink: 0;
  border-top: 1px solid #eee;
  margin-top: 4px;
}
.usage-summary-footer-item {
  white-space: nowrap;
}
.usage-summary-footer--reflected {
  color: #15803d;
}
.usage-summary-footer--not-reflected {
  color: #b45309;
}
.usage-summary-title-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.usage-reflected-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  margin-left: 8px;
}
.usage-reflected-badge.is-reflected {
  color: #16a34a;
  background: #dcfce7;
}
.usage-reflected-badge.is-not-reflected {
  color: #b45309;
  background: #fffbeb;
}
/* 切断指示テーブル内の使用材料反映列 */
.usage-reflected-tag {
  color: #16a34a;
  font-weight: 600;
  font-size: 11px;
}
.usage-not-reflected-tag {
  color: #b45309;
  font-size: 11px;
}
.usage-sub-manual-tag {
  color: #64748b;
  font-size: 11px;
  font-style: italic;
}
.usage-summary-wrap--tomorrow .usage-reflected-badge.is-reflected {
  color: #15803d;
  background: #bbf7d0;
}
.usage-summary-wrap--tomorrow .usage-reflected-badge.is-not-reflected {
  color: #9a3412;
  background: #fed7aa;
}
.usage-summary-wrap {
  padding: 8px 10px 10px;
  border-top: 2px solid #e0e7ff;
  background: #fafafa;
  border-radius: 0 0 6px 6px;
  height: 380px;
  display: flex;
  flex-direction: column;
  min-height: 380px;
}
.usage-summary-wrap--tomorrow {
  background: #f0fdf4;
  border-top-color: #bbf7d0;
}
.usage-summary-title {
  font-size: 11px;
  font-weight: 600;
  color: #6366f1;
  margin-bottom: 0;
}
.usage-summary-wrap--tomorrow .usage-summary-title {
  color: #16a34a;
}
.usage-summary-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.usage-summary-table th,
.usage-summary-table td {
  padding: 3px 8px;
  border: 1px solid #e0e7ff;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.usage-count-col {
  width: 120px;
  text-align: right;
}
.usage-summary-wrap--tomorrow .usage-summary-table th,
.usage-summary-wrap--tomorrow .usage-summary-table td {
  border-color: #bbf7d0;
}
.usage-summary-table th {
  background: #eef2ff;
  color: #4338ca;
  font-weight: 600;
}
.usage-summary-wrap--tomorrow .usage-summary-table th {
  background: #dcfce7;
  color: #15803d;
}
.usage-count-cell {
  text-align: right;
  font-weight: 600;
  color: #d97706;
}
.usage-summary-total-row td {
  background: #f5f3ff;
  font-weight: 700;
  color: #4338ca;
}
.usage-summary-wrap--tomorrow .usage-summary-total-row td {
  background: #f0fdf4;
  color: #15803d;
}
/* 材料ラベル（ホバーで下線ヒント） */
.usage-material-label {
  cursor: default;
  text-decoration: underline dotted #94a3b8;
  text-underline-offset: 2px;
  transition: color 0.15s;
}
.usage-material-label:hover {
  color: #4338ca;
  text-decoration-color: #4338ca;
}

/* ── 材料 tooltip（グローバル）── */
:global(.usage-product-tooltip) {
  max-width: 300px !important;
  padding: 8px 10px !important;
}
.usage-tooltip-title {
  font-size: 11px;
  font-weight: 700;
  color: #c7d2fe;
  margin-bottom: 4px;
  letter-spacing: 0.02em;
}
.usage-tooltip-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  font-size: 11px;
  line-height: 1.6;
}
.usage-tooltip-cd {
  color: #fbbf24;
  font-family: monospace;
  white-space: nowrap;
  min-width: 60px;
}
.usage-tooltip-name {
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── 使用数反映ダイアログ ── */
.usage-overwrite-warning {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  color: #92400e;
  font-size: 12px;
  margin-bottom: 10px;
}
.usage-preview-desc {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 8px;
}
.usage-preview-table {
  font-size: 12px;
}
.usage-preview-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
  padding: 20px 0;
}
.usage-dialog-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  padding: 30px 0;
  color: #94a3b8;
  font-size: 13px;
}

/* ── 指定日ダイアログ ── */
.specified-date-dialog .el-dialog__body {
  padding: 16px 20px;
}
.specified-date-dialog-body {
  min-height: 120px;
}
.specified-date-controls {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.specified-date-picker {
  width: 180px;
}
.specified-date-today-btn {
  margin-right: 4px;
}
.specified-date-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.usage-preview-desc {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 10px;
}
.usage-preview-table.specified-date-table .el-table__cell {
  text-align: center;
}
.usage-preview-table.specified-date-table .cell {
  text-align: center;
  justify-content: center;
}
.specified-date-total {
  text-align: center;
  font-weight: 700;
  color: #d97706;
  font-size: 14px;
  margin-top: 12px;
  padding: 8px 0 0;
}
</style>
