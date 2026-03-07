<template>
  <el-dialog
    v-model="visible"
    title="納入先グループ管理"
    width="56%"
    :close-on-click-modal="false"
    class="destination-group-dialog"
    @close="handleClose"
  >
    <div class="group-manager">
      <!-- 利用可能な納入先（各グループで重複選択可） -->
      <div class="destinations-section">
        <div class="section-row">
          <span class="section-title">
            <el-icon><Collection /></el-icon>
            利用可能な納入先
          </span>
          <span class="section-hint">（各グループで重複選択可）</span>
        </div>
        <div class="destinations-container">
          <div v-for="destination in availableDestinations" :key="destination.value"
            :data-destination="JSON.stringify(destination)" class="destination-tag" draggable="true"
            @dragstart="handleDragStart"
            @touchstart="handleTouchStart($event, destination)"
            @touchcancel="handleTouchCancel">
            <el-tag size="default" type="info" class="draggable-tag">
              {{ destination.label }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- グループ管理 -->
      <div class="groups-section">
        <div class="section-row groups-header">
          <span class="section-title">
            <el-icon><Box /></el-icon>
            グループ管理
          </span>
          <el-button type="primary" size="small" @click="showCreateGroupDialog" class="btn-create">
            <el-icon><Plus /></el-icon>
            新規作成
          </el-button>
        </div>

        <div class="groups-container">
          <div v-for="(group, index) in groups" :key="group.id || index"
            :class="['group-container', `group-${(index % 3) + 1}`]"
            :data-group-index="String(index)"
            @drop="handleDrop($event, index)"
            @dragover="handleDragOver" @dragenter="handleDragEnter" @dragleave="handleDragLeave">
            <div class="group-header">
              <div class="group-title">
                <el-input
                  v-if="group.editing"
                  v-model="group.groupName"
                  size="small"
                  @blur="saveGroupName(group)"
                  @keyup.enter="saveGroupName(group)"
                  ref="groupNameInput"
                  class="group-name-input"
                />
                <h4 v-else @dblclick="editGroupName(group)">
                  <el-icon><Box /></el-icon>
                  {{ group.groupName }}
                  <el-badge :value="group.destinations.length" type="primary" class="group-badge" />
                </h4>
              </div>
              <div class="group-actions">
                <el-button size="small" type="primary" text @click="editGroupName(group)" title="編集" class="btn-icon">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" type="warning" text @click="clearGroup(index)"
                  :disabled="group.destinations.length === 0" title="クリア" class="btn-icon">
                  <el-icon><Delete /></el-icon>
                </el-button>
                <el-button size="small" type="danger" text @click="deleteGroup(group, index)" title="削除" class="btn-icon">
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
            </div>
            <div class="group-content">
              <div v-for="destination in group.destinations" :key="destination.value" class="group-item">
                <el-tag :type="getGroupTagType(index)" closable @close="removeFromGroup(index, destination)">
                  {{ destination.label }}
                </el-tag>
              </div>
              <div v-if="group.destinations.length === 0" class="empty-group">
                <el-icon><Plus /></el-icon>
                <span>ここにドラッグ</span>
                <span class="touch-hint">長押しでドラッグ</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="actions-section">
        <el-button size="small" @click="autoAssignByIssueType" :loading="autoAssignLoading" class="btn-action">
          <el-icon><Star /></el-icon>
          一键分配
        </el-button>
        <el-button type="primary" size="small" @click="saveAndClose" :loading="saveLoading" class="btn-action btn-save">
          <el-icon><Check /></el-icon>
          保存
        </el-button>
      </div>
    </div>

    <!-- 创建新分组对话框 -->
    <el-dialog v-model="createGroupDialogVisible" title="新規グループ作成" width="400px" :close-on-click-modal="false">
      <el-form :model="newGroupForm" label-width="120px">
        <el-form-item label="グループ名">
          <el-input v-model="newGroupForm.groupName" placeholder="グループ名を入力してください" maxlength="50" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createGroupDialogVisible = false">キャンセル</el-button>
          <el-button type="primary" @click="createGroup" :disabled="!newGroupForm.groupName.trim()">
            作成
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 触摸拖拽时的跟随幽灵（手机/平板用） -->
    <Teleport to="body">
      <div
        v-show="touchDragActive"
        ref="touchDragGhostRef"
        class="touch-drag-ghost"
        :style="touchGhostStyle"
      >
        <el-tag size="default" type="info" class="draggable-tag">{{ touchDragLabel }}</el-tag>
      </div>
    </Teleport>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Collection, Box, Plus, Edit, Delete, Close, Check, Star } from '@element-plus/icons-vue'
