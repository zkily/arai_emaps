<template>
  <div class="home-container">
    <!-- 背景层：网格 + 光晕（营造景深） -->
    <div class="bg-effects" aria-hidden="true">
      <div class="orb orb-a" />
      <div class="orb orb-b" />
      <div class="orb orb-c" />
      <div class="grid-floor" />
    </div>

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
        <el-button type="primary" class="login-btn" @click="goToLogin">
          <el-icon><User /></el-icon>
          ログイン
        </el-button>
      </div>
    </header>

    <main class="main">
      <div class="hero">
        <div class="hero-layout">
          <div class="hero-content">
            <h1 class="hero-title">
              製造業の<br />
              <span class="gradient-text">デジタルトランスフォーメーション</span>
            </h1>
            <p class="hero-subtitle">
              ERP・APS・MESを統合した次世代管理システム。リアルタイム可視化から計画立案まで、ひとつのプラットフォームで。
            </p>
            <div class="hero-actions">
              <el-button type="primary" size="large" class="cta-btn" @click="goToLogin">
                今すぐ始める
                <el-icon class="btn-arrow"><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>

          <!-- CSS 3D 展示：悬浮模块 + 底座 -->
          <div class="hero-showcase" aria-hidden="true">
            <div class="showcase-stage">
              <div class="showcase-plate" />
              <div class="showcase-glow" />
              <div
                v-for="(block, i) in showcaseBlocks"
                :key="block.label"
                class="float-block"
                :class="`float-block--${i + 1}`"
              >
                <span class="float-block__shine" />
                <el-icon class="float-block__icon" :size="22"><component :is="block.icon" /></el-icon>
                <span class="float-block__label">{{ block.label }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="features-grid">
          <div
            v-for="feature in features"
            :key="feature.title"
            class="feature-card"
            :style="{ '--accent': feature.accent }"
          >
            <div class="feature-card__inner">
              <div class="feature-icon">
                <el-icon :size="26"><component :is="feature.icon" /></el-icon>
              </div>
              <div class="feature-content">
                <h3>{{ feature.title }}</h3>
                <p class="feature-name">{{ feature.name }}</p>
                <p class="feature-desc">{{ feature.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <footer class="footer">
      <p>&copy; 2026 Smart-EMAP. All rights reserved.</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { markRaw } from 'vue'
import { useRouter } from 'vue-router'
import {
  Management,
  DataAnalysis,
  Monitor,
  DataBoard,
  User,
  ArrowRight,
} from '@element-plus/icons-vue'

const router = useRouter()

const goToLogin = () => {
  router.push('/login')
}

const showcaseBlocks = [
  { label: 'ERP', icon: markRaw(Management) },
  { label: 'APS', icon: markRaw(DataAnalysis) },
  { label: 'MES', icon: markRaw(Monitor) },
]

const features = [
  {
    title: 'ERP',
    name: '企業資源計画',
    description: '経営判断に必要な情報を一元管理',
    icon: markRaw(Management),
    accent: '168, 85, 247',
  },
  {
    title: 'APS',
    name: '先進的計画・スケジューリング',
    description: '最適化された生産計画を立案',
    icon: markRaw(DataAnalysis),
    accent: '244, 63, 94',
  },
  {
    title: 'MES',
    name: '製造実行システム',
    description: '現場のリアルタイム情報収集',
    icon: markRaw(Monitor),
    accent: '6, 182, 212',
  },
]
</script>

<style scoped>
.home-container {
  --home-bg0: #0f0a1f;
  --home-bg1: #1a1040;
  --home-bg2: #12082a;
  --glass: rgba(255, 255, 255, 0.08);
  --glass-border: rgba(255, 255, 255, 0.14);
  --text: #f8fafc;
  --text-muted: rgba(248, 250, 252, 0.72);

  position: relative;
  isolation: isolate;
  min-height: 100vh;
  min-height: 100dvh;
  background: radial-gradient(120% 80% at 80% 0%, #2d1b69 0%, transparent 55%),
    radial-gradient(90% 60% at 0% 100%, #0c4a6e 0%, transparent 45%),
    linear-gradient(165deg, var(--home-bg0) 0%, var(--home-bg1) 45%, var(--home-bg2) 100%);
  display: flex;
  flex-direction: column;
  overflow-x: clip;
}

.bg-effects {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.55;
  animation: orb-drift 18s ease-in-out infinite;
}

.orb-a {
  width: min(42vw, 420px);
  height: min(42vw, 420px);
  background: #7c3aed;
  top: -12%;
  right: -8%;
  animation-delay: 0s;
}

.orb-b {
  width: min(50vw, 480px);
  height: min(50vw, 480px);
  background: #0891b2;
  bottom: -18%;
  left: -15%;
  animation-delay: -6s;
}

.orb-c {
  width: min(36vw, 320px);
  height: min(36vw, 320px);
  background: #db2777;
  top: 38%;
  left: 35%;
  opacity: 0.35;
  animation-delay: -12s;
}

.grid-floor {
  position: absolute;
  inset: -40% -20% 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  transform: perspective(600px) rotateX(72deg);
  transform-origin: 50% 100%;
  mask-image: linear-gradient(to bottom, transparent 0%, rgba(0, 0, 0, 0.35) 40%, black 100%);
  -webkit-mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    rgba(0, 0, 0, 0.35) 40%,
    black 100%
  );
}

@keyframes orb-drift {
  0%,
  100% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(-3%, 4%) scale(1.06);
  }
}

/* Header */
.header {
  position: relative;
  z-index: 2;
  padding: 14px 20px;
  padding-top: max(14px, env(safe-area-inset-top));
  background: linear-gradient(to bottom, rgba(15, 10, 31, 0.75), transparent);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.logo-icon {
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.22), rgba(255, 255, 255, 0.05));
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);
  transform: translateZ(0);
}

.logo-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.logo-title {
  font-size: clamp(17px, 4vw, 20px);
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}

.logo-sub {
  font-size: 11px;
  color: var(--text-muted);
}

.login-btn {
  flex-shrink: 0;
  background: var(--glass) !important;
  border: 1px solid var(--glass-border) !important;
  color: var(--text) !important;
  backdrop-filter: blur(12px);
  border-radius: 12px !important;
  padding: 10px 18px !important;
  height: auto !important;
  min-height: 44px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.12);
  transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}

