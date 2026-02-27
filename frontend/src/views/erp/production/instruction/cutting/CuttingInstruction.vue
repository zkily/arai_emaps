<template>
  <div class="cutting-instruction-container">
    <div class="page-header">
      <div class="header-left">
        <div class="header-title">
          <h1>切断指示管理</h1>
        </div>
      </div>
    </div>

    <!-- 上部：生産バッチ 50% + 右侧 50% -->
    <div class="plan-row">
      <div class="plan-section plan-section-left">
        <el-card class="section-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div class="section-title">
              <el-icon size="18"><Calendar /></el-icon>
              <span>生産バッチ一覧</span>
              <el-button type="default" size="small" class="title-right-btn" @click="openDataManagementDialog">
                データ管理
              </el-button>
            </div>
            <div class="header-actions">
              <el-select
                v-model="selectedScheduleMonth"
                placeholder="生産月"
                clearable
                size="small"
                style="width: 100px"
                @change="loadPlans"
              >
                <el-option
                  v-for="m in scheduleMonths"
                  :key="m.value"
                  :label="m.label"
                  :value="m.value"
                />
              </el-select>
              <el-button
                type="primary"
                size="small"
                :loading="generateFromScheduleLoading"
                :disabled="!selectedScheduleMonth"
                @click="generateFromSchedule"
              >
                切断指示生成
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
                @change="loadPlans"
              >
                <el-option
                  v-for="machine in machineOptions"
                  :key="machine.machine_name"
                  :label="machine.machine_name"
                  :value="machine.machine_name"
                />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="small" @click="openNewRecordDialog">+ 新規追加</el-button>
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
          <div v-if="dragOverZone === 'batchList'" class="plan-batch-drop-hint">ここにドロップで切断指示をバッチへ戻す</div>
          <div v-show="planListForTable.length > 0" class="plan-batch-table-inner">
            <div class="plan-batch-thead">
              <div class="plan-batch-tr">
                <div class="plan-batch-th">生産月</div>
                <div class="plan-batch-th">ライン</div>
                <div class="plan-batch-th">順位</div>
                <div class="plan-batch-th">製品名</div>
                <div class="plan-batch-th">計画数</div>
                <div class="plan-batch-th">原材料</div>
                <div class="plan-batch-th">ロット数</div>
                <div class="plan-batch-th">No</div>
                <div class="plan-batch-th">生産数</div>
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
                <div class="plan-batch-td">{{ formatDateOnly(String(row.production_month ?? '')) || '-' }}</div>
                <div class="plan-batch-td">{{ row.production_line ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.priority_order ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.product_name || row.product_cd || '-' }}</div>
                <div class="plan-batch-td">{{ row.planned_quantity ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.material_name ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.production_lot_size ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.lot_number ?? '-' }}</div>
                <div class="plan-batch-td">{{ row.actual_production_quantity ?? '-' }}</div>
                <div class="plan-batch-td plan-batch-td-actions">
                  <el-button type="danger" link size="small" title="削除" @click.stop="deletePlanBatch(row)">
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
            :total="planPagination.total"
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
              <div class="detail-row"><span class="detail-label">製品CD</span><span class="detail-value">{{ productDetail.product_cd ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">製品名</span><span class="detail-value">{{ productDetail.product_name ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">生産ロット</span><span class="detail-value">{{ productDetail.lot_size ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">材料</span><span class="detail-value">{{ productDetail.material_cd ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">切断長</span><span class="detail-value">{{ productDetail.cut_length ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">面取長</span><span class="detail-value">{{ productDetail.chamfer_length ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">展開長</span><span class="detail-value">{{ productDetail.developed_length ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">端材長</span><span class="detail-value">{{ productDetail.scrap_length ?? '-' }}</span></div>
              <div class="detail-row"><span class="detail-label">取数</span><span class="detail-value">{{ productDetail.take_count ?? '-' }}</span></div>
            </template>
            <div v-else-if="!productDetailLoading" class="right-panel-placeholder">該当製品なし</div>
          </div>
        </div>
        <!-- 下：設備能率（equipment_efficiency 表・該当製品） -->
        <div class="right-panel-bottom">
          <div class="right-panel-title">設備能率</div>
          <div v-if="!selectedProductCd" class="right-panel-placeholder">一覧で製品をクリック</div>
          <div v-else v-loading="equipmentEfficiencyLoading" class="equipment-efficiency-body">
            <el-table v-if="equipmentEfficiencyList.length" :data="equipmentEfficiencyList" size="small" max-height="220">
              <el-table-column prop="machines_name" label="設備名" min-width="100" show-overflow-tooltip />
              <el-table-column prop="efficiency_rate" label="能率" width="80" align="right" />
            </el-table>
            <div v-else-if="!equipmentEfficiencyLoading" class="right-panel-placeholder">該当データなし</div>
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
              <el-button type="primary" size="small" :loading="issueCuttingInstructionSheetLoading" @click="issueCuttingInstructionSheet">指示書発行</el-button>
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
          <div v-loading="cuttingManagementLoading" class="cutting-mgmt-table-wrap">
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
                <div class="cutting-mgmt-drop-hint" v-if="dragOverZone === 'cuttingManagement'">ここにドロップでバッチを切断指示へ移行</div>
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
                        <el-button type="info" link size="small" title="キャンセル（Esc）" @click.stop="cancelEditProductionDay">×</el-button>
                      </span>
                    </template>
                    <template v-else>{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
                  </div>
                  <div class="cutting-mgmt-td">{{ row.cutting_machine ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.product_name ?? row.product_cd ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.material_name ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.actual_production_quantity ?? '-' }}</div>
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
            <div v-if="cuttingManagementList.length" class="cutting-mgmt-tfoot-wrap">
              <div class="cutting-mgmt-tfoot">
                <div class="cutting-mgmt-tr">
                  <div class="cutting-mgmt-td cutting-mgmt-td-total-label">合計</div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-total-value">{{ cuttingTodayTotal.quantity }}</div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-total-value">{{ cuttingTodayTotal.time ?? '-' }}</div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-actions"></div>
                </div>
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
            <div class="cutting-mgmt-table-inner cutting-mgmt-table-inner--tomorrow">
              <div class="cutting-mgmt-thead">
                <div class="cutting-mgmt-tr">
                  <div class="cutting-mgmt-th">CD</div>
                  <div class="cutting-mgmt-th">生産日</div>
                  <div class="cutting-mgmt-th">切断機</div>
                  <div class="cutting-mgmt-th">製品名</div>
                  <div class="cutting-mgmt-th">生産数</div>
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
                <div class="cutting-mgmt-drop-hint" v-if="dragOverZone === 'cuttingManagement'">ここにドロップでバッチを切断指示へ移行</div>
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
                        <el-button type="info" link size="small" title="キャンセル（Esc）" @click.stop="cancelEditProductionDay">×</el-button>
                      </span>
                    </template>
                    <template v-else>{{ formatDateOnly(String(row.production_day ?? '')) || '-' }}</template>
                  </div>
                  <div class="cutting-mgmt-td">{{ row.cutting_machine ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.product_name ?? row.product_cd ?? '-' }}</div>
                  <div class="cutting-mgmt-td">{{ row.actual_production_quantity ?? '-' }}</div>
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
            <div v-if="cuttingManagementListTomorrow.length" class="cutting-mgmt-tfoot-wrap cutting-mgmt-tfoot-wrap--tomorrow">
              <div class="cutting-mgmt-tfoot">
                <div class="cutting-mgmt-tr">
                  <div class="cutting-mgmt-td cutting-mgmt-td-total-label">合計</div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-total-value">{{ cuttingTomorrowTotal.quantity }}</div>
                  <div class="cutting-mgmt-td"></div>
                  <div class="cutting-mgmt-td cutting-mgmt-td-total-value">{{ cuttingTomorrowTotal.time ?? '-' }}</div>
                </div>
              </div>
            </div>
            <div v-if="!cuttingManagementListTomorrow.length && !cuttingManagementLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
      </div>
      <!-- 第2行：面取指示 | カンバン発行 -->
      <div class="instruction-row instruction-two-cols">
        <div class="instruction-col chamfering-management-section">
          <div class="cutting-mgmt-header">
            <span class="cutting-mgmt-title">面取指示</span>
          </div>
          <div v-loading="chamferingManagementLoading" class="cutting-mgmt-table-wrap">
            <el-table
              :data="chamferingManagementList"
              size="small"
              class="cutting-mgmt-table"
              max-height="260"
              stripe
            >
              <el-table-column prop="production_day" label="生産日" width="92" align="center">
                <template #default="{ row }">{{ formatDateOnly(String(row.production_day ?? '')) }}</template>
              </el-table-column>
              <el-table-column prop="production_line" label="ライン" width="72" show-overflow-tooltip />
              <el-table-column prop="product_name" label="製品名" min-width="100" show-overflow-tooltip />
              <el-table-column prop="actual_production_quantity" label="数" width="48" align="center" />
              <el-table-column prop="chamfering_length" label="面取長" width="72" align="right" />
              <el-table-column prop="production_completed_check" label="完了" width="52" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.production_completed_check" type="success" size="small">済</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="!chamferingManagementList.length && !chamferingManagementLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
        <div class="instruction-col kanban-issuance-section">
          <div class="cutting-mgmt-header">
            <span class="cutting-mgmt-title">カンバン発行</span>
          </div>
          <div v-loading="kanbanIssuanceLoading" class="cutting-mgmt-table-wrap">
            <el-table
              :data="kanbanIssuanceList"
              size="small"
              class="cutting-mgmt-table"
              max-height="260"
              stripe
            >
              <el-table-column prop="process_type" label="工程" width="80" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.process_type === 'cutting'" type="info" size="small">切断</el-tag>
                  <el-tag v-else-if="row.process_type === 'chamfering'" type="warning" size="small">面取</el-tag>
                  <span v-else>{{ row.process_type }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="kanban_no" label="カンバン番号" min-width="140" show-overflow-tooltip />
              <el-table-column prop="issue_date" label="発行日" width="92" align="center" />
              <el-table-column prop="status" label="状態" width="80" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.status === 'pending'" type="warning" size="small">待発行</el-tag>
                  <el-tag v-else-if="row.status === 'issued'" size="small">発行済</el-tag>
                  <el-tag v-else-if="row.status === 'completed'" type="success" size="small">完了</el-tag>
                  <span v-else>{{ row.status }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center" fixed="right">
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
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="!kanbanIssuanceList.length && !kanbanIssuanceLoading" class="cutting-mgmt-empty">データなし</div>
          </div>
        </div>
      </div>
    </div>

    <!-- バッチ→切断：生産日・切断機指定ダイアログ -->
    <el-dialog
      v-model="moveToCuttingDialogVisible"
      width="480px"
      :close-on-click-modal="false"
      class="move-to-cutting-dialog"
      @close="pendingBatchRow = null"
    >
      <template #header>
        <div class="move-to-cutting-dialog__header">
          <span class="move-to-cutting-dialog__title">切断指示の登録</span>
        </div>
      </template>
      <el-form :model="moveToCuttingForm" label-width="72px" label-position="left" class="move-to-cutting-form">
        <el-form-item label="生産日" class="move-to-cutting-form-item">
          <div class="move-to-cutting-date-row">
            <el-date-picker
              v-model="moveToCuttingForm.production_day"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="生産日"
              size="small"
              class="move-to-cutting-date-picker"
            />
            <div class="move-to-cutting-date-shortcuts">
              <el-button size="small" @click="moveToCuttingForm.production_day = shiftDate(moveToCuttingForm.production_day || getTodayString(), -1)">前日</el-button>
              <el-button size="small" type="primary" @click="moveToCuttingForm.production_day = getTodayString()">今日</el-button>
              <el-button size="small" @click="moveToCuttingForm.production_day = shiftDate(moveToCuttingForm.production_day || getTodayString(), 1)">翌日</el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="切断機" class="move-to-cutting-form-item">
          <div class="move-to-cutting-machine-btns">
            <el-button
              v-for="m in cuttingMachineOptionsFiltered"
              :key="m.machine_name"
              size="small"
              :type="moveToCuttingForm.cutting_machine === m.machine_name ? 'primary' : 'default'"
              @click="moveToCuttingForm.cutting_machine = m.machine_name"
            >
              {{ m.machine_name }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="move-to-cutting-dialog__footer">
          <el-button size="small" @click="moveToCuttingDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" :loading="moveToCuttingSubmitting" @click="submitMoveToCutting">登録</el-button>
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
        <el-form-item label="生産数" class="cutting-edit-form-item">
          <el-input
            v-model="cuttingEditForm.actual_production_quantity"
            placeholder="生産数"
            size="small"
            clearable
          />
        </el-form-item>
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
        <el-form-item label="備考" class="cutting-edit-remarks cutting-edit-form-item">
          <div class="cutting-edit-remarks-btns">
            <el-button size="small" class="cutting-edit-tag-btn" @click="appendCuttingRemark('取合せ・試作')">取合せ・試作</el-button>
            <el-button size="small" class="cutting-edit-tag-btn" @click="appendCuttingRemark('取合せ')">取合せ</el-button>
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

    <!-- 生産バッチ：双击编辑（テーブル全項目） -->
    <el-dialog
      v-model="planEditDialogVisible"
      width="min(96vw, 900px)"
      :close-on-click-modal="false"
      class="plan-edit-dialog"
      @close="editingPlanId = null"
    >
      <template #header>
        <div class="ped-header">
          <div class="ped-header-icon"><el-icon size="16"><Calendar /></el-icon></div>
          <div class="ped-header-text">
            <span class="ped-title">バッチ内容編集</span>
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
              <el-input v-model="planEditForm.management_code" placeholder="管理コード" size="small" clearable />
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

    <!-- データ管理：instruction_plans 全件表示＋筛选 -->
    <el-dialog
      v-model="dataManagementDialogVisible"
      title="データ管理（instruction_plans）"
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
            <el-select v-model="dataManagementFilter.equipment" placeholder="全部" clearable filterable style="width: 120px">
              <el-option label="（全部）" value="" />
              <el-option v-for="line in dataManagementLineOptions" :key="line" :label="line" :value="line" />
            </el-select>
          </el-form-item>
          <el-form-item label="製品名">
            <el-select v-model="dataManagementFilter.product_name" placeholder="全部" clearable filterable style="width: 160px">
              <el-option label="（全部）" value="" />
              <el-option v-for="name in dataManagementProductNameOptions" :key="name" :label="name" :value="name" />
            </el-select>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="small" @click="openNewRecordDialog">+ 新規追加</el-button>
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
          <el-table-column prop="production_line" label="ライン" width="80">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'production_line')">
                <el-input :model-value="row.production_line ?? ''" size="small" @update:model-value="(v) => (row.production_line = v ?? '')" @blur="saveDataManagementCell(row, 'production_line', row.production_line ?? '')" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'production_line')">{{ row.production_line || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 3. 順位 -->
          <el-table-column prop="priority_order" label="順位" width="58" align="right">
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
          <el-table-column prop="material_name" label="原材料" width="100" show-overflow-tooltip>
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'material_name')">
                <el-input :model-value="row.material_name ?? ''" size="small" @update:model-value="(v) => (row.material_name = v ?? '')" @blur="saveDataManagementCell(row, 'material_name', row.material_name ?? '')" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'material_name')">{{ row.material_name || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 6. 計画数 -->
          <el-table-column prop="planned_quantity" label="計画数" width="72" align="right">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'planned_quantity')">
                <el-input-number :model-value="row.planned_quantity ?? null" size="small" :min="0" controls-position="right" style="width: 100%" @change="(v: number | undefined) => saveDataManagementCell(row, 'planned_quantity', v ?? null)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'planned_quantity')">{{ row.planned_quantity ?? '-' }}</span>
            </template>
          </el-table-column>

          <!-- 7. ロット数 -->
          <el-table-column prop="production_lot_size" label="ロット数" width="72" align="right">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'production_lot_size')">
                <el-input-number :model-value="row.production_lot_size ?? null" size="small" :min="0" controls-position="right" style="width: 100%" @change="(v: number | undefined) => saveDataManagementCell(row, 'production_lot_size', v ?? null)" @blur="dataManagementEditingCell = null" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'production_lot_size')">{{ row.production_lot_size ?? '-' }}</span>
            </template>
          </el-table-column>

          <!-- 8. ロットNo -->
          <el-table-column prop="lot_number" label="ロットNo" width="90">
            <template #default="{ row }">
              <template v-if="isEditingDataCell(row, 'lot_number')">
                <el-input :model-value="row.lot_number ?? ''" size="small" @update:model-value="(v) => (row.lot_number = v ?? '')" @blur="saveDataManagementCell(row, 'lot_number', row.lot_number ?? '')" />
              </template>
              <span v-else class="editable-cell" @dblclick="startEditDataCell(row, 'lot_number')">{{ row.lot_number || '-' }}</span>
            </template>
          </el-table-column>

          <!-- 9. 生産数 -->
          <el-table-column prop="actual_production_quantity" label="生産数" width="72" align="right">
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

    <!-- 新規追加ダイアログ -->
    <el-dialog
      v-model="newRecordDialogVisible"
      title="新規レコード追加"
      width="min(96vw, 640px)"
      :close-on-click-modal="false"
      class="new-record-dialog"
    >
      <el-form :model="newRecordForm" label-width="90px" size="small" class="nr-form">
        <div class="nr-grid">
          <el-form-item label="生産月">
            <el-date-picker v-model="newRecordForm.production_month" type="month" value-format="YYYY-MM" placeholder="YYYY-MM" style="width:100%" />
          </el-form-item>
          <el-form-item label="ライン">
            <el-input v-model="newRecordForm.production_line" placeholder="例: A" />
          </el-form-item>
          <el-form-item label="順位">
            <el-input-number v-model="newRecordForm.priority_order" :min="0" :max="9999" controls-position="right" style="width:100%" />
          </el-form-item>
          <el-form-item label="製品名">
            <el-input v-model="newRecordForm.product_name" placeholder="製品名" />
          </el-form-item>
          <el-form-item label="製品CD">
            <el-input v-model="newRecordForm.product_cd" placeholder="製品CD" />
          </el-form-item>
          <el-form-item label="原材料">
            <el-input v-model="newRecordForm.material_name" placeholder="原材料名" />
          </el-form-item>
          <el-form-item label="計画数">
            <el-input-number v-model="newRecordForm.planned_quantity" :min="0" controls-position="right" style="width:100%" />
          </el-form-item>
          <el-form-item label="ロット数">
            <el-input-number v-model="newRecordForm.production_lot_size" :min="0" controls-position="right" style="width:100%" />
          </el-form-item>
          <el-form-item label="ロットNo">
            <el-input v-model="newRecordForm.lot_number" placeholder="ロットNo" />
          </el-form-item>
          <el-form-item label="生産数">
            <el-input-number v-model="newRecordForm.actual_production_quantity" :min="0" controls-position="right" style="width:100%" />
          </el-form-item>
          <el-form-item label="開始日">
            <el-date-picker v-model="newRecordForm.start_date" type="date" value-format="YYYY-MM-DD" placeholder="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="終了日">
            <el-date-picker v-model="newRecordForm.end_date" type="date" value-format="YYYY-MM-DD" placeholder="YYYY-MM-DD" style="width:100%" />
          </el-form-item>
          <el-form-item label="面取工程">
            <el-switch v-model="newRecordForm.has_chamfering_process" :active-value="1" :inactive-value="0" />
          </el-form-item>
          <el-form-item label="SW工程">
            <el-switch v-model="newRecordForm.has_sw_process" :active-value="1" :inactive-value="0" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="nr-footer">
          <el-button size="small" @click="newRecordDialogVisible = false">取消</el-button>
          <el-button type="primary" size="small" :loading="newRecordSubmitting" @click="createDataManagementRecord">保存</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'CuttingInstruction' })

import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Check, DocumentCopy, Delete, ArrowLeft, ArrowRight, DArrowRight, Warning } from '@element-plus/icons-vue'
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

/** 日付文字列を YYYY-MM-DD で表示（ISO の先頭10文字） */
const formatDateOnly = (v: string | null | undefined) => {
  if (v == null || v === '') return ''
  const s = String(v)
  return s.slice(0, 10)
}

/** 生産バッチ一覧：順位ごとの浅色背景クラス（順位数字で区別） */
function getPlanBatchPriorityClass(order: number | null | undefined): string {
  if (order == null || order === undefined) return 'plan-batch-priority-none'
  const idx = (Number(order) - 1) % 5
  return `plan-batch-priority-${idx}`
}

const planSearchForm = reactive({
  equipment: '',
})

const planPagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0,
})

