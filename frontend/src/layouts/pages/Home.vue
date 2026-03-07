<template>
  <div class="home-container">
    <!-- Header -->
    <header class="header">
      <div class="header-content">
        <div class="logo">
          <div class="logo-icon">
            <el-icon :size="24"><DataBoard /></el-icon>
          </div>
          <div class="logo-text">
            <span class="logo-title">Smart-EMAP</span>
            <span class="logo-sub">統合管理システム</span>
          </div>
        </div>
        <el-button type="primary" @click="goToLogin" class="login-btn">
          <el-icon><User /></el-icon>
          ログイン
        </el-button>
      </div>
    </header>

    <!-- Hero Section -->
    <main class="main">
      <div class="hero">
        <div class="hero-content">
          <h1 class="hero-title">
            製造業の<br />
            <span class="gradient-text">デジタルトランスフォーメーション</span>
          </h1>
          <p class="hero-subtitle">ERP・APS・MESを統合した次世代管理システム</p>
          <el-button type="primary" size="large" @click="goToLogin" class="cta-btn">
            今すぐ始める
            <el-icon class="btn-arrow"><ArrowRight /></el-icon>
          </el-button>
        </div>

        <!-- Feature Cards -->
        <div class="features-grid">
          <div class="feature-card" v-for="feature in features" :key="feature.title">
            <div class="feature-icon" :style="{ background: feature.gradient }">
              <el-icon :size="28"><component :is="feature.icon" /></el-icon>
            </div>
            <div class="feature-content">
              <h3>{{ feature.title }}</h3>
              <p class="feature-name">{{ feature.name }}</p>
              <p class="feature-desc">{{ feature.description }}</p>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="footer">
      <p>&copy; 2026 Smart-EMAP. All rights reserved.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { Management, DataAnalysis, Monitor, DataBoard, User, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

const goToLogin = () => {
  router.push('/login')
}

const features = [
  {
    title: 'ERP',
    name: '企業資源計画',
    description: '経営判断に必要な情報を一元管理',
    icon: markRaw(Management),
    gradient: 'linear-gradient(135deg, #667eea, #764ba2)'
  },
  {
    title: 'APS',
    name: '先進的計画・スケジューリング',
    description: '最適化された生産計画を立案',
    icon: markRaw(DataAnalysis),
    gradient: 'linear-gradient(135deg, #f43f5e, #e11d48)'
  },
  {
    title: 'MES',
    name: '製造実行システム',
    description: '現場のリアルタイム情報収集',
    icon: markRaw(Monitor),
    gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)'
  }
]
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
}

/* Header */
.header {
  padding: 16px 24px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.logo-text {
  display: flex;
  flex-direction: column;
}

.logo-title {
  font-size: 20px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.5px;
}

.logo-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.8);
}

.login-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(10px);
}

.login-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Main */
.main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
}

.hero {
  max-width: 1200px;
  text-align: center;
}

.hero-content {
  margin-bottom: 48px;
}

.hero-title {
  font-size: 48px;
  font-weight: 700;
  color: white;
  line-height: 1.2;
  margin: 0 0 16px;
  text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.gradient-text {
  background: linear-gradient(90deg, #a5f3fc, #f9a8d4);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 32px;
}

.cta-btn {
  background: white;
  color: #667eea;
  border: none;
  font-weight: 600;
  padding: 14px 32px;
  font-size: 16px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.cta-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  background: white;
  color: #764ba2;
}

.btn-arrow {
  margin-left: 8px;
  transition: transform 0.3s ease;
}

.cta-btn:hover .btn-arrow {
  transform: translateX(4px);
}

/* Features Grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 28px 24px;
  text-align: center;
  transition: all 0.3s ease;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 50px rgba(0, 0, 0, 0.25);
}

.feature-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 16px;
}

.feature-content h3 {
  font-size: 28px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 4px;
}

.feature-name {
  font-size: 14px;
  font-weight: 600;
  color: #667eea;
  margin: 0 0 8px;
}

.feature-desc {
  font-size: 13px;
  color: #64748b;
  margin: 0;
  line-height: 1.5;
}

/* Footer */
.footer {
  padding: 16px 24px;
  text-align: center;
}

.footer p {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

/* Responsive */
@media (max-width: 768px) {
  .hero-title {
    font-size: 32px;
  }
  
  .hero-subtitle {
    font-size: 16px;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .feature-card {
    padding: 24px 20px;
  }
}
</style>