import request from '@/utils/request'
import type { Ref } from 'vue'

// 类型定义
interface Destination {
  value: string
  label: string
  issue_type?: string | number
}

interface Group {
  id?: number
  groupName: string
  group_name?: string
  destinations: Destination[]
  editing?: boolean
}

// Props
const props = defineProps<{
  modelValue: boolean
  pageKey: string
}>()

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'groupsUpdated': [groups: Group[]]
}>()

// 响应式数据
const visible = ref(props.modelValue)
const loading = ref(false)
const saveLoading = ref(false)
const autoAssignLoading = ref(false)
const allDestinations: Ref<Destination[]> = ref([])
const allDestinationsWithIssueType: Ref<Destination[]> = ref([])
const groups: Ref<Group[]> = ref([])
const createGroupDialogVisible = ref(false)
const groupNameInput = ref<HTMLElement[]>()

// 触摸拖拽状态（手机/平板）
const touchDragGhostRef = ref<HTMLElement | null>(null)
const touchDragActive = ref(false)
const touchDragPayload = ref<Destination | null>(null)
const touchGhostX = ref(0)
const touchGhostY = ref(0)
const longPressTimer = ref<ReturnType<typeof setTimeout> | null>(null)
let touchMoveHandler: ((e: TouchEvent) => void) | null = null
let touchEndHandler: ((e: TouchEvent) => void) | null = null
let touchCancelHandler: ((e: TouchEvent) => void) | null = null

const touchDragLabel = computed(() => touchDragPayload.value?.label ?? '')
const touchGhostStyle = computed(() => ({
  left: `${touchGhostX.value}px`,
  top: `${touchGhostY.value}px`,
}))

// 新建分组表单
const newGroupForm = reactive({
  groupName: '',
})

// 利用可能な納入先：常に全件表示し、各グループで重複選択可能
const availableDestinations = computed(() => [...allDestinations.value])

// 监听props变化
watch(
  () => props.modelValue,
  (newVal) => {
    visible.value = newVal
    if (newVal) {
      loadDestinations()
      loadDestinationsWithIssueType()
      loadGroups()
    }
  },
)

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 生命周期
onMounted(() => {
  if (visible.value) {
    loadDestinations()
    loadDestinationsWithIssueType()
    loadGroups()
  }
})

onUnmounted(() => {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
  removeTouchListeners()
})

// API响应类型定义
interface DestinationApiItem {
  cd: string
  name: string
  issue_type?: string | number
}

interface ApiResponse {
  success?: boolean
  data?: DestinationApiItem[]
}

// 方法
async function loadDestinations() {
  try {
    loading.value = true
    const response: ApiResponse | DestinationApiItem[] = await request.get('/api/master/destinations/options')

    // 处理不同的响应格式
    let data: DestinationApiItem[] | null = null
    if (response && 'success' in response && response.success === true && Array.isArray(response.data)) {
      data = response.data
    } else if (Array.isArray(response)) {
      data = response
    } else if (response && 'data' in response && Array.isArray(response.data)) {
      data = response.data
    }

    if (data && Array.isArray(data)) {
      allDestinations.value = data.map((item: DestinationApiItem) => ({
        value: item.cd,
        label: `${item.cd} - ${item.name}`,
      }))
    } else {
      console.error('納入先データ格式不正确:', response)
      ElMessage.error('納入先データの取得に失敗しました')
    }
  } catch (error) {
    console.error('获取纳入先失败:', error)
    ElMessage.error('納入先データの取得に失敗しました')
  } finally {
    loading.value = false
  }
}