const plans = ref<CuttingPlanRow[]>([])
const planLoading = ref(false)

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
  take_count?: number | null
  cutting_length?: number | null
  chamfering_length?: number | null
  developed_length?: number | null
  scrap_length?: number | null
  material_name?: string | null
  material_manufacturer?: string | null
  standard_specification?: string | null
  production_completed_check?: number | null
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
/** 切断指示-今日：生産数・生産時間の合計 */
const cuttingTodayTotal = computed(() => {
  const list = cuttingManagementList.value
  let qty = 0
  let time = 0
  for (const row of list) {
    const n = row.actual_production_quantity
    if (n != null && typeof n === 'number' && !Number.isNaN(n)) qty += n
    else if (n != null && String(n).trim() !== '') {
      const v = Number(String(n).trim())
      if (!Number.isNaN(v)) qty += v
    }
    const t = row.production_time
    if (t != null && (typeof t === 'number' || typeof t === 'string')) {
      const tv = typeof t === 'number' ? t : parseFloat(String(t))
      if (!Number.isNaN(tv)) time += tv
    }
  }
  return { quantity: qty, time: time === 0 ? null : Math.round(time * 10) / 10 }
})
/** 切断指示-翌日：生産数・生産時間の合計 */
const cuttingTomorrowTotal = computed(() => {
  const list = cuttingManagementListTomorrow.value
  let qty = 0
  let time = 0
  for (const row of list) {
    const n = row.actual_production_quantity
    if (n != null && typeof n === 'number' && !Number.isNaN(n)) qty += n
    else if (n != null && String(n).trim() !== '') {
      const v = Number(String(n).trim())
      if (!Number.isNaN(v)) qty += v
    }
    const t = row.production_time
    if (t != null && (typeof t === 'number' || typeof t === 'string')) {
      const tv = typeof t === 'number' ? t : parseFloat(String(t))
      if (!Number.isNaN(tv)) time += tv
    }
  }
  return { quantity: qty, time: time === 0 ? null : Math.round(time * 10) / 10 }
})
/** バッチ→切断にドロップ時：生産日・切断機を指定するダイアログ */
const moveToCuttingDialogVisible = ref(false)
const pendingBatchRow = ref<CuttingPlanRow | null>(null)
const moveToCuttingForm = reactive({ production_day: '', cutting_machine: '' })
const moveToCuttingSubmitting = ref(false)
/** 切断指示：双击编辑弹窗 */
const cuttingEditDialogVisible = ref(false)
const editingCuttingId = ref<number | null>(null)
const cuttingEditForm = reactive({
  cutting_machine: '',
  actual_production_quantity: '' as string,
  production_sequence: 1,
  remarks: '',
})
const cuttingEditSubmitting = ref(false)
/** 生産日セル：双击でインライン編集（±1日ボタン + 日期选择） */
const editingProductionDayId = ref<number | null>(null)
const editingProductionDayValue = ref('')
/** 完了切替 loading：当前正在请求的行 id，用于显示该行的 switch loading */
const cuttingCompletedLoading = ref<number>(0)
/** 生産バッチ双击编辑 */
const planEditDialogVisible = ref(false)
const editingPlanId = ref<number | null>(null)
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

