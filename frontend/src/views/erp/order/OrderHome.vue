<template>
  <div class="order-home">
    <div class="dynamic-background">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>

    <div class="modern-header">
      <div class="header-content">
        <div class="header-left">
          <div class="header-icon">
            <el-icon size="32"><Document /></el-icon>
          </div>
          <div class="header-text">
            <h1 class="header-title">受注管理</h1>
            <div class="header-subtitle">Order Management</div>
          </div>
        </div>
      </div>
    </div>

    <div class="module-grid">
      <router-link to="/erp/order/monthly" class="module-card modern-card">
        <div class="module-icon" style="background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);">
          <el-icon :size="32"><Calendar /></el-icon>
        </div>
        <div class="module-info">
          <h3 class="module-title">月受注管理</h3>
          <p class="module-desc">月別受注の登録・照会・内示管理</p>
        </div>
        <el-icon class="module-arrow"><ArrowRight /></el-icon>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Document, Calendar, ArrowRight } from '@element-plus/icons-vue'
</script>

<style scoped>
.order-home {
  position: relative;
  min-height: 100%;
  padding: 24px;
  overflow: hidden;
}
.dynamic-background {
  position: fixed;
  inset: 0;
  z-index: 0;
  overflow: hidden;
  pointer-events: none;
}
.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.2;
}
.orb-1 { width: 400px; height: 400px; background: linear-gradient(135deg, #8b5cf6, #a78bfa); top: -100px; right: -100px; }
.orb-2 { width: 300px; height: 300px; background: linear-gradient(135deg, #06b6d4, #22d3ee); bottom: 20%; left: -80px; }
.orb-3 { width: 250px; height: 250px; background: linear-gradient(135deg, #f59e0b, #fbbf24); bottom: -50px; right: 20%; }
.modern-header {
  position: relative;
  z-index: 1;
  margin-bottom: 24px;
}
.header-content { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.header-icon {
  width: 56px; height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.header-title { font-size: 24px; font-weight: 700; margin: 0 0 4px 0; color: #1e293b; }
.header-subtitle { font-size: 13px; color: #64748b; margin: 0; }
.module-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}
.module-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  border: 1px solid #e2e8f0;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s;
}
.module-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
  transform: translateY(-2px);
}
.module-icon {
  width: 64px; height: 64px;
  border-radius: 14px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.module-info { flex: 1; min-width: 0; }
.module-title { font-size: 16px; font-weight: 600; margin: 0 0 4px 0; color: #1e293b; }
.module-desc { font-size: 13px; color: #64748b; margin: 0; }
.module-arrow { color: #94a3b8; font-size: 20px; }
</style>
