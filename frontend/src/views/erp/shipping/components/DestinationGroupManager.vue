<template>
  <el-dialog v-model="visible" title="納入先グループ管理" width="58%" :close-on-click-modal="false"
    class="destination-group-dialog" @close="handleClose">
    <div class="group-manager">
      <!-- 顶部纳入先标签区域 -->
      <div class="destinations-section">
        <h3 class="section-title">
          <el-icon>
            <Collection />
          </el-icon>
          利用可能な納入先
        </h3>
        <div class="destinations-container">
          <div v-for="destination in availableDestinations" :key="destination.value"
            :data-destination="JSON.stringify(destination)" class="destination-tag" draggable="true"
            @dragstart="handleDragStart">
            <el-tag size="default" type="info" class="draggable-tag">
              {{ destination.label }}
            </el-tag>
          </div>
        </div>
      </div>

      <!-- 分组管理区域 -->
      <div class="groups-section">
        <div class="groups-header">
          <h3 class="section-title">
            <el-icon>
              <Box />
            </el-icon>
            グループ管理
          </h3>
          <el-button type="primary" @click="showCreateGroupDialog">
            <el-icon>
              <Plus />
            </el-icon>
            新規グループ作成
          </el-button>
        </div>

        <div class="groups-container">
          <div v-for="(group, index) in groups" :key="group.id || index"
            :class="['group-container', `group-${(index % 3) + 1}`]" @drop="handleDrop($event, index)"
            @dragover="handleDragOver" @dragenter="handleDragEnter" @dragleave="handleDragLeave">
            <div class="group-header">
              <div class="group-title">
                <el-input v-if="group.editing" v-model="group.groupName" size="small" @blur="saveGroupName(group)"
                  @keyup.enter="saveGroupName(group)" ref="groupNameInput" />
                <h4 v-else @dblclick="editGroupName(group)">
                  <el-icon>
                    <Box />
                  </el-icon>
                  {{ group.groupName }}
                  <el-badge :value="group.destinations.length" type="primary" />
                </h4>
              </div>
              <div class="group-actions">
                <el-button size="small" type="primary" text @click="editGroupName(group)" title="グループ名編集">
                  <el-icon>
                    <Edit />
                  </el-icon>
                </el-button>
                <el-button size="small" type="warning" text @click="clearGroup(index)"
                  :disabled="group.destinations.length === 0" title="グループクリア">
                  <el-icon>
                    <Delete />
                  </el-icon>
                </el-button>
                <el-button size="small" type="danger" text @click="deleteGroup(group, index)" title="グループ削除">
                  <el-icon>
                    <Close />
                  </el-icon>
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
                <el-icon>
                  <Plus />
                </el-icon>
                <span>ここに納入先をドラッグ</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions-section">
        <el-button @click="autoAssignByIssueType" :loading="autoAssignLoading">
          <el-icon>
            <Star />
          </el-icon>
          一键分配（按発行区分）
        </el-button>
        <el-button type="primary" @click="saveAndClose" :loading="saveLoading">
          <el-icon>
            <Check />
          </el-icon>
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

  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
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

// 新建分组表单
const newGroupForm = reactive({
  groupName: '',
})

// 计算可用的纳入先（未分组的）
const availableDestinations = computed(() => {
  const assignedValues = new Set()
  groups.value.forEach((group) => {
    group.destinations.forEach((dest) => {
      assignedValues.add(dest.value)
    })
  })

  return allDestinations.value.filter((dest) => !assignedValues.has(dest.value))
})

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

    // 检查是否已经在该分组中
    const isAlreadyInGroup = groups.value[groupIndex].destinations.some(
      (dest) => dest.value === destination.value,
    )

    if (!isAlreadyInGroup) {
      // 从其他分组中移除（如果存在）
      groups.value.forEach((group) => {
        group.destinations = group.destinations.filter((dest) => dest.value !== destination.value)
      })

      // 添加到目标分组
      groups.value[groupIndex].destinations.push(destination)
    }
  } catch (error) {
    console.error('拖拽处理失败:', error)
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
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.destination-group-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
  color: white;
  padding: 12px 16px;
  border-radius: 8px 8px 0 0;
}

.destination-group-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
  font-size: 16px;
}

.destination-group-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

.destination-group-dialog :deep(.el-dialog__body) {
  padding: 12px;
}

.destination-group-dialog {
  --el-dialog-content-font-size: 13px;
}

.group-manager {
  min-height: 500px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  color: #374151;
  font-size: 14px;
  font-weight: 600;
}

.section-title .el-icon {
  font-size: 16px;
  color: #2563eb;
}

/* 纳入先标签区域 */
.destinations-section {
  margin-bottom: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #e5e7eb;
}

.destinations-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  min-height: 60px;
}

.destination-tag {
  cursor: move;
  user-select: none;
}

.destination-tag:hover {
  transform: translateY(-1px);
  transition: transform 0.2s ease;
}

.draggable-tag {
  cursor: move;
  font-size: 12px;
  padding: 4px 10px;
}

/* 分组区域 */
.groups-section {
  margin-bottom: 16px;
}

.groups-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.groups-header .el-button {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 6px;
  font-weight: 500;
}

.groups-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.group-container {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  min-height: 250px;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.group-container.drag-over {
  border-color: #2563eb;
  background: #eff6ff;
  transform: scale(1.01);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.2);
}

.group-1 {
  border-left: 3px solid #10b981;
}

.group-2 {
  border-left: 3px solid #f59e0b;
}

.group-3 {
  border-left: 3px solid #ef4444;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  border-radius: 6px 6px 0 0;
}

.group-title {
  flex: 1;
  min-width: 0;
}

.group-title h4 {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
}

.group-title h4 .el-icon {
  font-size: 14px;
  color: #2563eb;
}

.group-title h4:hover {
  color: #2563eb;
}

.group-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.group-actions .el-button {
  padding: 4px 6px;
  font-size: 12px;
}

.group-content {
  padding: 10px;
  min-height: 200px;
  max-height: 300px;
  overflow-y: auto;
}

.group-item {
  margin-bottom: 6px;
}

.group-item .el-tag {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.empty-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: #9ca3af;
  font-size: 12px;
}

.empty-group .el-icon {
  font-size: 24px;
  margin-bottom: 6px;
  color: #d1d5db;
}

/* 操作按钮区域 */
.actions-section {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 12px 0;
  border-top: 1px solid #e5e7eb;
}

.actions-section .el-button {
  padding: 8px 16px;
  font-weight: 500;
  font-size: 13px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.actions-section .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

/* 对话框底部 */
.dialog-footer {
  display: flex;
  gap: 8px;
}

.dialog-footer .el-button {
  padding: 8px 16px;
  font-size: 13px;
  border-radius: 6px;
  font-weight: 500;
}

/* 创建分组对话框 */
.destination-group-dialog :deep(.el-dialog__body .el-dialog__body) {
  padding: 16px;
}

/* 滚动条美化 */
.group-content::-webkit-scrollbar {
  width: 6px;
}

.group-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.group-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.group-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .destinations-container {
    justify-content: center;
  }

  .groups-container {
    grid-template-columns: 1fr;
  }

  .group-container {
    margin-bottom: 12px;
  }

  .groups-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