/** 新規追加ダイアログ */
const newRecordDialogVisible = ref(false)
const newRecordSubmitting = ref(false)
const newRecordFormDefault = () => ({
  production_month: '',
  production_line: '',
  priority_order: null as number | null,
  product_cd: '',
  product_name: '',
  material_name: '',
  planned_quantity: null as number | null,
  production_lot_size: null as number | null,
  lot_number: '',
  actual_production_quantity: null as number | null,
  start_date: '',
  end_date: '',
  has_chamfering_process: 0 as number,
  has_sw_process: 0 as number,
})
const newRecordForm = reactive(newRecordFormDefault())

function openNewRecordDialog() {
  Object.assign(newRecordForm, newRecordFormDefault())
  newRecordDialogVisible.value = true
}

async function createDataManagementRecord() {
  newRecordSubmitting.value = true
  try {
    const payload: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(newRecordForm)) {
      if (v !== '' && v !== null) payload[k] = v
    }
    const result = await request.post<{ success?: boolean; message?: string }>(
      '/api/plan/batch/create',
      payload
    )
    if ((result as any)?.success) {
      ElMessage.success('レコードを追加しました')
      newRecordDialogVisible.value = false
      loadDataManagementList()
    } else {
      throw new Error((result as any)?.message ?? '追加に失敗しました')
    }
  } catch (e: unknown) {
    ElMessage.error(e instanceof Error ? e.message : '追加に失敗しました')
  } finally {
    newRecordSubmitting.value = false
  }
}

