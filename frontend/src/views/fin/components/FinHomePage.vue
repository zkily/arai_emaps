<!--
  FIN 汎用ホーム（ダッシュボード）。
  タイトル + 機能カードグリッド。カードは子メニューへのナビゲーション。
  原価・会計ホーム（CostingHome.vue）と視覚言語を揃えている。
-->
<template>
  <div class="fin-home">
    <div class="fin-home-header">
      <div class="fin-home-icon"><el-icon :size="30"><Money /></el-icon></div>
      <div>
        <h1 class="fin-home-title">{{ title }}</h1>
        <div class="fin-home-subtitle">{{ subtitle }}</div>
      </div>
    </div>

    <div class="fin-module-grid">
      <router-link
        v-for="card in cards"
        :key="card.path"
        :to="card.path"
        class="fin-module-card"
      >
        <div class="fin-module-icon">
          <el-icon :size="26"><component :is="card.icon || 'Menu'" /></el-icon>
        </div>
        <div class="fin-module-info">
          <h3 class="fin-module-name">{{ card.title }}</h3>
          <p class="fin-module-desc">{{ card.desc }}</p>
        </div>
        <el-icon class="fin-module-arrow"><ArrowRight /></el-icon>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Money, ArrowRight } from '@element-plus/icons-vue'
import type { FinHomeCard } from './types'

defineProps<{ title: string; subtitle?: string; cards: FinHomeCard[] }>()
</script>

<style scoped>
.fin-home {
  min-height: 100%;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.fin-home-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
  color: #fff;
}
.fin-home-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.18);
}
.fin-home-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
}
.fin-home-subtitle {
  font-size: 13px;
  opacity: 0.85;
}
.fin-module-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}
.fin-module-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  text-decoration: none;
  color: inherit;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.fin-module-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
}
.fin-module-icon {
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  flex-shrink: 0;
}
.fin-module-info {
  flex: 1;
  min-width: 0;
}
.fin-module-name {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
.fin-module-desc {
  margin: 2px 0 0;
  font-size: 12px;
  color: #888;
}
.fin-module-arrow {
  color: #bbb;
}
</style>