// 加载带有issue_type的纳入先数据
async function loadDestinationsWithIssueType() {
  try {
    const response: ApiResponse | DestinationApiItem[] = await request.get('/api/master/destinations/options-with-issue-type')

    let data: DestinationApiItem[] | null = null
    if (response && 'success' in response && response.success === true && Array.isArray(response.data)) {
      data = response.data
    } else if (Array.isArray(response)) {
      data = response
    } else if (response && 'data' in response && Array.isArray(response.data)) {
      data = response.data
    }

    if (data && Array.isArray(data)) {
      allDestinationsWithIssueType.value = data.map((item: DestinationApiItem) => ({
        value: item.cd,
        label: `${item.cd} - ${item.name}`,
        issue_type: item.issue_type,
      }))
    }
  } catch (error) {
    console.error('获取带有issue_type的纳入先失败:', error)
  }
}

// 分组API响应类型定义
interface GroupApiItem {
  id: number
  group_name: string
  destinations: Destination[]
}

// 加载分组数据
async function loadGroups() {
  try {
    loading.value = true
    const response: GroupApiItem[] = await request.get(`/api/shipping/destination-groups/${props.pageKey}`)

    // 响应拦截器会直接返回数据数组，所以我们检查它是否是数组
    if (Array.isArray(response)) {
      groups.value = response.map((group: GroupApiItem) => ({
        ...group,
        groupName: group.group_name, // 从后端的 snake_case 映射到前端的 camelCase
        destinations: group.destinations || [],
        editing: false,
      }))
    } else {
      groups.value = []
    }
  } catch (error) {
    console.error('分组数据加载失败:', error)
    ElMessage.error('分組データの取得に失敗しました')
    groups.value = []
  } finally {
    loading.value = false
  }
}

// 显示创建分组对话框
function showCreateGroupDialog() {
  newGroupForm.groupName = ''
  createGroupDialogVisible.value = true
}

// 创建新分组
async function createGroup() {
  try {
    const response = await request.post('/api/shipping/destination-groups', {
      pageKey: props.pageKey,
      groupName: newGroupForm.groupName.trim(),
      destinations: [],
    })

    // 成功时，response是返回的data对象（request 拦截器返回 response.data）
    const data = response as { id?: number }
    if (data && data.id) {
      ElMessage.success('グループが作成されました')
      createGroupDialogVisible.value = false
      await loadGroups()
    } else {
      ElMessage.error('グループの作成に失敗しました')
    }
  } catch (error) {
    console.error('创建分组失败:', error)
    ElMessage.error('グループの作成に失敗しました')
  }
}

// 编辑分组名
function editGroupName(group: Group) {
  group.editing = true
  nextTick(() => {
    if (groupNameInput.value && groupNameInput.value.length > 0) {
      groupNameInput.value[0]?.focus()
    }
  })
}

// 保存分组名
async function saveGroupName(group: Group) {
  group.editing = false
  if (!group.groupName.trim()) {
    ElMessage.error('グループ名は必須です')
    await loadGroups()
    return
  }

  try {
    const response = await request.put(`/api/shipping/destination-groups/${group.id}`, {
      groupName: group.groupName.trim(),
      destinations: group.destinations,
    }) as { success?: boolean } | undefined

    if (response && response.success) {
      ElMessage.success('グループ名が更新されました')
    } else {
      ElMessage.error('グループ名の更新に失敗しました')
      await loadGroups()
    }
  } catch (error) {
    console.error('分组名保存失败:', error)
    ElMessage.error('グループ名の更新に失敗しました')
    await loadGroups()
  }
}

