<template>
  <transition name="fade-slide" mode="out-in">
    <div class="route-master-container rtm-modern" v-if="true">
      <!-- Compact Header -->
      <div class="page-header">
        <div class="page-header-fx" aria-hidden="true">
          <span class="fx-orb orb-a" />
          <span class="fx-orb orb-b" />
          <span class="fx-grid" />
          <span class="fx-sheen" />
        </div>
        <div class="header-content">
          <div class="title-section">
            <div class="title-row">
              <span class="title-icon">🛠️</span>
              <h1 class="main-title">{{ t('master.processRoute.title') }}</h1>
              <div class="stat-badge">
                <span class="stat-number">{{ routeList.length }}</span>
                <span class="stat-label">{{ t('master.common.items') }}</span>
              </div>
            </div>
            <p class="subtitle">{{ t('master.processRoute.subtitle') }}</p>
          </div>
          <div class="header-stats" @mousemove="handleStatTilt" @mouseleave="resetStatTilt">
            <div class="stat-card stat-card--active">
              <div class="stat-card-number">{{ activeRouteCount }}</div>
              <div class="stat-card-label">{{ t('master.common.active') }}</div>
            </div>
            <div class="stat-card stat-card--inactive">
              <div class="stat-card-number">{{ routeList.length - activeRouteCount }}</div>
              <div class="stat-card-label">{{ t('master.common.inactive') }}</div>
            </div>
            <div class="stat-card stat-card--default">
              <div class="stat-card-number">{{ defaultRouteCount }}</div>
              <div class="stat-card-label">{{ t('master.processRoute.default') }}</div>
            </div>
          </div>
          <el-button v-if="canCreate" type="primary" icon="Plus" @click="openAddDialog" class="add-btn">
            <span class="btn-icon">➕</span> {{ t('master.processRoute.addRoute') }}
          </el-button>
        </div>
      </div>

      <!-- Compact Search Section -->
      <div class="search-section">
        <div class="search-row">
          <div class="search-input-wrapper">
            <el-icon class="search-icon">🔍</el-icon>
            <el-input 
              v-model="filters.keyword" 
              :placeholder="t('master.processRoute.searchPlaceholder')" 
              clearable 
              @keyup.enter="fetchList"
              class="search-input"
            />
          </div>
          <el-button type="primary" @click="fetchList" class="search-btn">{{ t('master.common.search') }}</el-button>
        </div>
      </div>

      <!-- Data Table -->
      <div class="table-section">
        <el-table 
          :data="routeList" 
          border 
          stripe 
          highlight-current-row 
          v-loading="loading" 
          class="modern-table"
          :header-cell-style="{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff', fontWeight: '600', fontSize: '13px', padding: '8px 12px' }"
          :cell-style="{ padding: '6px 10px', fontSize: '13px' }"
        >
          <el-table-column :label="t('master.processRoute.routeCD')" prop="route_cd" width="110" align="center">
            <template #default="{ row }">
              <span class="code-cell">{{ row.route_cd }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('master.processRoute.routeName')" prop="route_name" min-width="120">
            <template #default="{ row }">
              <span class="name-cell">{{ row.route_name }}</span>
            </template>
          </el-table-column>
          <el-table-column :label="t('master.processRoute.description')" prop="description" min-width="180" show-overflow-tooltip />
          <el-table-column :label="t('master.processRoute.inUse')" prop="is_active" width="70" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active !== false ? 'success' : 'info'" size="small" effect="plain" class="status-tag">
                {{ row.is_active !== false ? t('master.common.active') : t('master.common.inactive') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="t('master.processRoute.default')" prop="is_default" width="85" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.is_default" class="default-icon">✅</el-icon>
              <span v-else class="empty-default">-</span>
            </template>
          </el-table-column>
          <el-table-column v-if="canEdit || canDelete" :label="t('master.common.actions')" width="240" align="center" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button v-if="canEdit" size="small" type="primary" plain @click="goToSteps(row)" class="action-btn">
                  📋 {{ t('master.processRoute.steps') }}
                </el-button>
                <el-button v-if="canEdit" size="small" type="warning" plain @click="openEditDialog(row)" class="action-btn">
                  ✏️ {{ t('master.common.edit') }}
                </el-button>
                <el-button v-if="canDelete" size="small" type="danger" plain @click="handleDelete(row)" class="action-btn">
                  🗑️
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- Footer Info -->
      <div class="footer-section">
        <div class="result-info">
          <el-icon>📊</el-icon>
          <span>{{ t('master.processRoute.displayCountShort', { n: routeList.length }) }}</span>
        </div>
        <el-pagination 
          v-if="pagination.total > pagination.pageSize"
          v-model:current-page="pagination.currentPage" 
          v-model:page-size="pagination.pageSize"
          :page-sizes="[20, 50, 100, 200]" 
          :total="pagination.total" 
          layout="sizes, prev, pager, next"
          @size-change="fetchList" 
          @current-change="fetchList"
          class="compact-pagination"
          size="small"
        />
      </div>

      <RouteEditDialog v-model:visible="showDialog" :mode="dialogMode" :initial-data="editData" @saved="fetchList" />
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox, ElMessage } from 'element-plus'
import { fetchRoutes, deleteRoute } from '@/api/master/processRouterMaster'
import type { RouteItem } from '@/types/master'
import RouteEditDialog from './ProcessRouteEditDialog.vue'
import { useMasterOperationPermission } from '@/composables/useMasterOperationPermission'
import { guardMasterOperation } from '@/utils/masterOperationGuard'

const { t } = useI18n()
const { canCreate, canEdit, canDelete } = useMasterOperationPermission()
const router = useRouter()

/** ステップ編集へ（直接 ProcessRouteStepEditor へ遷移。製品は遷移先で選択） */
const goToSteps = (row: RouteItem) => {
  router.push({
    name: 'RouteStepList',
    params: { route_cd: row.route_cd }
  })
}

const filters = ref({ keyword: '' })
const routeList = ref<RouteItem[]>([])
const loading = ref(false)
const pagination = ref({
  currentPage: 1,
  pageSize: 50,
  total: 0
})

const showDialog = ref(false)
const dialogMode = ref<'add' | 'edit'>('add')
const editData = ref<RouteItem | null>(null)

const activeRouteCount = computed(() => routeList.value.filter((r) => r.is_active !== false).length)
const defaultRouteCount = computed(() => routeList.value.filter((r) => r.is_default).length)

// ヘッダー統計カードの3Dチルト（マウス追従）
function handleStatTilt(e: MouseEvent) {
  const item = (e.target as HTMLElement | null)?.closest<HTMLElement>('.stat-card')
  const host = e.currentTarget as HTMLElement
  host.querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    if (el !== item) {
      el.style.removeProperty('--rx')
      el.style.removeProperty('--ry')
    }
  })
  if (!item) return
  const rect = item.getBoundingClientRect()
  const px = (e.clientX - rect.left) / rect.width
  const py = (e.clientY - rect.top) / rect.height
  item.style.setProperty('--rx', `${((0.5 - py) * 14).toFixed(2)}deg`)
  item.style.setProperty('--ry', `${((px - 0.5) * 14).toFixed(2)}deg`)
  item.style.setProperty('--mx', `${(px * 100).toFixed(1)}%`)
  item.style.setProperty('--my', `${(py * 100).toFixed(1)}%`)
}

