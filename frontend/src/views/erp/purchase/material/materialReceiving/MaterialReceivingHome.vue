<template>
  <div class="receiving-home">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="main-title">
          <el-icon class="title-icon">
            <Download />
          </el-icon>
          材料受入管理
        </h1>
        <p class="subtitle">材料の受け入れ履歴・検品管理システム</p>
      </div>
      <div class="header-decoration">
        <div class="decoration-circle circle-1"></div>
        <div class="decoration-circle circle-2"></div>
        <div class="decoration-circle circle-3"></div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="content-container">
      <div class="feature-grid">
        <!-- 受け入れ履歴 -->
        <div class="feature-card history-card" @click="goToHistory">
          <div class="card-icon">
            <el-icon class="animated-icon">
              <Document />
            </el-icon>
          </div>
          <div class="card-content">
            <h3 class="card-title">材料受入更新</h3>
            <p class="card-description">材料更新・受入履歴を確認・管理します</p>
            <ul class="feature-list">
              <li>受入記録の一覧表示</li>
              <li>受入データの更新</li>
              <li>受入状況の統計</li>
            </ul>
          </div>
          <div class="card-arrow">
            <el-icon>
              <ArrowRight />
            </el-icon>
          </div>
        </div>

        <!-- 受け入れ検品 -->
        <div class="feature-card inspection-card" @click="goToInspection">
          <div class="card-icon">
            <el-icon class="animated-icon">
              <View />
            </el-icon>
          </div>
          <div class="card-content">
            <h3 class="card-title">受入検品管理</h3>
            <p class="card-description">受入材料の品質設定・検品を行います</p>
            <ul class="feature-list">
              <li>検品項目の登録・管理</li>
              <li>品質基準の設定</li>
              <li>検品結果の記録</li>
            </ul>
          </div>
          <div class="card-arrow">
            <el-icon>
              <ArrowRight />
            </el-icon>
          </div>
        </div>
      </div>
    </div>

    <router-view />
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Download, Document, View, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

const goToHistory = (): void => {
  router.push({ name: 'MaterialReceivingHistory' })
}

const goToInspection = (): void => {
  router.push({ name: 'MaterialReceivingInspection' })
}
</script>

<style scoped>
.receiving-home {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  position: relative;
  overflow-x: hidden;
}

.page-header {
  position: relative;
  padding: 40px 20px 60px;
  text-align: center;
  color: white;
  overflow: hidden;
}

.header-content {
  position: relative;
  z-index: 2;
  max-width: 800px;
  margin: 0 auto;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.title-icon {
  font-size: 2.2rem;
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

.subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
  font-weight: 300;
}

.header-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.decoration-circle {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  animation: float 6s ease-in-out infinite;
}

.circle-1 {
  width: 100px;
  height: 100px;
  top: 20%;
  left: 10%;
  animation-delay: 0s;
}

.circle-2 {
  width: 150px;
  height: 150px;
  top: 60%;
  right: 15%;
  animation-delay: 2s;
}

.circle-3 {
  width: 80px;
  height: 80px;
  top: 40%;
  left: 80%;
  animation-delay: 4s;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0px) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(180deg);
  }
}

.content-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px 40px;
  position: relative;
  z-index: 1;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
  gap: 32px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 32px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: flex-start;
  gap: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  border-radius: 20px 20px 0 0;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 1.8rem;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

.feature-card:hover .card-icon {
  transform: scale(1.1) rotate(5deg);
}

.animated-icon {
  transition: transform 0.3s ease;
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 8px;
  color: #2c3e50;
}

.card-description {
  font-size: 1rem;
  color: #7f8c8d;
  margin: 0 0 16px;
  line-height: 1.5;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  font-size: 0.9rem;
  color: #95a5a6;
  margin: 4px 0;
  padding-left: 16px;
  position: relative;
}

.feature-list li::before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #27ae60;
  font-weight: bold;
}

.card-arrow {
  color: #bdc3c7;
  font-size: 1.5rem;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.feature-card:hover .card-arrow {
  color: #667eea;
  transform: translateX(8px);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    padding: 30px 15px 40px;
  }

  .main-title {
    font-size: 2rem;
    flex-direction: column;
    gap: 8px;
  }

  .subtitle {
    font-size: 1rem;
  }

  .content-container {
    padding: 0 15px 30px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .feature-card {
    padding: 24px 20px;
    flex-direction: column;
    text-align: center;
  }

  .card-content {
    text-align: left;
  }
}

@media (max-width: 480px) {
  .main-title {
    font-size: 1.8rem;
  }
}

/* 深色模式支持 */
@media (prefers-color-scheme: dark) {
  .receiving-home {
    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  }

  .feature-card {
    background: rgba(45, 55, 72, 0.95);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .card-title {
    color: #e2e8f0;
  }

  .card-description {
    color: #a0aec0;
  }
}

/* 动画效果 */
.feature-card {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.feature-card:nth-child(1) {
  animation-delay: 0.1s;
}
.feature-card:nth-child(2) {
  animation-delay: 0.2s;
}
</style>