// 删除分组
// eslint-disable-next-line @typescript-eslint/no-unused-vars
async function deleteGroup(group: Group, _index: number) {
  try {
    await ElMessageBox.confirm(`グループ「${group.groupName}」を削除しますか？`, '確認', {
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
      type: 'warning',
    })

    const response = await request.delete(`/api/shipping/destination-groups/${group.id}`) as { success?: boolean } | undefined

    if (response && response.success) {
      ElMessage.success('グループが削除されました')
      await loadGroups()
    } else {
      ElMessage.error('グループの削除に失敗しました')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除分组失败:', error)
      ElMessage.error('グループの削除に失敗しました')
    }
  }
}

// 清空分组
function clearGroup(index: number) {
  groups.value[index].destinations = []
}

// 按issue_type自动分配
async function autoAssignByIssueType() {
  try {
    autoAssignLoading.value = true

    // 确保至少有3个分组
    while (groups.value.length < 3) {
      const groupNumber = groups.value.length + 1
      await request.post('/api/shipping/destination-groups', {
        pageKey: props.pageKey,
        groupName: `グループ${groupNumber}`,
        destinations: [],
      })
    }

    // 重新加载分组
    await loadGroups()

    // 清空前3个分组
    for (let i = 0; i < Math.min(3, groups.value.length); i++) {
      groups.value[i].destinations = []
    }

    // 按issue_type分组
    const groupsByIssueType: Record<number, Destination[]> = {}
    allDestinationsWithIssueType.value.forEach((dest: Destination) => {
      let issueTypeNum = 1 // 默认分配到组1

      if (dest.issue_type) {
        if (typeof dest.issue_type === 'string') {
          const parsed = parseInt(dest.issue_type.trim())
          if (!isNaN(parsed) && parsed >= 1 && parsed <= 3) {
            issueTypeNum = parsed
          } else if (dest.issue_type === '自動') {
            issueTypeNum = 1
          } else if (dest.issue_type === '手動') {
            issueTypeNum = 2
          }
        } else if (typeof dest.issue_type === 'number') {
          if (dest.issue_type >= 1 && dest.issue_type <= 3) {
            issueTypeNum = dest.issue_type
          }
        }
      }

      if (!groupsByIssueType[issueTypeNum]) {
        groupsByIssueType[issueTypeNum] = []
      }
      groupsByIssueType[issueTypeNum].push(dest)
    })

    // 分配到对应的分组
    Object.keys(groupsByIssueType).forEach((issueType: string) => {
      const groupIndex = parseInt(issueType) - 1
      if (groupIndex >= 0 && groupIndex < groups.value.length) {
        groups.value[groupIndex].destinations = groupsByIssueType[parseInt(issueType)]
      }
    })

    const totalAssigned = Object.values(groupsByIssueType).reduce(
      (sum: number, group: Destination[]) => sum + group.length,
      0,
    )

    const assignmentDetails = Object.keys(groupsByIssueType)
      .map((issueType: string) => `グループ${issueType}: ${groupsByIssueType[parseInt(issueType)].length}件`)
      .join(', ')

    ElMessage.success(
      `発行区分に基づいて${totalAssigned}件の納入先を自動分配しました (${assignmentDetails})`,
    )
  } catch (error) {
    console.error('自动分配失败:', error)
    ElMessage.error('自動分配に失敗しました')
  } finally {
    autoAssignLoading.value = false
  }
}

// 保存所有分组
async function saveAllGroups() {
  try {
    saveLoading.value = true

    // 批量更新所有分组
    const groupsData = groups.value.map((group) => ({
      id: group.id,
      groupName: group.groupName,
      destinations: group.destinations.map((dest: Destination) => ({
        value: dest.value,
        label: dest.label || dest.value
      })),
    }))

    const response = await request.put(`/api/shipping/destination-groups/page/${props.pageKey}`, {
      groups: groupsData,
    }) as { success?: boolean } | undefined

    if (response && response.success) {
      ElMessage.success('すべてのグループが保存されました')
      emit('groupsUpdated', groups.value)
    } else {
      ElMessage.error('グループの保存に失敗しました')
    }
  } catch (error) {
    console.error('保存分组失败:', error)
    ElMessage.error('グループの保存に失敗しました')
  } finally {
    saveLoading.value = false
  }
}