function resetStatTilt(e: MouseEvent) {
  ;(e.currentTarget as HTMLElement).querySelectorAll<HTMLElement>('.stat-card').forEach((el) => {
    el.style.removeProperty('--rx')
    el.style.removeProperty('--ry')
  })
}

const fetchList = async () => {
  loading.value = true
  try {
    const result = await fetchRoutes(
      filters.value.keyword,
      pagination.value.currentPage,
      pagination.value.pageSize
    )
    routeList.value = result?.data?.list ?? result?.list ?? []
    pagination.value.total = result?.data?.total ?? result?.total ?? 0
  } catch {
    ElMessage.error(t('master.common.loadError'))
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  if (!guardMasterOperation(canCreate)) return
  dialogMode.value = 'add'
  editData.value = null
  showDialog.value = true
}

const openEditDialog = (row: RouteItem) => {
  if (!guardMasterOperation(canEdit)) return
  dialogMode.value = 'edit'
  editData.value = { ...row }
  showDialog.value = true
}

const handleDelete = async (row: RouteItem) => {
  if (!guardMasterOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(t('master.processRoute.confirmDelete'), t('common.confirm'), { type: 'warning' })
    if (row.id == null) return
    await deleteRoute(row.id)
    ElMessage.success(t('master.common.deleteSuccess'))
    fetchList()
  } catch {
    // cancelled
  }
}

onMounted(fetchList)
</script>

<style scoped>
.route-master-container {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
  min-height: 100vh;
}

/* Header */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 14px 20px;
  margin-bottom: 12px;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 1.5rem;
}

