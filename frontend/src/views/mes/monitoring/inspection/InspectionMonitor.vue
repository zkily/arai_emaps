<script setup lang="ts">
import ProcessMonitorPage from '../shared/ProcessMonitorPage.vue'

defineOptions({ name: 'InspectionMonitor' })
</script>

<template>
  <ProcessMonitorPage process-key="inspection" />
</template>