// 将納入先加入指定分组（同一納入先可存在于多个グループ，不再从其他组移除）
function addDestinationToGroup(groupIndex: number, destination: Destination) {
  if (groupIndex < 0 || groupIndex >= groups.value.length) return
  const group = groups.value[groupIndex]
  const isAlreadyInGroup = group.destinations.some((dest) => dest.value === destination.value)
  if (!isAlreadyInGroup) {
    group.destinations.push({ ...destination })
  }
}

// 拖拽开始
function handleDragStart(event: DragEvent) {
  const target = event.target as HTMLElement
  const destinationData = target.dataset.destination
  if (event.dataTransfer && destinationData) {
    event.dataTransfer.setData('text/plain', destinationData)
    event.dataTransfer.effectAllowed = 'move'
  }
}

// 拖拽悬停
function handleDragOver(event: DragEvent) {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

// 拖拽进入
function handleDragEnter(event: DragEvent) {
  event.preventDefault()
  const target = event.currentTarget as HTMLElement
  target.classList.add('drag-over')
}

// 拖拽离开
function handleDragLeave(event: DragEvent) {
  const target = event.currentTarget as HTMLElement
  target.classList.remove('drag-over')
}

// 拖拽放下
function handleDrop(event: DragEvent, groupIndex: number) {
  event.preventDefault()
  const target = event.currentTarget as HTMLElement
  target.classList.remove('drag-over')

  try {
    const destinationData = event.dataTransfer?.getData('text/plain')
    if (!destinationData) return
    const destination: Destination = JSON.parse(destinationData)
    addDestinationToGroup(groupIndex, destination)
  } catch (error) {
    console.error('拖拽处理失败:', error)
  }
}

// 清除所有 drop 区域的高亮（触摸拖拽用）
function clearTouchDragOver() {
  document.querySelectorAll('.group-container.drag-over').forEach((el) => el.classList.remove('drag-over'))
}

// 触摸：长按开始拖拽
function handleTouchStart(event: TouchEvent, destination: Destination) {
  if (event.touches.length !== 1) return
  const touch = event.touches[0]
  const startX = touch.clientX
  const startY = touch.clientY

  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }

  longPressTimer.value = setTimeout(() => {
    longPressTimer.value = null
    touchDragPayload.value = destination
    touchGhostX.value = startX
    touchGhostY.value = startY
    touchDragActive.value = true

    touchMoveHandler = (e: TouchEvent) => {
      if (!touchDragActive.value || e.touches.length !== 1) return
      e.preventDefault()
      const t = e.touches[0]
      touchGhostX.value = t.clientX
      touchGhostY.value = t.clientY
      clearTouchDragOver()
      const under = document.elementFromPoint(t.clientX, t.clientY)
      const container = under?.closest('.group-container')
      if (container) container.classList.add('drag-over')
    }

    touchEndHandler = (e: TouchEvent) => {
      if (!touchDragActive.value) return
      e.preventDefault()
      touchDragActive.value = false
      clearTouchDragOver()
      const under = document.elementFromPoint(touchGhostX.value, touchGhostY.value)
      const container = under?.closest('.group-container')
      const groupIndexStr = container?.getAttribute('data-group-index')
      if (groupIndexStr != null && touchDragPayload.value) {
        const groupIndex = parseInt(groupIndexStr, 10)
        if (!Number.isNaN(groupIndex)) addDestinationToGroup(groupIndex, touchDragPayload.value)
      }
      touchDragPayload.value = null
      removeTouchListeners()
    }

    touchCancelHandler = () => {
      touchDragActive.value = false
      touchDragPayload.value = null
      clearTouchDragOver()
      removeTouchListeners()
    }

    document.addEventListener('touchmove', touchMoveHandler, { passive: false })
    document.addEventListener('touchend', touchEndHandler, { passive: false })
    document.addEventListener('touchcancel', touchCancelHandler, { passive: false })
  }, 400)
}

