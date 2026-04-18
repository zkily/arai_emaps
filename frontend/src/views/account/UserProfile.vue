<template>
  <div class="user-profile">
    <div class="user-profile__header">
      <h1 class="user-profile__title">{{ t('profilePage.title') }}</h1>
      <p class="user-profile__desc">{{ t('profilePage.desc') }}</p>
    </div>

    <UserProfilePanel />
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import UserProfilePanel from '@/components/account/UserProfilePanel.vue'

const { t } = useI18n()
</script>

<style scoped>
.user-profile {
  padding: 8px 4px 24px;
  max-width: 720px;
}

.user-profile__header {
  margin-bottom: 20px;
}

.user-profile__title {
  margin: 0 0 8px;
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: 0.02em;
}

.user-profile__desc {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}
</style>
