<template>
  <el-dialog
    :model-value="modelValue"
    title="納入先選択"
    width="900px"
    @update:model-value="$emit('update:modelValue', $event)"
    class="destination-select-dialog"
  >
    <div class="dialog-content">
      <!-- 操作按钮区域 - 移到顶部 -->
      <div class="action-section">
        <el-button @click="handleClear" class="action-button clear-button" size="small">
          <el-icon><Delete /></el-icon>
          クリア
        </el-button>
        <div class="action-right">
          <el-button
            @click="$emit('update:modelValue', false)"
            class="action-button cancel-button"
            size="small"
          >
            <el-icon><Close /></el-icon>
            キャンセル
          </el-button>
          <el-button
            type="primary"
            @click="handleConfirm"
            class="action-button confirm-button"
            size="small"
          >
            <el-icon><Check /></el-icon>
            確定
          </el-button>
        </div>
      </div>

      <!-- 搜索和排序控制区域 -->
      <div class="control-section">
        <el-input
          v-model="searchKeyword"
          placeholder="納入先コードまたは名称で検索"
          clearable
          class="search-input"
          size="default"
        >
          <template #prepend>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <div class="sort-controls">
          <el-button-group>
            <el-button
              :type="sortBy === 'code' ? 'primary' : 'default'"
              @click="setSortBy('code')"
              class="sort-button"
              size="small"
            >
              <el-icon><Grid /></el-icon>
              コード順
            </el-button>
            <el-button
              :type="sortBy === 'name' ? 'primary' : 'default'"
              @click="setSortBy('name')"
              class="sort-button"
              size="small"
            >
              <el-icon><Menu /></el-icon>
              名称順
            </el-button>
          </el-button-group>

          <el-button
            @click="toggleSortOrder"
            class="sort-order-button"
            :type="sortOrder === 'asc' ? 'primary' : 'default'"
            size="small"
          >
            <el-icon v-if="sortOrder === 'asc'"><ArrowUp /></el-icon>
            <el-icon v-else><ArrowDown /></el-icon>
            {{ sortOrder === 'asc' ? '昇順' : '降順' }}
          </el-button>
        </div>
      </div>

      <!-- 数量显示 -->
      <div class="result-info">
        <span class="result-count">
          <el-icon><DataAnalysis /></el-icon>
          {{ filteredDestinations.length }}件表示
        </span>
        <span v-if="selectedDestination" class="selected-info">
          <el-icon><CircleCheckFilled /></el-icon>
          選択中: {{ getSelectedDestinationName }}
        </span>
      </div>

      <!-- 目的地列表 -->
      <el-scrollbar height="500px" class="destination-list-scrollbar">
        <div class="destination-grid">
          <div
            v-for="dest in sortedDestinations"
            :key="dest.value"
            class="destination-button compact-button"
            :class="{ selected: dest.value === selectedDestination }"
            @click="handleSelect(dest)"
          >
            <div class="button-content">
              <div class="destination-code">{{ dest.value }}</div>
              <div class="destination-name">{{ dest.label }}</div>
            </div>
            <div v-if="dest.value === selectedDestination" class="selected-indicator">
              <el-icon class="selected-icon"><CircleCheckFilled /></el-icon>
            </div>
          </div>

          <el-empty
            v-if="filteredDestinations.length === 0"
            description="該当する納入先がありません"
            class="empty-state"
          />
        </div>
      </el-scrollbar>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  Search,
  CircleCheckFilled,
  Grid,
  Menu,
  ArrowUp,
  ArrowDown,
  DataAnalysis,
  Delete,
  Check,
  Close,
} from '@element-plus/icons-vue'

interface DestinationOption {
  value: string
  label: string
}

const props = defineProps<{
  modelValue: boolean
  destinations: DestinationOption[]
  currentDestination: string | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  select: [destination: DestinationOption | null]
}>()

const searchKeyword = ref('')
const selectedDestination = ref<string | null>(props.currentDestination)
const sortBy = ref<'code' | 'name'>('code')
const sortOrder = ref<'asc' | 'desc'>('asc')

watch(
  () => props.currentDestination,
  (newValue) => {
    selectedDestination.value = newValue
  },
)

const filteredDestinations = computed(() => {
  if (!searchKeyword.value) {
    return props.destinations
  }
  const keyword = searchKeyword.value.toLowerCase()
  return props.destinations.filter(
    (dest) =>
      dest.value.toLowerCase().includes(keyword) || dest.label.toLowerCase().includes(keyword),
  )
})

const sortedDestinations = computed(() => {
  const destinations = [...filteredDestinations.value]

  destinations.sort((a, b) => {
    let compareResult = 0

    if (sortBy.value === 'code') {
      compareResult = a.value.localeCompare(b.value)
    } else {
      compareResult = a.label.localeCompare(b.label)
    }

    return sortOrder.value === 'asc' ? compareResult : -compareResult
  })

  return destinations
})

const getSelectedDestinationName = computed(() => {
  const destination = props.destinations.find((d) => d.value === selectedDestination.value)
  return destination ? destination.label : ''
})