function removeTouchListeners() {
  if (touchMoveHandler) {
    document.removeEventListener('touchmove', touchMoveHandler)
    touchMoveHandler = null
  }
  if (touchEndHandler) {
    document.removeEventListener('touchend', touchEndHandler)
    touchEndHandler = null
  }
  if (touchCancelHandler) {
    document.removeEventListener('touchcancel', touchCancelHandler)
    touchCancelHandler = null
  }
}

function handleTouchCancel() {
  if (longPressTimer.value) {
    clearTimeout(longPressTimer.value)
    longPressTimer.value = null
  }
  if (touchDragActive.value) {
    touchDragActive.value = false
    touchDragPayload.value = null
    clearTouchDragOver()
    removeTouchListeners()
  }
}

// 从分组中移除纳入先
function removeFromGroup(groupIndex: number, destination: Destination) {
  groups.value[groupIndex].destinations = groups.value[groupIndex].destinations.filter(
    (dest) => dest.value !== destination.value,
  )
}

// 获取分组标签类型
function getGroupTagType(groupIndex: number): 'success' | 'warning' | 'danger' | 'info' | 'primary' {
  const types: ('success' | 'warning' | 'danger' | 'info' | 'primary')[] = ['success', 'warning', 'danger', 'info', 'primary']
  return types[groupIndex % types.length]
}

// 关闭弹窗
function handleClose() {
  visible.value = false
}

// 保存并关闭
async function saveAndClose() {
  await saveAllGroups()
  handleClose()
}

// 暴露方法给父组件
defineExpose({
  getGroups: () => groups.value,
  loadGroups,
})
</script>

<style scoped>
.destination-group-dialog :deep(.el-dialog) {
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.12), 0 4px 12px rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.destination-group-dialog :deep(.el-dialog__header) {
  padding: 10px 14px;
  background: linear-gradient(135deg, #1e40af 0%, #2563eb 50%, #3b82f6 100%);
  color: #fff;
  border-bottom: none;
}

.destination-group-dialog :deep(.el-dialog__title) {
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  letter-spacing: 0.02em;
}

.destination-group-dialog :deep(.el-dialog__headerbtn) {
  width: 32px;
  height: 32px;
  top: 50%;
  transform: translateY(-50%);
}

.destination-group-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: rgba(255, 255, 255, 0.9);
}

.destination-group-dialog :deep(.el-dialog__headerbtn:hover .el-dialog__close) {
  color: #fff;
}

.destination-group-dialog :deep(.el-dialog__body) {
  padding: 10px 14px 12px;
  --el-dialog-content-font-size: 13px;
}

.group-manager {
  min-height: 320px;
}

.section-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 6px;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #334155;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.section-title .el-icon {
  font-size: 14px;
  color: #2563eb;
}

.section-hint {
  margin-left: 8px;
  font-size: 12px;
  color: #64748b;
  font-weight: normal;
}

/* 利用可能な納入先 - 紧凑 */
.destinations-section {
  margin-bottom: 10px;
  padding: 8px 10px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.destinations-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  min-height: 40px;
  align-items: center;
}

.destination-tag {
  cursor: move;
  user-select: none;
}

.destination-tag:hover {
  transform: translateY(-1px);
  transition: transform 0.15s ease;
}

.draggable-tag {
  cursor: move;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 6px;
  font-weight: 500;
}

/* グループ管理 */
.groups-section {
  margin-bottom: 10px;
}

.groups-header .btn-create {
  padding: 5px 10px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
}

.groups-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 8px;
}

.group-container {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  min-height: 180px;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}

.group-container:hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
}

.group-container.drag-over {
  border-color: #2563eb;
  background: linear-gradient(180deg, #eff6ff 0%, #dbeafe 100%);
  transform: scale(1.02);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.18);
}