.main-title {
  font-size: 1.4rem;
  font-weight: 700;
  margin: 0;
  color: #fff;
  letter-spacing: 0.5px;
}

.stat-badge {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 4px 12px;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
}

.stat-number {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.9);
}

.subtitle {
  color: rgba(255, 255, 255, 0.85);
  margin: 4px 0 0;
  font-size: 0.85rem;
}

.add-btn {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  padding: 8px 16px;
  font-weight: 600;
  color: #fff;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.add-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-icon {
  font-size: 0.9rem;
}

/* Search Section */
.search-section {
  background: #fff;
  border-radius: 10px;
  padding: 10px 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.search-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8fafc;
  border-radius: 8px;
  padding: 0 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s;
}

.search-input-wrapper:focus-within {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  color: #94a3b8;
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  background: transparent;
}

.search-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  font-weight: 600;
}

/* Table Section */
.table-section {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  margin-bottom: 12px;
}

.modern-table {
  width: 100%;
}

.code-cell {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 600;
  color: #667eea;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.name-cell {
  font-weight: 500;
  color: #1e293b;
}

.status-tag {
  border-radius: 12px;
  font-size: 11px;
  padding: 2px 8px;
}

.default-icon {
  color: #10b981;
  font-size: 1rem;
}

.empty-default {
  color: #cbd5e1;
}

.action-buttons {
  display: flex;
  gap: 4px;
  justify-content: center;
  flex-wrap: nowrap;
}

.action-btn {
  padding: 4px 8px;
  font-size: 11px;
  border-radius: 6px;
}

/* Footer */
.footer-section {
  background: #fff;
  border-radius: 10px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.result-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #64748b;
  font-size: 0.85rem;
}

.result-info strong {
  color: #667eea;
  font-weight: 700;
}

.compact-pagination {
  --el-pagination-button-height: 28px;
}

