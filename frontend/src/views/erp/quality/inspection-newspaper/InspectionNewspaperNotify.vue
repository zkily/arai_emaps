<template>
  <div class="inn-page">
    <div class="inn-header">
      <div class="inn-header-glow" aria-hidden="true" />
      <div class="inn-header-left">
        <div class="inn-title-icon">
          <el-icon :size="22"><Bell /></el-icon>
        </div>
        <div>
          <h1 class="inn-title">検査通知(防錆)</h1>
          <p class="inn-subtitle">
            切断実績確定後、対象製品があれば検査工程へ「新聞紙を入れる」メールを自動送信します
          </p>
        </div>
      </div>
      <div class="inn-header-stats">
        <div class="inn-stat inn-stat--product">
          <div class="inn-stat-icon"><el-icon><Goods /></el-icon></div>
          <div class="inn-stat-body">
            <span class="inn-stat-value">{{ targetProducts.length }}</span>
            <span class="inn-stat-label">対象製品</span>
          </div>
        </div>
        <div class="inn-stat inn-stat--mail">
          <div class="inn-stat-icon"><el-icon><Message /></el-icon></div>
          <div class="inn-stat-body">
            <span class="inn-stat-value">{{ activeRecipients.length }}</span>
            <span class="inn-stat-label">受信者</span>
          </div>
        </div>
        <div class="inn-auto-pill" :class="{ 'is-on': autoSendEnabled }">
          <span class="inn-auto-dot" />
          <span class="inn-switch-label">自動送信</span>
          <el-switch
            v-model="autoSendEnabled"
            :loading="settingSaving"
            :disabled="!canEdit"
            inline-prompt
            active-text="ON"
            inactive-text="OFF"
            @change="onAutoSendChange"
          />
        </div>
      </div>
    </div>

    <el-row :gutter="14" class="inn-row inn-row--delay-1">
      <el-col :xs="24" :lg="12">
        <section v-loading="productsLoading" class="inn-panel inn-panel--product">
          <header class="inn-panel-head">
            <div class="inn-panel-title">
              <span class="inn-panel-badge"><el-icon><Goods /></el-icon></span>
              <div>
                <h2>対象製品</h2>
                <p>製品名順で表示。切断確定分に含まれると通知されます</p>
              </div>
            </div>
            <div class="inn-head-tools">
              <el-button
                class="inn-btn inn-btn--pdf"
                size="small"
                :loading="productPdfExporting"
                :disabled="productsLoading || targetProducts.length === 0"
                @click="exportProductsPdf"
              >
                <el-icon><Download /></el-icon>
                PDF出力
              </el-button>
              <el-tag type="success" effect="dark" round size="small">{{ targetProducts.length }} 件</el-tag>
            </div>
          </header>
          <div class="inn-panel-body">
            <div class="inn-add-row">
              <el-select
                v-model="productToAdd"
                filterable
                clearable
                placeholder="製品を選択（製品CD・製品名で検索）"
                class="inn-add-select"
                :loading="productOptionsLoading"
              >
                <el-option
                  v-for="p in availableProductOptions"
                  :key="p.product_cd"
                  :label="`${p.product_cd} ${p.product_name}`"
                  :value="p.product_cd"
                />
              </el-select>
              <el-button
                type="primary"
                class="inn-btn inn-btn--product"
                :loading="productSaving"
                :disabled="!productToAdd"
                @click="addProduct"
              >
                <el-icon><Plus /></el-icon>
                追加
              </el-button>
            </div>
            <el-table
              :data="sortedTargetProducts"
              stripe
              size="small"
              max-height="320"
              class="inn-table"
              empty-text="対象製品はまだありません"
            >
              <el-table-column prop="product_cd" label="製品CD" width="130">
                <template #default="{ row }">
                  <span class="inn-code">{{ row.product_cd }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="product_name" label="製品名" min-width="140">
                <template #default="{ row }">{{ row.product_name || '—' }}</template>
              </el-table-column>
              <el-table-column prop="updated_by" label="更新者" width="100">
                <template #default="{ row }">{{ row.updated_by || '—' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button
                    link
                    type="danger"
                    size="small"
                    @click="() => deleteProduct(row as InspectionNewspaperProduct)"
                  >
                    削除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </section>
      </el-col>

      <el-col :xs="24" :lg="12">
        <section v-loading="recipientsLoading" class="inn-panel inn-panel--mail">
          <header class="inn-panel-head">
            <div class="inn-panel-title">
              <span class="inn-panel-badge"><el-icon><Message /></el-icon></span>
              <div>
                <h2>メール受信者</h2>
                <p>通知メールの送信先です（全製品共通）</p>
              </div>
            </div>
            <el-button
              v-if="isAdmin"
              type="primary"
              class="inn-btn inn-btn--mail"
              size="small"
              @click="openRecipientAdd"
            >
              <el-icon><Plus /></el-icon>
              追加
            </el-button>
          </header>
          <div class="inn-panel-body">
            <el-table
              :data="activeRecipients"
              stripe
              size="small"
              max-height="360"
              class="inn-table"
              empty-text="受信者が登録されていません"
            >
              <el-table-column label="種別" width="100">
                <template #default="{ row }">
                  <el-tag
                    size="small"
                    effect="light"
                    :type="(row as NotificationRecipientItem).recipient_type === 'user' ? 'primary' : 'warning'"
                    round
                  >
                    {{ recipientTypeLabel(row as NotificationRecipientItem) }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="受信者" min-width="180">
                <template #default="{ row }">
                  {{ recipientLabel(row as NotificationRecipientItem) }}
                </template>
              </el-table-column>
              <el-table-column v-if="isAdmin" label="操作" width="80" align="center">
                <template #default="{ row }">
                  <el-button
                    link
                    type="danger"
                    size="small"
                    @click="() => deleteRecipient(row as NotificationRecipientItem)"
                  >
                    削除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <p v-if="!isAdmin" class="inn-readonly-hint">
              受信者の変更は管理者のみ可能です。通知センターでも設定できます。
            </p>
          </div>
        </section>
      </el-col>
    </el-row>

    <section v-loading="previewLoading" class="inn-panel inn-panel--preview inn-row--delay-2">
      <header class="inn-panel-head">
        <div class="inn-panel-title">
          <span class="inn-panel-badge"><el-icon><Promotion /></el-icon></span>
          <div>
            <h2>送信プレビュー・手動送信</h2>
            <p>管理コード前13桁でバッチを識別し、計画数を当日初回検知時に送信します</p>
          </div>
        </div>
        <div class="inn-preview-actions">
          <el-date-picker
            v-model="previewDay"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="生産日"
            :clearable="false"
            class="inn-date"
          />
          <el-button
            type="primary"
            class="inn-btn inn-btn--preview"
            :loading="previewLoading"
            @click="loadPreview"
          >
            <el-icon><View /></el-icon>
            プレビュー
          </el-button>
          <el-button
            type="warning"
            class="inn-btn inn-btn--send"
            :loading="sending"
            :disabled="
              previewLoading ||
              !preview ||
              preview.matched_count === 0 ||
              preview.production_day !== previewDay
            "
            @click="sendManually"
          >
            <el-icon><Promotion /></el-icon>
            送信
          </el-button>
        </div>
      </header>

      <div class="inn-panel-body">
        <template v-if="preview">
          <div v-if="previewStatus" class="inn-banner" :class="`inn-banner--${previewStatus.tone}`">
            <el-icon>
              <Warning v-if="previewStatus.tone === 'warn'" />
              <CircleCheck v-else />
            </el-icon>
            <span>{{ previewStatus.text }}</span>
          </div>

          <div class="inn-metrics">
            <div class="inn-metric inn-metric--teal">
              <span class="inn-metric-label">対象製品</span>
              <strong class="inn-metric-value">{{ preview.product_count }}<small>品目</small></strong>
            </div>
            <div class="inn-metric inn-metric--indigo">
              <span class="inn-metric-label">バッチ</span>
              <strong class="inn-metric-value">{{ preview.matched_count }}<small>件</small></strong>
            </div>
            <div class="inn-metric inn-metric--amber">
              <span class="inn-metric-label">計画数合計</span>
              <strong class="inn-metric-value">
                {{ preview.total_quantity.toLocaleString() }}<small>本</small>
              </strong>
            </div>
            <div class="inn-metric inn-metric--slate">
              <span class="inn-metric-label">受信者</span>
              <strong class="inn-metric-value inn-metric-value--sm">
                {{
                  preview.recipient_count
                    ? preview.recipients.map((r) => r.name || r.email).join('、')
                    : '未設定'
                }}
              </strong>
            </div>
          </div>

          <el-table
            v-if="preview.matched_rows.length"
            :data="preview.matched_rows"
            stripe
            size="small"
            max-height="280"
            class="inn-table"
          >
            <el-table-column prop="product_cd" label="製品CD" width="130">
              <template #default="{ row }">
                <span class="inn-code">{{ row.product_cd }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="product_name" label="製品名" min-width="140" />
            <el-table-column prop="batch_key" label="管理コード(前13桁)" width="160">
              <template #default="{ row }">
                <span class="inn-code">{{ row.batch_key || '—' }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="cutting_machine" label="切断機" width="140">
              <template #default="{ row }">{{ row.cutting_machine || '—' }}</template>
            </el-table-column>
            <el-table-column label="計画数" width="120" align="right">
              <template #default="{ row }">
                <span class="inn-qty">{{ Number(row.quantity || 0).toLocaleString() }} 本</span>
              </template>
            </el-table-column>
            <el-table-column label="状態" width="110" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.already_sent ? 'success' : row.delivered_count ? 'info' : 'warning'"
                  size="small"
                  effect="dark"
                  round
                >
                  {{ row.already_sent ? '送信済' : row.delivered_count ? '一部未着' : '初回検知' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
          <el-empty
            v-else
            description="この生産日に確定済みの対象製品はありません"
            :image-size="64"
          />
        </template>
        <el-empty v-else description="生産日を指定して「プレビュー」を押してください" :image-size="64" />
      </div>
    </section>

    <section v-loading="historyLoading" class="inn-panel inn-panel--history inn-row--delay-3">
      <header class="inn-panel-head">
        <div class="inn-panel-title">
          <span class="inn-panel-badge"><el-icon><Clock /></el-icon></span>
          <div>
            <h2>送信履歴</h2>
            <p>直近の自動・手動送信ログです</p>
          </div>
        </div>
        <el-button class="inn-btn inn-btn--ghost" size="small" @click="loadHistory">
          <el-icon><Refresh /></el-icon>
          更新
        </el-button>
      </header>
      <div class="inn-panel-body">
        <el-table
          :data="history"
          stripe
          size="small"
          max-height="300"
          class="inn-table"
          empty-text="送信履歴はありません"
        >
          <el-table-column prop="sent_at" label="送信日時" width="160">
            <template #default="{ row }">{{ row.sent_at || '—' }}</template>
          </el-table-column>
          <el-table-column prop="reference_key" label="対象" width="220" />
          <el-table-column prop="recipient_email" label="送信先" min-width="180" />
          <el-table-column label="結果" width="100" align="center">
            <template #default="{ row }">
              <el-tag
                :type="row.status === 'success' ? 'success' : 'danger'"
                size="small"
                effect="dark"
                round
              >
                {{ row.status === 'success' ? '成功' : '失敗' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="error_message" label="エラー" min-width="160">
            <template #default="{ row }">{{ row.error_message || '—' }}</template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <el-dialog
      v-model="recipientFormVisible"
      width="480px"
      destroy-on-close
      align-center
      class="inn-dialog"
    >
      <template #header>
        <div class="inn-dialog-head">
          <span class="inn-panel-badge inn-panel-badge--mail"><el-icon><User /></el-icon></span>
          <div>
            <h3>受信者追加</h3>
            <p>メール通知の送信先を登録します</p>
          </div>
        </div>
      </template>
      <el-form label-width="96px" size="default">
        <el-form-item label="種別">
          <el-radio-group v-model="recipientForm.recipient_type">
            <el-radio-button value="user">ユーザー</el-radio-button>
            <el-radio-button value="email">メール</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="recipientForm.recipient_type === 'user'" label="ユーザー">
          <el-select v-model="recipientForm.user_id" filterable placeholder="選択" style="width: 100%">
            <el-option
              v-for="u in users"
              :key="u.id"
              :label="`${u.full_name || u.username} (${u.email || 'メール未設定'})`"
              :value="u.id"
              :disabled="!u.email"
            />
          </el-select>
        </el-form-item>
        <template v-else>
          <el-form-item label="メール">
            <el-input v-model="recipientForm.email" placeholder="example@example.com" />
          </el-form-item>
          <el-form-item label="表示名">
            <el-input v-model="recipientForm.display_name" placeholder="任意" />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="recipientFormVisible = false">キャンセル</el-button>
        <el-button
          type="primary"
          class="inn-btn inn-btn--mail"
          :loading="recipientSaving"
          @click="submitRecipient"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bell, CircleCheck, Clock, Download, Goods, Message, Plus, Promotion, Refresh, User, View, Warning } from '@element-plus/icons-vue'
import { exportInspectionNewspaperProductsPdf } from './exportTargetProductsPdf'
import { useUserStore } from '@/modules/auth/stores/user'
import { isAdminUser } from '@/utils/menuPermissions'
import { useQualityOperationPermission } from '@/composables/useQualityOperationPermission'
import { guardQualityOperation } from '@/utils/qualityOperationGuard'
import { getProductList } from '@/api/master/productMaster'
import type { Product } from '@/types/master'
import {
  createNotificationRecipient,
  deleteNotificationRecipient,
  getNotificationRecipients,
  getUsers,
  type NotificationRecipientItem,
  type UserListItem,
} from '@/api/system'
import {
  INSPECTION_NEWSPAPER_EVENT,
  addInspectionNewspaperProduct,
  deleteInspectionNewspaperProduct,
  getInspectionNewspaperHistory,
  getInspectionNewspaperPreview,
  getInspectionNewspaperProducts,
  getInspectionNewspaperSetting,
  sendInspectionNewspaperNotification,
  updateInspectionNewspaperSetting,
  type InspectionNewspaperHistoryItem,
  type InspectionNewspaperPreview,
  type InspectionNewspaperProduct,
} from '@/api/erp/quality/inspectionNewspaper'

const userStore = useUserStore()
const isAdmin = computed(() => isAdminUser(userStore.user))
const { canCreate, canEdit, canDelete } = useQualityOperationPermission()

// ===== 通知設定（自動送信 ON/OFF） =====
const autoSendEnabled = ref(false)
const settingSaving = ref(false)

async function loadSetting() {
  try {
    const res = await getInspectionNewspaperSetting()
    autoSendEnabled.value = !!(res.data?.is_active && res.data?.email_enabled)
  } catch (e: any) {
    console.error('検査通知(防錆)設定の取得に失敗:', e)
    ElMessage.error(e?.response?.data?.detail || '通知設定の取得に失敗しました')
  }
}

async function onAutoSendChange(value: string | number | boolean) {
  const enabled = !!value
  if (!guardQualityOperation(canEdit)) {
    autoSendEnabled.value = !enabled
    return
  }
  settingSaving.value = true
  try {
    await updateInspectionNewspaperSetting({ is_active: enabled, email_enabled: enabled })
    ElMessage.success(enabled ? '自動送信を有効にしました' : '自動送信を無効にしました')
  } catch (e: any) {
    autoSendEnabled.value = !enabled
    ElMessage.error(e?.response?.data?.detail || '通知設定の更新に失敗しました')
  } finally {
    settingSaving.value = false
  }
}

// ===== 対象製品 =====
const productsLoading = ref(false)
const productSaving = ref(false)
const productPdfExporting = ref(false)
const targetProducts = ref<InspectionNewspaperProduct[]>([])
const productToAdd = ref('')
const productOptions = ref<Product[]>([])
const productOptionsLoading = ref(false)

function compareByProductName(
  a: { product_name?: string | null; product_cd?: string | null },
  b: { product_name?: string | null; product_cd?: string | null },
) {
  const nameA = (a.product_name || '').trim()
  const nameB = (b.product_name || '').trim()
  if (!nameA && nameB) return 1
  if (nameA && !nameB) return -1
  const byName = nameA.localeCompare(nameB, 'ja')
  if (byName !== 0) return byName
  return (a.product_cd || '').localeCompare(b.product_cd || '', 'ja')
}

const sortedTargetProducts = computed(() =>
  [...targetProducts.value].sort(compareByProductName),
)

const availableProductOptions = computed(() => {
  const registered = new Set(targetProducts.value.map((p) => p.product_cd))
  const seen = new Set<string>()
  return productOptions.value.filter((p) => {
    const cd = (p.product_cd || '').trim()
    if (!cd || registered.has(cd) || seen.has(cd)) return false
    seen.add(cd)
    return true
  })
})

async function loadProducts() {
  productsLoading.value = true
  try {
    const res = await getInspectionNewspaperProducts()
    targetProducts.value = res.data?.list ?? []
  } catch (e: any) {
    console.error('対象製品の取得に失敗:', e)
    ElMessage.error(e?.response?.data?.detail || '対象製品の取得に失敗しました')
  } finally {
    productsLoading.value = false
  }
}

async function loadProductOptions() {
  productOptionsLoading.value = true
  try {
    const res = await getProductList({ page: 1, pageSize: 5000, status: 'active' })
    productOptions.value = res.data?.list ?? res.list ?? []
  } catch (e) {
    console.error('製品一覧の取得に失敗:', e)
    productOptions.value = []
  } finally {
    productOptionsLoading.value = false
  }
}

async function addProduct() {
  if (!guardQualityOperation(canCreate)) return
  const productCd = productToAdd.value.trim()
  if (!productCd) return
  const product = productOptions.value.find((p) => p.product_cd === productCd)
  productSaving.value = true
  try {
    await addInspectionNewspaperProduct({
      product_cd: productCd,
      product_name: product?.product_name ?? null,
    })
    productToAdd.value = ''
    await loadProducts()
    await loadPreview()
    ElMessage.success('追加しました')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '追加に失敗しました')
  } finally {
    productSaving.value = false
  }
}

async function exportProductsPdf() {
  if (!targetProducts.value.length) {
    ElMessage.warning('対象製品がありません')
    return
  }
  productPdfExporting.value = true
  try {
    await exportInspectionNewspaperProductsPdf(sortedTargetProducts.value)
    ElMessage.success('PDFを出力しました')
  } catch (e) {
    console.error('対象製品PDFの出力に失敗:', e)
    ElMessage.error('PDFの出力に失敗しました')
  } finally {
    productPdfExporting.value = false
  }
}

async function deleteProduct(item: InspectionNewspaperProduct) {
  if (!guardQualityOperation(canDelete)) return
  try {
    await ElMessageBox.confirm(`「${item.product_cd}」を削除しますか？`, '確認', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
    })
  } catch {
    return
  }
  try {
    await deleteInspectionNewspaperProduct(item.id)
    await loadProducts()
    await loadPreview()
    ElMessage.success('削除しました')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '削除に失敗しました')
  }
}

// ===== 受信者 =====
const recipientsLoading = ref(false)
const recipients = ref<NotificationRecipientItem[]>([])
const users = ref<UserListItem[]>([])

const activeRecipients = computed(() =>
  recipients.value.filter((r) => r.is_active && r.recipient_type !== 'line'),
)

const previewStatus = computed(() => {
  const p = preview.value
  if (!p) return null
  if (!p.enabled) {
    return { tone: 'warn', text: '通知が無効です。右上の自動送信スイッチを ON にしてください。' }
  }
  if (!p.smtp_configured) {
    return { tone: 'warn', text: 'SMTP が未設定です。通知センターで SMTP を設定してください。' }
  }
  if (p.recipient_count === 0) {
    return { tone: 'warn', text: '受信者が登録されていません。' }
  }
  if (p.already_sent) {
    return {
      tone: 'ok',
      text: `${p.production_day} の対象バッチはすべて送信済みです（「送信」で再送信できます）`,
    }
  }
  if ((p.pending_count ?? 0) > 0 && p.matched_count > p.pending_count) {
    return {
      tone: 'ok',
      text: `未送信 ${p.pending_count} 件を、まだ届いていない宛先だけに送れます`,
    }
  }
  if ((p.pending_count ?? 0) > 0) {
    return {
      tone: 'ok',
      text: `未送信 ${p.pending_count} 件があります。切断の実績確定後に自動送信されます`,
    }
  }
  return null
})

function recipientTypeLabel(r: NotificationRecipientItem) {
  if (r.recipient_type === 'user') return 'ユーザー'
  if (r.recipient_type === 'role') return 'ロール'
  return 'メール'
}

function recipientLabel(r: NotificationRecipientItem) {
  if (r.recipient_type === 'user' && r.user_id) {
    const u = users.value.find((x) => x.id === r.user_id)
    return u ? `${u.full_name || u.username} (${u.email})` : `user#${r.user_id}`
  }
  if (r.recipient_type === 'role') return `ロール: ${r.role}`
  return r.display_name ? `${r.display_name} (${r.email})` : r.email || '—'
}

async function loadRecipients() {
  recipientsLoading.value = true
  try {
    const [recs, userRes] = await Promise.all([
      getNotificationRecipients(INSPECTION_NEWSPAPER_EVENT),
      isAdmin.value
        ? getUsers({ page: 1, page_size: 500 })
        : Promise.resolve({ items: [] as UserListItem[] }),
    ])
    recipients.value = recs
    users.value = (userRes as { items?: UserListItem[] }).items || []
  } catch (e: any) {
    console.error('受信者の取得に失敗:', e)
    ElMessage.error(e?.response?.data?.detail || '受信者の取得に失敗しました')
  } finally {
    recipientsLoading.value = false
  }
}

const recipientFormVisible = ref(false)
const recipientSaving = ref(false)
const recipientForm = ref({
  recipient_type: 'user' as 'user' | 'email',
  user_id: null as number | null,
  email: '',
  display_name: '',
})

function openRecipientAdd() {
  recipientForm.value = { recipient_type: 'user', user_id: null, email: '', display_name: '' }
  recipientFormVisible.value = true
}

async function submitRecipient() {
  const form = recipientForm.value
  if (form.recipient_type === 'user' && !form.user_id) {
    ElMessage.warning('ユーザーを選択してください')
    return
  }
  if (form.recipient_type === 'email' && !form.email.trim()) {
    ElMessage.warning('メールアドレスを入力してください')
    return
  }
  recipientSaving.value = true
  try {
    await createNotificationRecipient({
      event_code: INSPECTION_NEWSPAPER_EVENT,
      recipient_type: form.recipient_type,
      user_id: form.recipient_type === 'user' ? form.user_id : null,
      email: form.recipient_type === 'email' ? form.email.trim() : null,
      display_name: form.display_name.trim() || null,
      is_active: true,
    })
    recipientFormVisible.value = false
    await loadRecipients()
    await loadPreview()
    ElMessage.success('受信者を追加しました')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '受信者の追加に失敗しました')
  } finally {
    recipientSaving.value = false
  }
}

async function deleteRecipient(row: NotificationRecipientItem) {
  try {
    await ElMessageBox.confirm(`「${recipientLabel(row)}」を削除しますか？`, '確認', {
      type: 'warning',
      confirmButtonText: '削除',
      cancelButtonText: 'キャンセル',
    })
  } catch {
    return
  }
  try {
    await deleteNotificationRecipient(row.id)
    await loadRecipients()
    await loadPreview()
    ElMessage.success('削除しました')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '削除に失敗しました')
  }
}

// ===== プレビュー・手動送信 =====
function todayStr() {
  const d = new Date()
  const m = `${d.getMonth() + 1}`.padStart(2, '0')
  const day = `${d.getDate()}`.padStart(2, '0')
  return `${d.getFullYear()}-${m}-${day}`
}

const previewDay = ref(todayStr())
const previewLoading = ref(false)
const preview = ref<InspectionNewspaperPreview | null>(null)
const sending = ref(false)
let previewSeq = 0

watch(previewDay, () => {
  void loadPreview()
})

async function loadPreview() {
  if (!previewDay.value) return
  const seq = ++previewSeq
  const day = previewDay.value
  previewLoading.value = true
  try {
    const res = await getInspectionNewspaperPreview(day)
    if (seq !== previewSeq || day !== previewDay.value) return
    preview.value = res
  } catch (e: any) {
    if (seq !== previewSeq) return
    ElMessage.error(e?.response?.data?.detail || 'プレビューの取得に失敗しました')
  } finally {
    if (seq === previewSeq) previewLoading.value = false
  }
}

async function sendManually() {
  if (!guardQualityOperation(canEdit)) return
  if (!preview.value) return
  const day = preview.value.production_day
  if (!day || day !== previewDay.value) {
    ElMessage.warning('生産日が変わっています。プレビューを更新してから送信してください')
    return
  }
  const force = preview.value.already_sent
  try {
    await ElMessageBox.confirm(
      force
        ? `${day} の対象バッチはすべて送信済みです。再送信しますか？`
        : `${day} の未送信 ${preview.value.pending_count} 件を、まだ届いていない宛先に送りますか？`,
      '送信確認',
      { type: 'warning', confirmButtonText: '送信', cancelButtonText: 'キャンセル' },
    )
  } catch {
    return
  }
  sending.value = true
  try {
    const res = await sendInspectionNewspaperNotification(day, force)
    if (res.data?.skipped) {
      ElMessage.warning(res.message || res.data?.reason || '送信をスキップしました')
    } else if (res.success) {
      ElMessage.success(res.data?.message || res.message || '送信しました')
    } else {
      ElMessage.error(res.data?.message || res.message || '送信に失敗しました')
    }
    await Promise.all([loadPreview(), loadHistory()])
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '送信に失敗しました')
  } finally {
    sending.value = false
  }
}

// ===== 送信履歴 =====
const historyLoading = ref(false)
const history = ref<InspectionNewspaperHistoryItem[]>([])

async function loadHistory() {
  historyLoading.value = true
  try {
    const res = await getInspectionNewspaperHistory(50)
    history.value = res.data?.list ?? []
  } catch (e: any) {
    console.error('送信履歴の取得に失敗:', e)
  } finally {
    historyLoading.value = false
  }
}

onMounted(() => {
  loadSetting()
  loadProducts()
  loadProductOptions()
  loadRecipients()
  loadHistory()
  loadPreview()
})
</script>

<style scoped>
.inn-page {
  min-height: 100%;
  padding: 10px 12px 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  background: linear-gradient(165deg, #f0fdfa 0%, #eff6ff 42%, #f8fafc 100%);
  font-family: 'Inter', 'Noto Sans JP', -apple-system, sans-serif;
}

.inn-header {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding: 16px 18px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(135deg, #0f766e 0%, #0e7490 48%, #1d4ed8 100%);
  box-shadow: 0 12px 32px rgba(14, 116, 144, 0.32);
  animation: inn-rise 0.45s ease both;
}

.inn-header-glow {
  position: absolute;
  top: -70px;
  right: -40px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.18) 0%, transparent 70%);
  pointer-events: none;
}

.inn-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  z-index: 1;
}

