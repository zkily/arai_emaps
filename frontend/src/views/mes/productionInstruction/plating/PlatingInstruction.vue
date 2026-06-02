<template>
  <div class="plating-instruction">
    <header class="page-header">
      <div class="header-content">
        <div class="header-info">
          <div class="title-wrapper">
            <span class="title-icon-wrap" aria-hidden="true">
              <el-icon class="title-icon"><Grid /></el-icon>
            </span>
            <div>
              <h1 class="page-title">メッキ指示</h1>
              <!-- <p class="page-subtitle">メッキ投入ボードの参照・印刷（APS メッキ計画と同一データ）</p> -->
            </div>
          </div>
        </div>
        <div class="header-badge">
          <span class="header-badge__dot" />
          <span>MES 生産指示</span>
        </div>
      </div>
    </header>

    <section class="content-shell">
      <PlatingInputBoardPanel mode="instruction" class="board-panel" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { Grid } from '@element-plus/icons-vue'
import PlatingInputBoardPanel from '@/views/aps/productionPlanCreation/plating/PlatingInputBoardPanel.vue'

defineOptions({ name: 'PlatingInstruction' })
</script>

<style scoped>
.plating-instruction {
  --pi-accent: #0d9488;
  --pi-accent-deep: #0f766e;
  --pi-accent-soft: #ccfbf1;
  --pi-surface: rgba(255, 255, 255, 0.96);
  --pi-shadow-sm: 0 2px 6px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04);
  --pi-shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08), 0 2px 8px rgba(15, 23, 42, 0.05);
  --pi-shadow-lg: 0 16px 40px rgba(13, 148, 136, 0.12), 0 6px 16px rgba(15, 23, 42, 0.08);

  position: relative;
  min-height: calc(100vh - 8px);
  padding: 12px 14px 20px;
  max-width: 1680px;
  margin: 0 auto;
  background: linear-gradient(145deg, #f0fdfa 0%, #f8fafc 42%, #f1f5f9 100%);
  animation: pi-fade-in 0.5s ease-out;
}

.plating-instruction::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 12% 18%, rgba(13, 148, 136, 0.08) 0%, transparent 42%),
    radial-gradient(circle at 88% 72%, rgba(56, 189, 248, 0.06) 0%, transparent 45%);
}

@keyframes pi-fade-in {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header {
  position: relative;
  z-index: 1;
  margin-bottom: 12px;
  padding: 14px 18px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.85);
  background: var(--pi-surface);
  backdrop-filter: blur(12px);
  box-shadow: var(--pi-shadow-md);
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--pi-accent-deep) 0%, var(--pi-accent) 45%, #38bdf8 100%);
  background-size: 200% 100%;
  animation: pi-accent-flow 4s ease infinite;
}

@keyframes pi-accent-flow {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(145deg, #14b8a6 0%, #0d9488 55%, #0f766e 100%);
  box-shadow:
    0 6px 14px rgba(13, 148, 136, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.title-icon {
  font-size: 22px;
  color: #fff;
}

.page-title {
  margin: 0 0 4px;
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.25;
  background: linear-gradient(135deg, #134e4a 0%, #0d9488 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  margin: 0;
  font-size: 12px;
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.02em;
}

.header-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  color: var(--pi-accent-deep);
  background: linear-gradient(180deg, #fff 0%, var(--pi-accent-soft) 100%);
  border: 1px solid rgba(13, 148, 136, 0.22);
  box-shadow: var(--pi-shadow-sm);
  white-space: nowrap;
}

.header-badge__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--pi-accent);
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.2);
}

.content-shell {
  position: relative;
  z-index: 1;
  border-radius: 16px;
  padding: 2px;
  background: linear-gradient(160deg, rgba(13, 148, 136, 0.18) 0%, rgba(148, 163, 184, 0.12) 50%, rgba(255, 255, 255, 0.4) 100%);
  box-shadow: var(--pi-shadow-lg);
}

.board-panel {
  display: block;
}

/* ── ボードカード立体感 ── */
.board-panel:deep(.pp-card--board) {
  border-radius: 14px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.95),
    0 4px 14px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.board-panel:deep(.pp-card--board .el-card__header) {
  padding: 10px 14px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid rgba(226, 232, 240, 0.85);
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.8);
}

.board-panel:deep(.pp-card-title) {
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
}

.board-panel:deep(.kpi-chip) {
  border-radius: 10px;
  padding: 5px 12px;
  background: linear-gradient(180deg, #fff 0%, #f1f5f9 100%);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow:
    0 2px 4px rgba(15, 23, 42, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.board-panel:deep(.kpi-chip:hover) {
  transform: translateY(-1px);
  box-shadow:
    0 4px 10px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 1);
}

.board-panel:deep(.lap-board-outer) {
  box-shadow:
    inset 0 2px 6px rgba(15, 23, 42, 0.04),
    0 1px 0 rgba(255, 255, 255, 0.8);
}

.board-panel:deep(.print-range-dialog .el-dialog) {
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 20px 48px rgba(15, 23, 42, 0.18);
}

.board-panel:deep(.print-range-dialog .el-dialog__footer .el-button--primary) {
  font-weight: 700;
  border-radius: 8px;
  background: linear-gradient(145deg, #2dd4bf 0%, #0d9488 100%) !important;
  border-color: rgba(13, 148, 136, 0.4) !important;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);
}
</style>