/* Responsive */
@media (max-width: 1024px) {
  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .add-btn {
    width: 100%;
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .route-master-container {
    padding: 8px;
  }
  .page-header {
    padding: 12px;
  }
  .main-title {
    font-size: 1.2rem;
  }
  .title-row {
    flex-wrap: wrap;
  }
  .search-section {
    padding: 8px 12px;
  }
  .search-row {
    flex-direction: column;
  }
  .search-input-wrapper {
    width: 100%;
  }
  .search-btn {
    width: 100%;
  }
  .footer-section {
    flex-direction: column;
    gap: 8px;
  }
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
  .action-btn {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .stat-badge {
    display: none;
  }
  .main-title {
    font-size: 1.1rem;
  }
}

/* Table Styles Override */
:deep(.el-table) {
  --el-table-border-color: #e2e8f0;
  --el-table-row-hover-bg-color: #f0f4ff;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #fafbfc;
}

:deep(.el-tag) {
  border-radius: 10px;
  font-weight: 500;
}

/* Transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* ============================================================
 * 页面美化：現代UI・3D動効・色分け（工程ルートマスタ / purple→fuchsia）
 * ============================================================ */
.route-master-container.rtm-modern {
  --hx-1: #2e1065;
  --hx-2: #6b21a8;
  --hx-3: #9333ea;
  --hx-4: #c026d3;
  --hx-deep: #581c87;
  --hx-accent: #9333ea;
  --hx-soft: #faf5ff;
  --hx-soft2: #f3e8ff;
  --hx-line: #e9d5ff;
  background:
    radial-gradient(1000px 360px at 0% 0%, rgba(147, 51, 234, 0.08), transparent 60%),
    radial-gradient(900px 360px at 100% 0%, rgba(192, 38, 211, 0.07), transparent 60%),
    #f8fafc;
}

/* ---------- ヒーローヘッダー ---------- */
.rtm-modern .page-header {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  background: linear-gradient(125deg, var(--hx-1) 0%, var(--hx-2) 34%, var(--hx-3) 70%, var(--hx-4) 100%);
  box-shadow:
    0 18px 36px -18px rgba(107, 33, 168, 0.7),
    0 4px 12px -6px rgba(192, 38, 211, 0.4),
    inset 0 0 0 1px rgba(255, 255, 255, 0.16);
}

.rtm-modern .page-header-fx {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}

.rtm-modern .header-content {
  position: relative;
  z-index: 1;
}

.rtm-modern .title-section {
  flex: 1;
  min-width: 0;
}

.rtm-modern .page-header-fx .fx-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(22px);
  opacity: 0.6;
  animation: rtmOrbFloat 11s ease-in-out infinite;
}

.rtm-modern .page-header-fx .orb-a {
  width: 240px;
  height: 240px;
  top: -140px;
  right: 30%;
  background: radial-gradient(circle, #f0abfc 0%, transparent 70%);
}

.rtm-modern .page-header-fx .orb-b {
  width: 190px;
  height: 190px;
  bottom: -120px;
  left: 22%;
  background: radial-gradient(circle, #c4b5fd 0%, transparent 70%);
  animation-delay: -5s;
}

.rtm-modern .page-header-fx .fx-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.08) 1px, transparent 1px);
  background-size: 22px 22px;
  mask-image: radial-gradient(ellipse at 14% 50%, #000 0%, transparent 70%);
}

.rtm-modern .page-header-fx .fx-sheen {
  position: absolute;
  top: 0;
  bottom: 0;
  left: -40%;
  width: 35%;
  background: linear-gradient(100deg, transparent 0%, rgba(255, 255, 255, 0.16) 50%, transparent 100%);
  animation: rtmSheen 7s ease-in-out infinite;
}

.rtm-modern .title-row {
  gap: 12px;
}

.rtm-modern .title-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  font-size: 20px;
  border-radius: 12px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.3) 0%, rgba(255, 255, 255, 0.08) 100%);
  border: 1px solid rgba(255, 255, 255, 0.34);
  box-shadow:
    0 4px 0 rgba(46, 16, 101, 0.6),
    0 10px 20px -8px rgba(2, 6, 23, 0.55),
    inset 0 1px 0 rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(6px);
  animation: rtmIconFloat 5s ease-in-out infinite;
}

.rtm-modern .main-title {
  font-size: 20px;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(2, 6, 23, 0.4);
}

.rtm-modern .stat-badge {
  border: 1px solid rgba(255, 255, 255, 0.26);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.3);
}

.rtm-modern .subtitle {
  color: rgba(250, 245, 255, 0.88);
}

/* 統計カード：3Dチルト＋グレア＋上端アクセント */
.rtm-modern .header-stats {
  display: flex;
  gap: 8px;
  perspective: 700px;
}

.rtm-modern .stat-card {
  --sc: #86efac;
  position: relative;
  overflow: hidden;
  min-width: 78px;
  padding: 6px 14px;
  color: #fff;
  text-align: center;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.26);
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(10px);
  box-shadow:
    0 10px 22px -12px rgba(2, 6, 23, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.32);
  transform: rotateX(var(--rx, 0deg)) rotateY(var(--ry, 0deg));
  transform-style: preserve-3d;
  transition:
    transform 0.18s ease-out,
    box-shadow 0.25s ease;
}

.rtm-modern .stat-card--inactive {
  --sc: #cbd5e1;
  background: rgba(46, 16, 101, 0.26);
}