.inn-title-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.18);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35), 0 8px 16px rgba(15, 23, 42, 0.18);
  backdrop-filter: blur(8px);
}

.inn-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.inn-subtitle {
  margin: 3px 0 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.88);
}

.inn-header-stats {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}

.inn-stat {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 92px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.22);
  backdrop-filter: blur(10px);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.inn-stat:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.18);
}

.inn-stat-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.inn-stat--product .inn-stat-icon {
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
}

.inn-stat--mail .inn-stat-icon {
  background: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
}

.inn-stat-body {
  display: flex;
  flex-direction: column;
}

.inn-stat-value {
  font-size: 16px;
  font-weight: 800;
  line-height: 1;
}

.inn-stat-label {
  margin-top: 2px;
  font-size: 11px;
  opacity: 0.9;
}

.inn-auto-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: background 0.25s ease, box-shadow 0.25s ease;
}

.inn-auto-pill.is-on {
  background: rgba(16, 185, 129, 0.28);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.18);
}

.inn-auto-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  box-shadow: 0 0 0 0 rgba(148, 163, 184, 0.5);
}

.inn-auto-pill.is-on .inn-auto-dot {
  background: #34d399;
  animation: inn-pulse 1.6s ease-out infinite;
}

.inn-switch-label {
  font-size: 12px;
  font-weight: 700;
}