const setSortBy = (type: 'code' | 'name') => {
  sortBy.value = type
}

const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

const handleSelect = (destination: DestinationOption) => {
  selectedDestination.value = destination.value
}

const handleClear = () => {
  selectedDestination.value = null
}

const handleConfirm = () => {
  const destination = props.destinations.find((d) => d.value === selectedDestination.value)
  emit('select', destination || null)
  emit('update:modelValue', false)
}
</script>

<style scoped>
.destination-select-dialog :deep(.el-dialog) {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.1);
}

.destination-select-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px 16px 0 0;
  padding: 20px 24px;
  border-bottom: none;
}

.destination-select-dialog :deep(.el-dialog__title) {
  font-weight: 700;
  color: white;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.destination-select-dialog :deep(.el-dialog__headerbtn) {
  top: 20px;
  right: 24px;
}

.destination-select-dialog :deep(.el-dialog__close) {
  color: white;
  font-size: 18px;
}

.destination-select-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.dialog-content {
  padding: 0;
}

/* 操作按钮区域样式 */
.action-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border-radius: 12px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.action-right {
  display: flex;
  gap: 8px;
}

.action-button {
  border-radius: 8px;
  padding: 8px 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  min-width: 80px;
  font-size: 12px;
}

.action-button.clear-button {
  background: linear-gradient(135deg, #f87171, #dc2626);
  color: white;
  border: none;
}

.action-button.clear-button:hover {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(248, 113, 113, 0.3);
}

.action-button.cancel-button {
  background: linear-gradient(135deg, #9ca3af, #6b7280);
  color: white;
  border: none;
}

.action-button.cancel-button:hover {
  background: linear-gradient(135deg, #6b7280, #4b5563);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(156, 163, 175, 0.3);
}

.action-button.confirm-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
}

.action-button.confirm-button:hover {
  background: linear-gradient(135deg, #5a6fd8, #6a4c93);
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(102, 126, 234, 0.3);
}

.control-section {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  align-items: center;
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 300px;
}

.search-input :deep(.el-input-group__prepend) {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 0 8px 8px 0;
  transition: all 0.3s ease;
}

.search-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.sort-controls {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.sort-button {
  border-radius: 8px;
  transition: all 0.3s ease;
  font-weight: 600;
}

.sort-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.sort-order-button {
  border-radius: 8px;
  transition: all 0.3s ease;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

.sort-order-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.result-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.1);
}

.result-count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #475569;
  font-size: 14px;
}

.selected-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #667eea;
  font-size: 14px;
  background: rgba(102, 126, 234, 0.1);
  padding: 4px 12px;
  border-radius: 16px;
}

.destination-list-scrollbar {
  background: white;
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.destination-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.destination-button {
  min-height: 80px;
  padding: 16px;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  background: linear-gradient(135deg, #ffffff, #f8fafc);
  transition: all 0.3s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.destination-button.compact-button {
  min-height: 60px;
  padding: 12px;
}

.destination-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.1), transparent);
  transition: left 0.5s;
}

.destination-button:hover::before {
  left: 100%;
}

.destination-button:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
  border-color: #667eea;
}

.destination-button.selected {
  background: linear-gradient(135deg, #e9eafc, #f3f4ff);
  border-color: #667eea;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.25);
  transform: translateY(-2px);
}

.button-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  flex: 1;
}

.destination-code {
  font-weight: 700;
  font-size: 14px;
  color: #1e293b;
  line-height: 1.2;
}

.compact-button .destination-code {
  font-size: 13px;
}

.destination-button.selected .destination-code {
  color: #667eea;
}

.destination-name {
  font-size: 12px;
  color: #64748b;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 180px;
}

.compact-button .destination-name {
  font-size: 11px;
}

.destination-button.selected .destination-name {
  color: #667eea;
  font-weight: 500;
}

.selected-indicator {
  flex-shrink: 0;
  animation: selectedPulse 1.5s infinite;
}

@keyframes selectedPulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.selected-icon {
  font-size: 20px;
  color: #667eea;
  filter: drop-shadow(0 2px 4px rgba(102, 126, 234, 0.3));
}

.compact-button .selected-icon {
  font-size: 18px;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 40px 20px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .destination-select-dialog :deep(.el-dialog) {
    width: 95% !important;
    margin: 0 auto;
  }

  .control-section {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    min-width: 100%;
  }

  .sort-controls {
    justify-content: center;
  }

  .destination-grid {
    grid-template-columns: 1fr;
    gap: 8px;
  }

  .destination-button {
    min-height: 60px;
    padding: 12px;
  }

  .destination-code {
    font-size: 14px;
  }

  .destination-name {
    font-size: 12px;
    max-width: 200px;
  }

  .action-section {
    flex-direction: column;
    gap: 12px;
    padding: 12px 15px;
  }

  .action-right {
    width: 100%;
    justify-content: space-between;
  }

  .action-button {
    flex: 1;
    min-width: auto;
  }
}

@media (max-width: 1200px) and (min-width: 769px) {
  .destination-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