/** 編集中セル: { rowId, prop } */
const dataManagementEditingCell = ref<{ rowId: number; prop: string } | null>(null)
const dataManagementSavingCell = ref(false)
/** 拖拽放置区：バッチ一覧（左）、切断指示 */
const dragOverZone = ref<'batchList' | 'cuttingManagement' | null>(null)
/** 当前拖拽来源：仅用于控制是否显示放置提示（切断内拖拽不显示提示） */
const dragSourceRef = ref<'batchList' | 'cuttingManagement' | null>(null)

/** 面取指示（chamfering_management） */
interface ChamferingManagementRow {
  id?: number
  cutting_management_id?: number | null
  production_month?: string | null
  production_day?: string | null
  production_line?: string | null
  production_order?: number | null
  product_cd?: string | null
  product_name?: string | null
  actual_production_quantity?: number | null
  chamfering_length?: number | null
  production_time?: number | null
  material_name?: string | null
  management_code?: string | null
  production_completed_check?: number | null
  cd?: string | null
  created_at?: string | null
}
const chamferingManagementList = ref<ChamferingManagementRow[]>([])
const chamferingManagementLoading = ref(false)

/** カンバン発行（kanban_issuance）：第一工程のみ待発行→手動発行 */
interface KanbanIssuanceRow {
  id?: number
  process_type?: string | null
  source_id?: number | null
  kanban_no?: string | null
  issue_date?: string | null
  status?: string | null
  created_at?: string | null
}
const kanbanIssuanceList = ref<KanbanIssuanceRow[]>([])
const kanbanIssuanceLoading = ref(false)
const kanbanIssuePendingLoading = ref<number | null>(null)
const dragEnterCount = ref(0)
const DRAG_PLAN_KEY = 'cutting-plan-row'