.group-1 { border-left: 3px solid #059669; }
.group-2 { border-left: 3px solid #d97706; }
.group-3 { border-left: 3px solid #dc2626; }

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  border-radius: 8px 8px 0 0;
}

.group-title {
  flex: 1;
  min-width: 0;
}

.group-title .group-name-input :deep(.el-input__wrapper) {
  padding: 2px 8px;
  min-height: 26px;
  border-radius: 4px;
}

.group-title h4 {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
}

.group-title h4 .el-icon {
  font-size: 13px;
  color: #2563eb;
  flex-shrink: 0;
}

.group-title h4:hover {
  color: #1d4ed8;
}

.group-badge {
  margin-left: 4px;
}

.group-badge :deep(.el-badge__content) {
  font-size: 10px;
  height: 16px;
  line-height: 16px;
  padding: 0 5px;
}

.group-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.group-actions .btn-icon {
  padding: 4px;
  font-size: 12px;
}

.group-content {
  padding: 8px;
  min-height: 140px;
  max-height: 220px;
  overflow-y: auto;
}

.group-item {
  margin-bottom: 3px;
}

.group-item .el-tag {
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 5px;
}

.empty-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #94a3b8;
  font-size: 11px;
}

.empty-group .el-icon {
  font-size: 20px;
  margin-bottom: 4px;
  color: #cbd5e1;
}

.empty-group .touch-hint {
  display: block;
  margin-top: 2px;
  font-size: 10px;
  color: #94a3b8;
}

/* 操作按钮 - 紧凑 */
.actions-section {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 8px 0 0;
  border-top: 1px solid #e2e8f0;
  margin-top: 2px;
}

.actions-section .btn-action {
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 6px;
  transition: transform 0.15s, box-shadow 0.15s;
}

.actions-section .btn-save {
  box-shadow: 0 1px 3px rgba(37, 99, 235, 0.25);
}

.actions-section .btn-action:hover {
  transform: translateY(-1px);
}

/* 内层对话框 */
.destination-group-dialog :deep(.el-dialog__body .el-dialog__body) {
  padding: 12px;
}

.dialog-footer {
  display: flex;
  gap: 8px;
}

.dialog-footer .el-button {
  padding: 6px 14px;
  font-size: 12px;
  border-radius: 6px;
  font-weight: 500;
}

/* 滚动条 */
.group-content::-webkit-scrollbar {
  width: 5px;
}

.group-content::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 3px;
}

.group-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.group-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 响应式 */
@media (max-width: 900px) {
  .destination-group-dialog :deep(.el-dialog) {
    width: 92% !important;
    margin: 4vh auto;
  }

  .groups-container {
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  }
}

@media (max-width: 768px) {
  .destination-group-dialog :deep(.el-dialog) {
    width: 96% !important;
    max-width: 100%;
  }

  .destination-group-dialog :deep(.el-dialog__body) {
    padding: 8px 10px 10px;
  }

  .group-manager {
    min-height: 280px;
  }

  .destinations-section {
    padding: 6px 8px;
    margin-bottom: 8px;
  }

  .destinations-container {
    min-height: 36px;
  }

  .groups-container {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .group-container {
    min-height: 160px;
  }

  .group-content {
    min-height: 120px;
    max-height: 180px;
  }

  .empty-group {
    height: 80px;
  }

  .section-row.groups-header {
    flex-direction: column;
    align-items: stretch;
  }

  .groups-header .btn-create {
    align-self: flex-end;
  }
}

@media (max-width: 480px) {
  .destination-group-dialog :deep(.el-dialog__header) {
    padding: 8px 12px;
  }

  .destination-group-dialog :deep(.el-dialog__title) {
    font-size: 14px;
  }

  .group-header {
    padding: 5px 8px;
  }

  .group-title h4 {
    font-size: 11px;
  }

  .actions-section {
    flex-wrap: wrap;
    justify-content: center;
    padding: 6px 0 0;
  }

  .actions-section .btn-action {
    flex: 1;
    min-width: 120px;
  }
}
</style>

<!-- 触摸拖拽幽灵在 body 下，需全局样式 -->
<style>
.touch-drag-ghost {
  position: fixed;
  z-index: 9999;
  pointer-events: none;
  transform: translate(-50%, -50%);
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.2));
}
.touch-drag-ghost .draggable-tag {
  white-space: nowrap;
}
</style>