.login-btn:hover {
  background: rgba(255, 255, 255, 0.14) !important;
  transform: translateY(-1px);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.28);
}

/* Main */
.main {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px 48px;
  padding-bottom: max(48px, env(safe-area-inset-bottom));
}

.hero {
  width: 100%;
  max-width: 1180px;
}

.hero-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(260px, 0.95fr);
  gap: clamp(28px, 5vw, 56px);
  align-items: center;
  margin-bottom: clamp(36px, 6vw, 56px);
}

.hero-content {
  text-align: left;
}

.hero-title {
  font-size: clamp(32px, 5.2vw, 52px);
  font-weight: 800;
  color: var(--text);
  line-height: 1.12;
  margin: 0 0 16px;
  letter-spacing: -0.03em;
  text-shadow: 0 4px 40px rgba(0, 0, 0, 0.35);
}

.gradient-text {
  background: linear-gradient(120deg, #a5f3fc 0%, #c4b5fd 35%, #f9a8d4 70%, #fde68a 100%);
  background-size: 180% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: shimmer 8s linear infinite;
}

@keyframes shimmer {
  0% {
    background-position: 0% center;
  }
  100% {
    background-position: 200% center;
  }
}

.hero-subtitle {
  font-size: clamp(15px, 1.75vw, 18px);
  line-height: 1.65;
  color: var(--text-muted);
  margin: 0 0 28px;
  max-width: 36em;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.cta-btn {
  background: linear-gradient(135deg, #e0e7ff 0%, #f5f3ff 40%, #ffffff 100%) !important;
  color: #312e81 !important;
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  font-weight: 700 !important;
  padding: 14px 28px !important;
  font-size: 16px !important;
  border-radius: 14px !important;
  min-height: 48px;
  box-shadow: 0 4px 0 rgba(49, 46, 129, 0.12), 0 16px 40px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.85);
  transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease;
}

.cta-btn:hover {
  transform: translateY(-3px);
  filter: brightness(1.03);
  box-shadow: 0 6px 0 rgba(49, 46, 129, 0.1), 0 24px 48px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.cta-btn:active {
  transform: translateY(-1px);
}

.btn-arrow {
  margin-left: 8px;
  transition: transform 0.25s ease;
}

.cta-btn:hover .btn-arrow {
  transform: translateX(5px);
}

/* 3D showcase */
.hero-showcase {
  perspective: 1000px;
  perspective-origin: 50% 40%;
  min-height: min(320px, 55vw);
  display: flex;
  align-items: center;
  justify-content: center;
}

.showcase-stage {
  position: relative;
  width: min(100%, 340px);
  height: 280px;
  transform-style: preserve-3d;
  animation: stage-tilt 12s ease-in-out infinite;
}

@keyframes stage-tilt {
  0%,
  100% {
    transform: rotateX(8deg) rotateY(-12deg) rotateZ(0deg);
  }
  50% {
    transform: rotateX(10deg) rotateY(8deg) rotateZ(-1deg);
  }
}

.showcase-plate {
  position: absolute;
  left: 50%;
  bottom: 12%;
  width: 88%;
  height: 42%;
  transform: translateX(-50%) rotateX(78deg);
  transform-origin: center bottom;
  background: linear-gradient(
    135deg,
    rgba(124, 58, 237, 0.45),
    rgba(6, 182, 212, 0.25)
  );
  border-radius: 20px;
  box-shadow: 0 0 60px rgba(124, 58, 237, 0.35), inset 0 0 40px rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.showcase-glow {
  position: absolute;
  left: 50%;
  bottom: 18%;
  width: 70%;
  height: 28%;
  transform: translateX(-50%) translateZ(-40px) rotateX(78deg);
  background: radial-gradient(ellipse at center, rgba(167, 139, 250, 0.55), transparent 70%);
  filter: blur(20px);
  opacity: 0.85;
}

.float-block {
  position: absolute;
  width: 108px;
  padding: 14px 12px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #f8fafc;
  transform-style: preserve-3d;
  background: linear-gradient(155deg, rgba(255, 255, 255, 0.16) 0%, rgba(255, 255, 255, 0.04) 100%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35),
    inset 0 -8px 16px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.float-block__shine {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(125deg, rgba(255, 255, 255, 0.35), transparent 42%);
  opacity: 0.45;
  pointer-events: none;
}

.float-block__icon {
  position: relative;
  z-index: 1;
}

.float-block__label {
  position: relative;
  z-index: 1;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: 0.12em;
}

.float-block--1 {
  left: 4%;
  top: 18%;
  animation: bob-z48 5s ease-in-out infinite;
  animation-delay: 0s;
}

.float-block--2 {
  left: 50%;
  top: 6%;
  animation: bob-z88 5s ease-in-out infinite;
  animation-delay: -1.6s;
}

.float-block--3 {
  right: 2%;
  top: 22%;
  animation: bob-z32 5s ease-in-out infinite;
  animation-delay: -3.2s;
}

@keyframes bob-z48 {
  0%,
  100% {
    transform: translate3d(0, 0, 48px);
  }
  50% {
    transform: translate3d(0, -10px, 52px);
  }
}

@keyframes bob-z88 {
  0%,
  100% {
    transform: translate3d(-50%, 0, 88px);
  }
  50% {
    transform: translate3d(-50%, -12px, 96px);
  }
}

@keyframes bob-z32 {
  0%,
  100% {
    transform: translate3d(0, 0, 32px);
  }
  50% {
    transform: translate3d(0, -10px, 38px);
  }
}

/* Feature cards — 立体卡片 + hover */
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(16px, 3vw, 24px);
  perspective: 960px;
}

.feature-card {
  position: relative;
  border-radius: 20px;
  padding: 1px;
  background: linear-gradient(
    145deg,
    rgba(var(--accent), 0.55),
    rgba(255, 255, 255, 0.12)
  );
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.35);
  transform-style: preserve-3d;
  transition: transform 0.35s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.35s ease;
}

.feature-card::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(
    120% 80% at 10% 0%,
    rgba(var(--accent), 0.35),
    transparent 55%
  );
  opacity: 0.85;
  pointer-events: none;
}

.feature-card:hover {
  transform: translateY(-8px) rotateX(4deg);
  box-shadow: 0 32px 64px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.feature-card__inner {
  position: relative;
  border-radius: 19px;
  padding: 24px 22px;
  text-align: center;
  background: linear-gradient(165deg, rgba(22, 16, 45, 0.94) 0%, rgba(15, 10, 31, 0.92) 100%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
  overflow: hidden;
}

.feature-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 14px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f8fafc;
  background: radial-gradient(circle at 30% 25%, rgba(var(--accent), 0.85), rgba(var(--accent), 0.35));
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}

.feature-content h3 {
  font-size: clamp(22px, 4vw, 28px);
  font-weight: 800;
  color: var(--text);
  margin: 0 0 6px;
  letter-spacing: -0.02em;
}

.feature-name {
  font-size: 13px;
  font-weight: 700;
  color: rgba(var(--accent), 1);
  margin: 0 0 10px;
}

.feature-desc {
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-muted);
  margin: 0;
}

/* Footer */
.footer {
  position: relative;
  z-index: 2;
  padding: 20px;
  padding-bottom: max(20px, env(safe-area-inset-bottom));
  text-align: center;
}

.footer p {
  margin: 0;
  font-size: 12px;
  color: rgba(248, 250, 252, 0.45);
}

/* Responsive */
@media (max-width: 900px) {
  .hero-layout {
    grid-template-columns: 1fr;
    grid-auto-flow: row dense;
    text-align: center;
    margin-bottom: 28px;
  }

  .hero-content {
    text-align: center;
  }

  .hero-subtitle {
    margin-left: auto;
    margin-right: auto;
  }

  .hero-actions {
    justify-content: center;
  }

  .hero-showcase {
    min-height: 260px;
    order: -1;
    margin-bottom: 8px;
  }

  .showcase-stage {
    height: 240px;
  }
}

@media (max-width: 640px) {
  .features-grid {
    grid-template-columns: 1fr;
  }

  .float-block {
    width: 96px;
    padding: 12px 10px;
  }

  .hero-showcase {
    transform: scale(0.92);
    transform-origin: center center;
  }
}

@media (max-width: 380px) {
  .header-content {
    flex-wrap: wrap;
    justify-content: center;
    row-gap: 10px;
  }

  .logo {
    flex: 1 1 auto;
    justify-content: center;
  }

  .login-btn {
    width: 100%;
    justify-content: center;
  }
}

/* 无障碍：减少动态效果 */
@media (prefers-reduced-motion: reduce) {
  .orb,
  .showcase-stage,
  .gradient-text,
  .float-block--1,
  .float-block--2,
  .float-block--3 {
    animation: none !important;
  }

  .showcase-stage {
    transform: rotateX(9deg) rotateY(-8deg);
  }

  .float-block--1 {
    transform: translate3d(0, 0, 48px);
  }

  .float-block--2 {
    transform: translate3d(-50%, 0, 88px);
  }

  .float-block--3 {
    transform: translate3d(0, 0, 32px);
  }

  .feature-card:hover {
    transform: none;
  }

  .cta-btn:hover,
  .login-btn:hover {
    transform: none;
  }
}
</style>