/** 右侧上：製品情報（products 表） */
interface ProductDetail {
  product_cd?: string
  product_name?: string
  lot_size?: number | null
  material_cd?: string | null
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

/** 拖拽中不触发点击 */
const isDragging = ref(false)

/** 生産バッチ一覧のクライアント側ページネーション用 */
const planListForTable = computed(() => {
  const start = (planPagination.currentPage - 1) * planPagination.pageSize
  return plans.value.slice(start, start + planPagination.pageSize)
})

// 生産月：默认 1月～12月（当年），value 格式 YYYY-MM；API 有数据时会被替换
const currentYear = new Date().getFullYear()
const scheduleMonths = ref<{ value: string; label: string }[]>(
  Array.from({ length: 12 }, (_, i) => ({
    value: `${currentYear}-${String(i + 1).padStart(2, '0')}`,
    label: `${i + 1}月`,
  }))
)
const selectedScheduleMonth = ref('')
const generateFromScheduleLoading = ref(false)

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

const handlePlanSizeChange = (size: number) => {
  planPagination.pageSize = size
  loadPlans()
}

const handlePlanCurrentChange = (page: number) => {
  planPagination.currentPage = page
  loadPlans()
}

const loadScheduleMonths = async () => {
  try {
    const result = (await request.get('/api/plan/batch/schedule-months')) as {
      success?: boolean
      data?: { value: string; label: string }[]
    }
    if (result?.success && Array.isArray(result.data) && result.data.length > 0) {
      scheduleMonths.value = result.data
    }
  } catch (e) {
    console.error('計画月一覧の取得に失敗:', e)
  }
}

const generateFromSchedule = async () => {
  if (!selectedScheduleMonth.value) {
    ElMessage.warning('生産月を選択してください')
    return
  }
  try {
    await ElMessageBox.confirm(
      `「${scheduleMonths.value.find((m) => m.value === selectedScheduleMonth.value)?.label ?? selectedScheduleMonth.value}」の計画から生産バッチを生成しますか？同一月の既存バッチ（計画由来）は上書きされます。`,
      'バッチ生成の確認',
      { confirmButtonText: '生成', cancelButtonText: '取消', type: 'warning' }
    )
  } catch {
    return
  }
  generateFromScheduleLoading.value = true
  try {
    const result = await request.post<{ success?: boolean; message?: string; detail?: string }>(
      '/api/plan/batch/generate-from-schedule',
      { month: selectedScheduleMonth.value }
    )
    if ((result as any)?.success) {
      ElMessage.success((result as any).message ?? '生産バッチを生成しました')
      loadPlans()
    } else {
      const errMsg =
        (typeof (result as any)?.detail === 'string' ? (result as any).detail : (result as any)?.message) ??
        'バッチ生成に失敗しました'
      ElMessage.error(errMsg)
    }
  } catch (e) {
    console.error('バッチ生成に失敗:', e)
    ElMessage.error('バッチ生成に失敗しました')
  } finally {
    generateFromScheduleLoading.value = false
  }
}

const loadPlans = async () => {
  planPagination.currentPage = 1
  planLoading.value = true
  try {
    const params: Record<string, string> = {}
    if (selectedScheduleMonth.value) params.production_month = selectedScheduleMonth.value
    if (planSearchForm.equipment) params.equipment = planSearchForm.equipment
    const result = await request.get<{ success?: boolean; data?: CuttingPlanRow[]; message?: string }>(
      '/api/plan/batch/list',
      { params }
    )
    if ((result as any)?.success) {
      plans.value = ((result as any).data ?? []) as CuttingPlanRow[]
      planPagination.total = plans.value.length
    } else {
      throw new Error((result as any)?.message ?? 'データの取得に失敗しました')
    }
  } catch (error) {
    console.error('計画リストの読み込みに失敗:', error)
    ElMessage.error('計画データの読み込みに失敗しました')
    plans.value = []
    planPagination.total = 0
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

/** 生産バッチ1件を削除（確認ダイアログ後） */
async function deletePlanBatch(row: CuttingPlanRow) {
  const id = row.id
  if (id == null) return
  try {
    await ElMessageBox.confirm(
      `このバッチ（製品: ${row.product_name ?? row.product_cd ?? ''}）を削除しますか？`,
      '削除の確認',
      { confirmButtonText: '削除', cancelButtonText: 'キャンセル', type: 'warning' }
    )
    await request.delete(`/api/plan/batch/${id}`)
    ElMessage.success('削除しました')
    loadPlans()
  } catch (e) {
    if ((e as string) === 'cancel') return
    const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (e as { message?: string })?.message
      ?? '削除に失敗しました'
    ElMessage.error(String(msg))
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
  // 切断指示内拖拽排序时不显示「バッチを切断指示へ移行」提示；仅从バッチ拖入时显示
  if (zone === 'cuttingManagement' && dragSourceRef.value === 'cuttingManagement') return
  if (zone === 'batchList' && dragSourceRef.value === 'batchList') return
  dragOverZone.value = zone
}

function onDragLeave(_zone: 'batchList' | 'cuttingManagement') {
  dragEnterCount.value = Math.max(0, dragEnterCount.value - 1)
  if (dragEnterCount.value === 0) dragOverZone.value = null
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
    ElMessage.warning('このデータはバッチに戻せません（IDがありません）')
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
    ElMessage.success('生産バッチに戻しました（切断・面取・カンバンを削除済み）')
    loadPlans()
    loadCuttingManagement()
    loadChamferingManagement()
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? 'バッチへの戻しに失敗しました'
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
    ElMessage.warning('このバッチは移行できません（IDがありません）')
    return
  }
  const productionMonth = String(row.production_month ?? '').slice(0, 7)
  if (!productionMonth || productionMonth.length < 7) {
    ElMessage.warning('生産月が不正です')
    return
  }
  const today = new Date()
  moveToCuttingForm.production_day = today.getFullYear() + '-' + String(today.getMonth() + 1).padStart(2, '0') + '-' + String(today.getDate()).padStart(2, '0')
  moveToCuttingForm.cutting_machine = cuttingMachineOptionsFiltered.value[0]?.machine_name ?? ''
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
    ElMessage.success('切断指示に登録しました（面取工程ありの場合は面取指示・カンバン待発行も登録）')
    moveToCuttingDialogVisible.value = false
    pendingBatchRow.value = null
    loadPlans()
    loadCuttingManagement()
    loadChamferingManagement()
    loadKanbanIssuance()
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
  planEditDialogVisible.value = true
}

async function savePlanEdit() {
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
      management_code: planEditForm.management_code || null,
      take_count: planEditForm.take_count,
      cutting_length: planEditForm.cutting_length,
      chamfering_length: planEditForm.chamfering_length,
      developed_length: planEditForm.developed_length,
      scrap_length: planEditForm.scrap_length,
      material_name: planEditForm.material_name || null,
      material_manufacturer: planEditForm.material_manufacturer || null,
      standard_specification: planEditForm.standard_specification || null,
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

function openCuttingEditDialog(row: CuttingManagementRow) {
  if (row.id == null) return
  editingCuttingId.value = row.id
  cuttingEditForm.cutting_machine = (row.cutting_machine ?? '') || ''
  cuttingEditForm.actual_production_quantity = row.actual_production_quantity != null ? String(row.actual_production_quantity) : ''
  cuttingEditForm.production_sequence = row.production_sequence ?? 1
  cuttingEditForm.remarks = (row.remarks ?? '') || ''
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
    await request.patch(`/api/plan/cutting-management/${id}`, {
      cutting_machine: cuttingEditForm.cutting_machine?.trim() || null,
      actual_production_quantity: Number.isNaN(qtyNum) ? 0 : qtyNum,
      production_sequence: cuttingEditForm.production_sequence,
      remarks: cuttingEditForm.remarks?.trim() || null,
    })
    ElMessage.success('保存しました')
    cuttingEditDialogVisible.value = false
    loadCuttingManagement()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '保存に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    cuttingEditSubmitting.value = false
  }
}

/** 生産日セル：双击でインライン編集開始 */
function startEditProductionDay(row: CuttingManagementRow) {
  if (row.id == null) return
  editingProductionDayId.value = row.id
  editingProductionDayValue.value = formatDateOnly(String(row.production_day ?? '')) || getTodayString()
}

/** 生産日を保存（PATCH）して編集終了 */
async function saveProductionDay(row: CuttingManagementRow, dateStr: string) {
  const id = row.id
  if (id == null) return
  const d = dateStr.slice(0, 10)
  if (!d) return
  try {
    await request.patch(`/api/plan/cutting-management/${id}`, { production_day: d })
    ;(row as { production_day?: string }).production_day = d
    ElMessage.success('生産日を更新しました')
    editingProductionDayId.value = null
    loadCuttingManagement()
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

/** 顺延：未完了分を翌日へ分割（当日完成数 + 翌日行を新規） */
const splitToNextDayDialogVisible = ref(false)
const splitDialogRow = ref<CuttingManagementRow | null>(null)
const splitTodayQuantityInput = ref('0')
const splitNextDay = ref('')
const splitToNextDaySubmitting = ref(false)

function onSplitTodayQuantityInput(val: string) {
  const s = val.replace(/\D/g, '')
  splitTodayQuantityInput.value = s
}

function openSplitToNextDayDialog(row: CuttingManagementRow) {
  const total = row.actual_production_quantity ?? 0
  if (total <= 0) return
  splitDialogRow.value = row
  splitTodayQuantityInput.value = '0'
  splitNextDay.value = shiftDate(String(row.production_day ?? ''), 1)
  splitToNextDayDialogVisible.value = true
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
      'この切断指示を削除しますか？紐づく面取指示・カンバン発行も削除されます。',
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
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
      ?? (err as { message?: string })?.message
      ?? '削除に失敗しました'
    ElMessage.error(String(msg))
  }
}

async function loadChamferingManagement() {
  chamferingManagementLoading.value = true
  try {
    const params: Record<string, string> = {}
    if (selectedScheduleMonth.value) params.production_month = selectedScheduleMonth.value
    const result = await request.get<{ success?: boolean; data?: ChamferingManagementRow[] }>(
      '/api/plan/chamfering-management/list',
      { params: { ...params, limit: 2000 } }
    )
    chamferingManagementList.value = (result as any)?.success ? ((result as any).data ?? []) : []
  } catch (e) {
    console.error('面取指示一覧の取得に失敗:', e)
    chamferingManagementList.value = []
  } finally {
    chamferingManagementLoading.value = false
  }
}

async function loadKanbanIssuance() {
  kanbanIssuanceLoading.value = true
  try {
    const result = await request.get<{ success?: boolean; data?: KanbanIssuanceRow[] }>(
      '/api/plan/kanban-issuance/list',
      { params: { limit: 1000 } }
    )
    kanbanIssuanceList.value = (result as any)?.success ? ((result as any).data ?? []) : []
  } catch (e) {
    console.error('カンバン発行一覧の取得に失敗:', e)
    kanbanIssuanceList.value = []
  } finally {
    kanbanIssuanceLoading.value = false
  }
}

/** 待発行カンバンを手動で発行 */
async function issuePendingKanban(kanbanId: number) {
  kanbanIssuePendingLoading.value = kanbanId
  try {
    const res = await request.post<{ success?: boolean; kanban_no?: string }>(
      `/api/plan/kanban-issuance/${kanbanId}/issue`
    )
    ElMessage.success((res as any)?.kanban_no ? `カンバン発行: ${(res as any).kanban_no}` : 'カンバンを発行しました')
    loadKanbanIssuance()
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ?? (err as { message?: string })?.message ?? 'カンバン発行に失敗しました'
    ElMessage.error(String(msg))
  } finally {
    kanbanIssuePendingLoading.value = null
  }
}

async function loadCuttingManagement() {
  cuttingManagementLoading.value = true
  const baseParams: Record<string, string> = {}
  if (selectedScheduleMonth.value) baseParams.production_month = selectedScheduleMonth.value
  if (cuttingMachineFilter.value) baseParams.cutting_machine = cuttingMachineFilter.value
  const todayParam = selectedDateToday.value ? String(selectedDateToday.value).slice(0, 10) : ''
  const tomorrowParam = selectedDateTomorrow.value ? String(selectedDateTomorrow.value).slice(0, 10) : ''
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
  }
}

/** 指示書発行：指定日の全データを切断機ごとに1ページずつ A5 横向で印刷 */
const issueCuttingInstructionSheetLoading = ref(false)
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
      .instruction-sheet-table th:nth-child(2), .instruction-sheet-table td:nth-child(2) { width: 13%; }
      .instruction-sheet-table th:nth-child(3), .instruction-sheet-table td:nth-child(3) { width: 4%; }
      .instruction-sheet-table th:nth-child(4), .instruction-sheet-table td:nth-child(4) { width: 16%; }
      .instruction-sheet-table th:nth-child(5), .instruction-sheet-table td:nth-child(5) { width: 5%; }
      .instruction-sheet-table th:nth-child(6), .instruction-sheet-table td:nth-child(6) { width: 5%; }
      .instruction-sheet-table th:nth-child(7), .instruction-sheet-table td:nth-child(7) { width: 4%; }
      .instruction-sheet-table th:nth-child(8), .instruction-sheet-table td:nth-child(8) { width: 4%; }
      .instruction-sheet-table th:nth-child(9), .instruction-sheet-table td:nth-child(9) { width: 4%; }
      .instruction-sheet-table th:nth-child(10), .instruction-sheet-table td:nth-child(10) { width: 5%; }
      .instruction-sheet-table th:nth-child(11), .instruction-sheet-table td:nth-child(11) { width: 5%; }
      .instruction-sheet-table th:nth-child(12), .instruction-sheet-table td:nth-child(12) { width: 10%; }
      .instruction-sheet-table th, .instruction-sheet-table td { border: 1px solid #999; padding: 3px 7px; text-align: center; line-height: 1.8; }
      .instruction-sheet-table th { background: #fff; font-weight: bold; font-size: 10px; }
      .instruction-sheet-table td { font-size: 14px; }
      .instruction-sheet-table td:nth-child(1), .instruction-sheet-table td:nth-child(12) { font-size: 10px; }
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
function escapeHtml(s: string): string {
  const div = document.createElement('div')
  div.textContent = s
  return div.innerHTML
}

watch(selectedScheduleMonth, () => {
  loadCuttingManagement()
  loadChamferingManagement()
})

function onProductionDayEditorKeydown(e: KeyboardEvent) {
  if (editingProductionDayId.value != null && e.key === 'Escape') {
    cancelEditProductionDay()
  }
}

onMounted(() => {
  loadMachineOptions()
  loadCuttingMachineOptions()
  loadScheduleMonths()
  loadPlans()
  loadCuttingManagement()
  loadChamferingManagement()
  loadKanbanIssuance()
  window.addEventListener('keydown', onProductionDayEditorKeydown)
})
onUnmounted(() => {
  window.removeEventListener('keydown', onProductionDayEditorKeydown)
})
</script>
 
<style scoped>
.cutting-instruction-container {
  max-width: 100%;
  margin: 0 auto;
  padding: 16px 20px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.header-title h1 {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
  margin: 0;
  letter-spacing: -0.02em;
}

.header-title .header-desc {
  font-size: 12px;
  color: #64748b;
  margin: 2px 0 0 0;
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
}

/* 右侧与生産バッチ一覧同高：288px（与 .plan-batch-table-wrap max-height 一致） */
.right-panel {
  display: flex;
  flex-direction: row;
  gap: 10px;
  height: 288px;
  min-height: 288px;
  max-height: 288px;
  background: #fafbfc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
  overflow: hidden;
}

.right-panel-top,
.right-panel-bottom {
  flex: 1 1 0;
  min-width: 0;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.right-panel-top {
  min-height: 0;
}

.right-panel-bottom {
  min-height: 0;
}

.right-panel-title {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  padding-bottom: 4px;
  border-bottom: 1px solid #f1f5f9;
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

.detail-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 2px 0;
}

.detail-label {
  flex: 0 0 72px;
  color: #64748b;
}

.detail-value {
  flex: 1;
  min-width: 0;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
}

.equipment-efficiency-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

.equipment-efficiency-body :deep(.el-table) {
  font-size: 11px;
}


.plan-section .section-card {
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.plan-section .section-card :deep(.el-card__header) {
  padding: 10px 16px;
  font-size: 13px;
  border-bottom: 1px solid #f1f5f9;
}

.plan-section .section-card :deep(.el-card__body) {
  padding: 12px 16px;
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
  flex: 6.5;
  min-width: 0;
}
.instruction-row.instruction-cols-6-4 .instruction-col:nth-child(2) {
  flex: 4.1;
  min-width: 0;
}

.instruction-row .instruction-col {
  flex: 1;
  min-width: 0;
  min-height: 240px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chamfering-management-section,
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
  background: #ffffff;
}

.cutting-mgmt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
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

.cutting-mgmt-title {
  font-size: 13px;
  font-weight: 600;
  color: #334155;
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

/* 切断指示：表形式（ヘッダ固定・データ行）、高さ 40% 増（320→448px） */
.cutting-management-section .cutting-mgmt-table-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  max-height: 448px;
  position: relative;
}

.cutting-mgmt-table-inner {
  flex: 1;
  min-height: 0;
  min-width: 0;
  display: flex;
  flex-direction: column;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-gutter: stable;
  background: #fff;
}

.cutting-mgmt-thead {
  flex-shrink: 0;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 1;
}

/* バッチ→切断のドロップゾーン：12行分の高さで固定、超過時は縦スクロール */
.cutting-mgmt-tbody-drop-zone {
  flex: 0 0 auto;
  height: 376px;
  min-height: 376px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
  border-radius: 0 0 6px 6px;
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
  min-width: 810px;
  width: 100%;
}
.cutting-mgmt-tfoot-wrap--tomorrow {
  min-width: 460px;
}
.cutting-mgmt-tfoot {
  border-top: 1px solid #e2e8f0;
  background: #f8fafc;
}
.cutting-mgmt-tfoot .cutting-mgmt-tr {
  font-weight: 600;
  color: #334155;
}
.cutting-mgmt-tfoot .cutting-mgmt-td-total-label {
  color: #475569;
}
.cutting-mgmt-tfoot .cutting-mgmt-td-total-value {
  justify-content: flex-end;
  text-align: right;
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
  min-width: 810px;
  width: 100%;
  font-size: 11px;
}

.cutting-mgmt-thead .cutting-mgmt-tr {
  font-weight: 600;
  color: #475569;
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
}

.cutting-mgmt-th:last-child,
.cutting-mgmt-td:last-child {
  border-right: none;
}

/* 11列: CD, ライン, 生産日, 切断機, 製品名, 原材料, 生産数, 完了, 生産順, 生産時間, 備考 */
.cutting-mgmt-th:nth-child(1),
.cutting-mgmt-td:nth-child(1) { flex: 0 0 45px; }
.cutting-mgmt-th:nth-child(2),
.cutting-mgmt-td:nth-child(2) { flex: 0 0 50px; }
.cutting-mgmt-th:nth-child(3),
.cutting-mgmt-td:nth-child(3) { flex: 0 0 75px; }
.cutting-mgmt-th:nth-child(4),
.cutting-mgmt-td:nth-child(4) { flex: 0 0 55px; }
.cutting-mgmt-th:nth-child(5),
.cutting-mgmt-td:nth-child(5) { flex: 1 1 0; min-width: 100px; }
.cutting-mgmt-th:nth-child(6),
.cutting-mgmt-td:nth-child(6) { flex: 0 0 110px; }
.cutting-mgmt-th:nth-child(7),
.cutting-mgmt-td:nth-child(7) { flex: 0 0 55px; }
.cutting-mgmt-th:nth-child(8),
.cutting-mgmt-td:nth-child(8) { flex: 0 0 44px; }
.cutting-mgmt-th:nth-child(9),
.cutting-mgmt-td:nth-child(9) { flex: 0 0 45px; }
.cutting-mgmt-th:nth-child(10),
.cutting-mgmt-td:nth-child(10) { flex: 0 0 60px; }
.cutting-mgmt-th:nth-child(11),
.cutting-mgmt-td:nth-child(11) { flex: 0 0 100px; }
.cutting-mgmt-th:nth-child(12),
.cutting-mgmt-td:nth-child(12) { flex: 0 0 70px; }

/* 翌日テーブル：7列（CD, 生産日, 切断機, 製品名, 生産数, 生産順, 生産時間）※原材料なし */
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-tr {
  min-width: 460px;
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
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(5) { flex: 0 0 30px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(6) { flex: 0 0 52px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(7),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(7) { flex: 0 0 62px; }
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(5),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-th:nth-child(7),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(5),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(6),
.cutting-mgmt-table-inner--tomorrow .cutting-mgmt-td:nth-child(7) {
  justify-content: center;
  text-align: center;
}

.cutting-mgmt-th-actions,
.cutting-mgmt-td-actions {
  justify-content: center;
  gap: 0;
}
.cutting-mgmt-td-actions .el-button {
  padding: 2px 4px;
  min-width: auto;
}
.cutting-mgmt-td-actions .el-button + .el-button {
  margin-left: 0;
}

/* 生産数(7)、生産順(9)、生産時間(10)：表头与数据居中 */
.cutting-mgmt-th:nth-child(7),
.cutting-mgmt-th:nth-child(9),
.cutting-mgmt-th:nth-child(10),
.cutting-mgmt-td:nth-child(7),
.cutting-mgmt-td:nth-child(9),
.cutting-mgmt-td:nth-child(10) {
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
  min-width: 200px;
}
.production-day-editor {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;
}
.production-day-editor .el-button.is-circle { padding: 4px; width: 24px; height: 24px; }
.production-day-editor .production-day-picker-inline { width: 108px; }
.production-day-editor :deep(.el-date-editor) { width: 108px !important; }

.cutting-mgmt-table :deep(.el-table__header th),
.cutting-mgmt-table :deep(.el-table__body td) {
  font-size: 11px;
}

.cutting-mgmt-empty {
  padding: 24px;
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
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
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}
.section-title .title-right-btn {
  margin-left: 8px;
}

.search-section {
  margin-bottom: 10px;
}

/* ============================
   バッチ編集ダイアログ (ped-*)
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

/* 生産バッチ一覧：表头固定・数据行表格模式 */
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
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow-x: auto;
  overflow-y: auto;
  scrollbar-gutter: stable;
  background: #fff;
}

.plan-batch-thead {
  flex-shrink: 0;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 1;
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

/* 10列: 生産月, ライン, 順位, 製品名, 計画数, 原材料, ロット数, ロットNo, 生産数, 操作 */
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
.plan-batch-td:nth-child(10) { flex: 0 0 50px; }

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
  padding: 24px;
  text-align: center;
  color: #94a3b8;
  font-size: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-top: 0;
}

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
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  .section-title {
    font-size: 13px;
  }
}
</style>

<!-- 設備下拉選項字體縮小（popper 掛在 body，需單獨樣式） -->
<style>
.equipment-select-dropdown.el-select-dropdown .el-select-dropdown__item {
  font-size: 12px;
}

/* 切断指示の登録：生産日快捷・切断機按钮・紧凑UI（body 直下 teleport のため global） */
.move-to-cutting-dialog .el-dialog {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 40px rgba(30, 58, 95, 0.18), 0 4px 12px rgba(0, 0, 0, 0.06);
}
.move-to-cutting-dialog .el-dialog__header {
  padding: 0;
  margin: 0;
  border: none;
}
.move-to-cutting-dialog .el-dialog__headerbtn {
  top: 10px;
  right: 12px;
  width: 28px;
  height: 28px;
  color: rgba(255, 255, 255, 0.85);
}
.move-to-cutting-dialog .el-dialog__headerbtn:hover {
  color: #fff;
}
.move-to-cutting-dialog__header {
  padding: 10px 14px 10px 16px;
  background: linear-gradient(135deg, #334155 0%, #475569 50%, #64748b 100%);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.move-to-cutting-dialog__title { opacity: 0.98; }
.move-to-cutting-dialog .el-dialog__body {
  padding: 10px 14px 12px;
  background: #fafbfc;
}
.move-to-cutting-form .el-form-item.move-to-cutting-form-item {
  margin-bottom: 10px;
}
.move-to-cutting-form .el-form-item:last-child { margin-bottom: 0; }
.move-to-cutting-form .el-form-item__label {
  font-size: 12px;
  color: #64748b;
  padding-right: 10px;
}
.move-to-cutting-date-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}
.move-to-cutting-date-picker { width: 100% !important; max-width: 100%; }
.move-to-cutting-date-picker .el-input__wrapper { border-radius: 6px; }
.move-to-cutting-date-shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.move-to-cutting-date-shortcuts .el-button { margin-left: 0; }
.move-to-cutting-machine-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.move-to-cutting-machine-btns .el-button {
  margin-left: 0;
  min-height: 28px;
  padding: 4px 12px;
  font-size: 12px;
  border-radius: 6px;
}
.move-to-cutting-dialog__footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 14px 10px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
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
.cutting-edit-save-btn {
  --el-button-bg-color: #2563eb;
  --el-button-border-color: #2563eb;
  --el-button-hover-bg-color: #1d4ed8;
  --el-button-hover-border-color: #1d4ed8;
  border-radius: 6px;
}

/* ==================================================
   バッチ編集ダイアログ: el-dialog overrides (global)
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

/* 新規追加ダイアログ */
.nr-form {
  padding: 16px 20px 8px;
}
.nr-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px 20px;
}
.nr-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
  padding: 8px 20px 12px;
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
</style>