.inn-row {
  width: 100%;
}

.inn-row--delay-1 {
  animation: inn-rise 0.5s ease 0.06s both;
}

.inn-row--delay-2 {
  animation: inn-rise 0.5s ease 0.12s both;
}

.inn-row--delay-3 {
  animation: inn-rise 0.5s ease 0.18s both;
}

.inn-panel {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
  overflow: hidden;
  height: 100%;
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.inn-panel:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 28px rgba(15, 23, 42, 0.1);
}

.inn-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px 14px;
  border-bottom: 1px solid #eef2f7;
}

.inn-panel--product .inn-panel-head {
  background: linear-gradient(135deg, #ecfdf5 0%, #f0fdfa 100%);
}

.inn-panel--mail .inn-panel-head {
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
}

.inn-panel--preview .inn-panel-head {
  background: linear-gradient(135deg, #fff7ed 0%, #fffbeb 100%);
}

.inn-panel--history .inn-panel-head {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.inn-head-tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.inn-panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.inn-panel-title h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 800;
  color: #1e293b;
}

.inn-panel-title p {
  margin: 2px 0 0;
  font-size: 11px;
  color: #64748b;
}

.inn-panel-badge {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.16);
}

.inn-panel--product .inn-panel-badge {
  background: linear-gradient(135deg, #10b981 0%, #047857 100%);
}

.inn-panel--mail .inn-panel-badge,
.inn-panel-badge--mail {
  background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
}

.inn-panel--preview .inn-panel-badge {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.inn-panel--history .inn-panel-badge {
  background: linear-gradient(135deg, #475569 0%, #1e293b 100%);
}

.inn-panel-body {
  padding: 12px 14px 14px;
}

.inn-add-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.inn-add-select {
  flex: 1;
}

.inn-btn.el-button {
  border: none;
  font-weight: 700;
  border-radius: 10px;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.16);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

@media (max-width: 1199px) {
  .inn-row :deep(.el-col) {
    margin-bottom: 14px;
  }
}

.inn-btn:not(:disabled):hover {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.inn-btn--pdf {
  --el-button-bg-color: #fff;
  --el-button-text-color: #047857;
  --el-button-hover-bg-color: #ecfdf5;
  --el-button-hover-text-color: #047857;
  background: #fff !important;
  color: #047857 !important;
  border: 1px solid #6ee7b7 !important;
  box-shadow: none;
}

.inn-btn--pdf.is-disabled,
.inn-btn--pdf:disabled {
  color: #94a3b8 !important;
  border-color: #e2e8f0 !important;
  background: #f8fafc !important;
}

.inn-btn--product {
  --el-button-bg-color: transparent;
  --el-button-border-color: transparent;
  --el-button-hover-bg-color: transparent;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  color: #fff !important;
}

.inn-btn--mail {
  --el-button-bg-color: transparent;
  --el-button-border-color: transparent;
  --el-button-hover-bg-color: transparent;
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
  color: #fff !important;
}

.inn-btn--send {
  --el-button-bg-color: transparent;
  --el-button-border-color: transparent;
  --el-button-hover-bg-color: transparent;
  background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%) !important;
  color: #fff !important;
}

.inn-btn--preview {
  --el-button-bg-color: transparent;
  --el-button-border-color: transparent;
  --el-button-hover-bg-color: transparent;
  --el-button-text-color: #fff;
  background: linear-gradient(135deg, #0ea5e9 0%, #0369a1 100%) !important;
  color: #fff !important;
}

.inn-btn--ghost {
  --el-button-bg-color: #fff;
  --el-button-text-color: #334155;
  --el-button-hover-bg-color: #f8fafc;
  background: #fff !important;
  color: #334155 !important;
  border: 1px solid #cbd5e1 !important;
  box-shadow: none;
}

.inn-preview-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.inn-date {
  width: 150px;
}

.inn-readonly-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #64748b;
}

.inn-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
}

.inn-banner--warn {
  background: #fff7ed;
  color: #9a3412;
  border: 1px solid #fed7aa;
}

.inn-banner--ok {
  background: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.inn-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.inn-metric {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 6px 14px rgba(15, 23, 42, 0.05);
}

.inn-metric--teal {
  background: linear-gradient(180deg, #ecfdf5 0%, #d1fae5 100%);
  border-color: #a7f3d0;
}

.inn-metric--indigo {
  background: linear-gradient(180deg, #eef2ff 0%, #e0e7ff 100%);
  border-color: #c7d2fe;
}

.inn-metric--amber {
  background: linear-gradient(180deg, #fffbeb 0%, #fef3c7 100%);
  border-color: #fde68a;
}

.inn-metric--slate {
  background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
  border-color: #cbd5e1;
}

.inn-metric-label {
  display: block;
  font-size: 11px;
  color: #64748b;
  font-weight: 600;
}

.inn-metric-value {
  display: block;
  margin-top: 4px;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.15;
}

.inn-metric-value small {
  margin-left: 4px;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
}

.inn-metric-value--sm {
  font-size: 13px;
  font-weight: 700;
}

.inn-code {
  display: inline-block;
  padding: 1px 7px;
  border-radius: 6px;
  background: #ecfdf5;
  color: #047857;
  font-weight: 700;
  font-size: 12px;
}

.inn-qty {
  font-weight: 800;
  color: #b45309;
}

.inn-table :deep(.el-table__header th) {
  background: #f8fafc;
  color: #334155;
  font-weight: 700;
}

.inn-table :deep(.el-table__row) {
  transition: background 0.15s ease;
}

.inn-table :deep(.el-table__body tr:hover > td) {
  background: #f0fdfa !important;
}

.inn-dialog-head {
  display: flex;
  align-items: center;
  gap: 10px;
}

.inn-dialog-head h3 {
  margin: 0;
  font-size: 16px;
}

.inn-dialog-head p {
  margin: 2px 0 0;
  font-size: 12px;
  color: #64748b;
}

@keyframes inn-rise {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes inn-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.55);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(52, 211, 153, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(52, 211, 153, 0);
  }
}

@media (max-width: 1100px) {
  .inn-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .inn-header {
    padding: 14px;
  }

  .inn-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