.rtm-modern .stat-card--default {
  --sc: #fde68a;
}

.rtm-modern .stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--sc);
}

.rtm-modern .stat-card::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.25s ease;
  background: radial-gradient(
    circle at var(--mx, 50%) var(--my, 50%),
    rgba(255, 255, 255, 0.3) 0%,
    transparent 60%
  );
}

.rtm-modern .stat-card:hover {
  box-shadow:
    0 16px 28px -12px rgba(2, 6, 23, 0.7),
    inset 0 1px 0 rgba(255, 255, 255, 0.42);
}

.rtm-modern .stat-card:hover::after {
  opacity: 1;
}

.rtm-modern .stat-card-number {
  font-size: 1.3rem;
  font-weight: 800;
  line-height: 1.1;
  text-shadow: 0 1px 6px rgba(2, 6, 23, 0.3);
  transform: translateZ(14px);
}

.rtm-modern .stat-card-label {
  margin-top: 2px;
  font-size: 0.7rem;
  font-weight: 600;
  opacity: 0.92;
  white-space: nowrap;
}

/* 追加ボタン：3Dキーキャップ */
.rtm-modern .add-btn,
.rtm-modern .add-btn:hover {
  --k-edge: #701a75;
  --k-glow: rgba(192, 38, 211, 0.55);
  color: #fff;
  font-weight: 700;
  border: 1px solid rgba(255, 255, 255, 0.34);
  background: linear-gradient(135deg, #f0abfc 0%, #d946ef 45%, #a21caf 100%);
}

.rtm-modern .add-btn {
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.34);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.18s ease;
}

.rtm-modern .add-btn:hover {
  filter: brightness(1.06);
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.4);
}

.rtm-modern .add-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -4px var(--k-glow);
}

/* ---------- 検索バー ---------- */
.rtm-modern .search-section,
.rtm-modern .table-section,
.rtm-modern .footer-section {
  position: relative;
  overflow: hidden;
  border-radius: 14px;
  border: 1px solid var(--hx-line);
  box-shadow:
    0 14px 28px -22px rgba(107, 33, 168, 0.5),
    0 1px 3px rgba(15, 23, 42, 0.05);
}

.rtm-modern .search-section::before,
.rtm-modern .table-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  z-index: 5;
  pointer-events: none;
  background: linear-gradient(90deg, var(--hx-2) 0%, var(--hx-3) 55%, var(--hx-4) 100%);
}

.rtm-modern .search-section {
  padding-top: 12px;
  background: linear-gradient(110deg, var(--hx-soft) 0%, #ffffff 60%);
}

.rtm-modern .search-input-wrapper {
  border-radius: 10px;
  background: #fff;
  border-color: var(--hx-line);
}

.rtm-modern .search-input-wrapper:focus-within {
  border-color: var(--hx-accent);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--hx-accent) 16%, transparent);
}

.rtm-modern .search-btn,
.rtm-modern .search-btn:hover {
  --k-edge: #3b0764;
  --k-glow: rgba(147, 51, 234, 0.5);
  background: linear-gradient(135deg, #c084fc 0%, #9333ea 55%, #7e22ce 100%);
}

.rtm-modern .search-btn {
  box-shadow:
    0 3px 0 var(--k-edge),
    0 10px 18px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.18s ease;
}

.rtm-modern .search-btn:hover {
  filter: brightness(1.06);
  transform: translateY(-2px);
  box-shadow:
    0 5px 0 var(--k-edge),
    0 14px 22px -8px var(--k-glow),
    inset 0 1px 0 rgba(255, 255, 255, 0.36);
}

.rtm-modern .search-btn:active {
  transform: translateY(2px);
  box-shadow:
    0 1px 0 var(--k-edge),
    0 4px 8px -4px var(--k-glow);
}

/* ---------- テーブル ---------- */
.rtm-modern .modern-table :deep(.el-table__header-wrapper th.el-table__cell) {
  color: var(--hx-deep) !important;
  font-weight: 700 !important;
  background: linear-gradient(180deg, var(--hx-soft) 0%, var(--hx-soft2) 100%) !important;
  border-bottom: 2px solid #d8b4fe !important;
}

.rtm-modern .modern-table :deep(.el-table__body tr:hover > td.el-table__cell:first-child),
.rtm-modern .modern-table :deep(.el-table__body tr.current-row > td.el-table__cell:first-child) {
  box-shadow: inset 3px 0 0 var(--hx-accent);
}

.rtm-modern .code-cell {
  display: inline-block;
  color: var(--hx-deep);
  font-weight: 700;
  background: linear-gradient(180deg, #ffffff 0%, var(--hx-soft2) 100%);
  border-radius: 6px;
  box-shadow:
    inset 0 0 0 1px var(--hx-line),
    0 2px 0 var(--hx-line);
  transition: transform 0.15s ease;
}

.rtm-modern .modern-table :deep(.el-table__body tr:hover) .code-cell {
  transform: translateY(-1px);
}

.rtm-modern .default-icon {
  display: inline-flex;
  width: 24px;
  height: 24px;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  background: #fefce8;
  box-shadow:
    inset 0 0 0 1px #fde68a,
    0 2px 0 #fde68a;
}

.rtm-modern .action-btn {
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease;
}

.rtm-modern .action-btn.el-button--primary {
  box-shadow: 0 2px 0 #bfdbfe;
}

.rtm-modern .action-btn.el-button--warning {
  box-shadow: 0 2px 0 #fde68a;
}

.rtm-modern .action-btn.el-button--danger {
  box-shadow: 0 2px 0 #fecaca;
}

.rtm-modern .action-btn:hover {
  transform: translateY(-1px);
}

.rtm-modern .action-btn.el-button--primary:hover {
  box-shadow:
    0 3px 0 #1e40af,
    0 8px 14px -8px rgba(37, 99, 235, 0.6);
}

.rtm-modern .action-btn.el-button--warning:hover {
  box-shadow:
    0 3px 0 #92400e,
    0 8px 14px -8px rgba(217, 119, 6, 0.6);
}

.rtm-modern .action-btn.el-button--danger:hover {
  box-shadow:
    0 3px 0 #991b1b,
    0 8px 14px -8px rgba(220, 38, 38, 0.6);
}

.rtm-modern .action-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}

/* ---------- フッター ---------- */
.rtm-modern .footer-section {
  background: linear-gradient(180deg, #ffffff 0%, var(--hx-soft) 100%);
}

.rtm-modern .result-info {
  padding: 2px 10px;
  color: var(--hx-deep);
  font-weight: 700;
  border-radius: 999px;
  background: var(--hx-soft2);
  box-shadow: inset 0 0 0 1px var(--hx-line);
}

.rtm-modern .compact-pagination :deep(.el-pager li.is-active) {
  color: #fff;
  border-radius: 7px;
  background: linear-gradient(135deg, #c084fc 0%, #9333ea 55%, #7e22ce 100%);
  box-shadow:
    0 2px 0 #3b0764,
    0 6px 12px -6px rgba(147, 51, 234, 0.7);
}

/* ---------- キーフレーム ---------- */
@keyframes rtmOrbFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(-18px, 10px, 0) scale(1.08);
  }
}

@keyframes rtmSheen {
  0%,
  60% {
    left: -40%;
  }
  100% {
    left: 130%;
  }
}

@keyframes rtmIconFloat {
  0%,
  100% {
    transform: perspective(300px) rotateX(0deg) rotateY(0deg) translateY(0);
  }
  50% {
    transform: perspective(300px) rotateX(10deg) rotateY(-14deg) translateY(-2px);
  }
}

@media (max-width: 1024px) {
  .rtm-modern .header-stats {
    justify-content: flex-start;
    flex-wrap: wrap;
  }
}

@media (prefers-reduced-motion: reduce) {
  .rtm-modern .page-header-fx .fx-orb,
  .rtm-modern .page-header-fx .fx-sheen,
  .rtm-modern .title-icon {
    animation: none;
  }

  .rtm-modern .stat-card {
    transform: none;
    transition: none;
  }
}
</style>
