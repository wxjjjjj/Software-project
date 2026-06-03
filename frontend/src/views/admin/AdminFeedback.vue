<template>
  <div class="admin-feedback-page">
    <section class="page-card page-hero">
      <div>
        <div class="eyebrow">运营处理</div>
        <h2>投诉与提现管理</h2>
        <p>集中处理用户投诉、钱包提现与运营统计。</p>
      </div>
    </section>

    <!-- 统计概览 -->
    <section class="stats-row">
      <div class="stat-card"><span>钱包数</span><strong>{{ stats.walletCount }}</strong></div>
      <div class="stat-card"><span>支付总额</span><strong>¥{{ stats.payAmount }}</strong></div>
      <div class="stat-card"><span>待处理投诉</span><strong>{{ stats.pending }}</strong></div>
    </section>

    <!-- 功能页签：投诉管理 / 提现管理 -->
    <section class="page-card content-card">
      <van-tabs v-model:active="adminTab" @change="onTabChange">
        <van-tab title="投诉管理">
          <template #title>投诉管理 <van-tag v-if="stats.pending > 0" type="danger" size="small">{{ stats.pending }}</van-tag></template>
        </van-tab>
        <van-tab title="提现管理" />
      </van-tabs>

      <!-- 投诉管理 -->
      <template v-if="adminTab === 0">
      <van-tabs v-model:active="statusFilter" @change="resetList">
        <van-tab title="全部" :name="-1" />
        <van-tab title="待处理" :name="0" />
        <van-tab title="处理中" :name="1" />
        <van-tab title="已解决" :name="2" />
        <van-tab title="已驳回" :name="3" />
      </van-tabs>

      <!-- 投诉列表 -->
      <van-list
        v-model:loading="listLoading"
        :finished="listFinished"
        finished-text="没有更多了"
        @load="loadList"
      >
        <article
          v-for="item in list"
          :key="item.ticketId"
          class="work-card"
          @click="openHandle(item)"
        >
          <div class="work-head">
            <div>
              <div class="work-title">投诉 #{{ item.ticketId }}</div>
              <div class="work-sub">
                投诉人：{{ item.plaintiffId }} · 被投诉：{{ complaintTargetName(item) }} · {{ formatTime(item.createdAt) }}
              </div>
            </div>
            <van-tag :type="statusTag(item.status)">{{ statusText(item.status) }}</van-tag>
          </div>
          <div class="work-detail">{{ item.detail }}</div>
          <div v-if="item.adminReply" class="reply-text">回复：{{ item.adminReply }}</div>
        </article>
      </van-list>

      <van-empty v-if="!listLoading && list.length === 0" description="暂无投诉" />
      </template>

      <!-- 提现管理 -->
      <template v-if="adminTab === 1">
      <van-list
        v-model:loading="wdLoading"
        :finished="wdFinished"
        finished-text="没有更多了"
        @load="loadWithdrawals"
      >
        <article
          v-for="item in withdrawals"
          :key="item.walletId"
          class="work-card withdrawal-card"
        >
          <div class="work-head">
            <div>
              <div class="work-title">用户 #{{ item.userId }}</div>
              <div class="work-sub">钱包 #{{ item.walletId }}</div>
            </div>
            <div class="amount">¥{{ item.balance }}</div>
          </div>
          <div class="work-detail">冻结金额：¥{{ item.frozenAmount }}</div>
          <div class="work-actions">
            <van-button size="small" type="success" @click="doApprove(item.userId)">通过</van-button>
            <van-button size="small" type="danger" @click="doReject(item.userId)">驳回</van-button>
          </div>
        </article>
      </van-list>
      <van-empty v-if="!wdLoading && withdrawals.length === 0" description="暂无提现申请" />
      </template>
    </section>

    <!-- 投诉处理弹窗 -->
    <van-dialog
      v-model:show="showDialog"
      title="处理投诉"
      show-cancel-button
      :before-close="doHandle"
    >
      <van-cell title="投诉编号" :value="currentItem?.ticketId" />
      <van-cell title="被投诉用户" :value="currentTargetName" />
      <van-cell v-if="currentItem?.orderId" title="关联行程" :value="currentItem?.orderId" />
      <van-cell title="投诉内容" :value="currentItem?.detail" />
      <van-field
        v-model="handleReply"
        label="回复"
        type="textarea"
        rows="3"
        placeholder="管理员回复"
      />
      <van-radio-group v-model="handleStatus" direction="horizontal" style="padding:12px">
        <van-radio :name="1">处理中</van-radio>
        <van-radio :name="2">已解决</van-radio>
        <van-radio :name="3">已驳回</van-radio>
      </van-radio-group>
    </van-dialog>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import { adminListComplaints, adminHandleComplaint, adminStatistics, getUserId,
         adminListWithdrawals, adminApproveWithdrawal, adminRejectWithdrawal } from '../../api/ops.js'

const stats = ref({ walletCount: 0, payAmount: 0, pending: 0 })
const adminTab = ref(0)
const statusFilter = ref(-1)
const list = ref([])
const listLoading = ref(false)
const listFinished = ref(false)
const listPage = ref(1)
const showDialog = ref(false)
const currentItem = ref(null)
const handleStatus = ref(2)
const handleReply = ref('')

const withdrawals = ref([])
const wdLoading = ref(false)
const wdFinished = ref(false)
const wdPage = ref(1)

const STATUS_MAP = { 0: '待处理', 1: '处理中', 2: '已解决', 3: '已驳回', [-1]: '全部' }
const STATUS_TAG = { 0: 'warning', 1: 'primary', 2: 'success', 3: 'default' }
const currentTargetName = computed(() => complaintTargetName(currentItem.value))

function statusText(s) { return STATUS_MAP[s] || '未知' }
function statusTag(s) { return STATUS_TAG[s] || 'default' }

function complaintTargetName(item) {
  if (!item) return ''
  const match = String(item.detail || '').match(/^投诉用户名：(.+)$/m)
  if (match?.[1]) return match[1].trim()
  if (item.defendantId) return `用户 #${item.defendantId}`
  return '未填写'
}

function formatTime(t) {
  if (!t) return ''
  return t.slice(0, 19).replace('T', ' ')
}

onMounted(async () => {
  try {
    const s = await adminStatistics()
    stats.value = { walletCount: s.totalWalletCount, payAmount: s.totalPaymentAmount, pending: s.pendingComplaintCount }
  } catch { /* ignore */ }
})

function onTabChange() {
  if (adminTab.value === 1) {
    withdrawals.value = []
    wdPage.value = 1
    wdFinished.value = false
    loadWithdrawals()
  } else {
    resetList()
  }
}

function resetList() {
  list.value = []
  listPage.value = 1
  listFinished.value = false
  loadList()
}

async function loadList() {
  listLoading.value = true
  try {
    const status = statusFilter.value >= 0 ? statusFilter.value : undefined
    const data = await adminListComplaints(status, listPage.value)
    list.value.push(...data.items)
    listPage.value++
    if (list.value.length >= data.total) listFinished.value = true
  } catch {
    showToast('加载投诉列表失败')
  } finally {
    listLoading.value = false
  }
}

function openHandle(item) {
  currentItem.value = item
  handleStatus.value = item.status === 0 ? 1 : item.status
  handleReply.value = item.adminReply || ''
  showDialog.value = true
}

async function loadWithdrawals() {
  wdLoading.value = true
  try {
    const data = await adminListWithdrawals(wdPage.value)
    withdrawals.value.push(...data.items)
    wdPage.value++
    if (withdrawals.value.length >= data.total) wdFinished.value = true
  } catch {
    showToast('加载提现列表失败')
  } finally {
    wdLoading.value = false
  }
}

async function doApprove(userId) {
  try {
    await showConfirmDialog({ message: `确认通过用户 #${userId} 的提现申请？` })
    await adminApproveWithdrawal(userId)
    showToast('已通过')
    withdrawals.value = []
    wdPage.value = 1
    wdFinished.value = false
    loadWithdrawals()
  } catch { /* cancelled or error */ }
}

async function doReject(userId) {
  try {
    await showConfirmDialog({ message: `确认驳回用户 #${userId} 的提现申请？` })
    await adminRejectWithdrawal(userId)
    showToast('已驳回')
    withdrawals.value = []
    wdPage.value = 1
    wdFinished.value = false
    loadWithdrawals()
  } catch { /* cancelled or error */ }
}

async function doHandle(action) {
  if (action !== 'confirm') return true
  try {
    await adminHandleComplaint(currentItem.value.ticketId, {
      adminId: getUserId(),
      status: handleStatus.value,
      adminReply: handleReply.value
    })
    showToast('处理成功')
    currentItem.value.status = handleStatus.value
    currentItem.value.adminReply = handleReply.value
    return true
  } catch (e) {
    showToast(e.message || '处理失败')
    return false
  }
}
</script>

<style scoped>
.admin-feedback-page {
  display: grid;
  gap: 12px;
  padding: 14px;
  padding-bottom: 28px;
}

.page-hero {
  padding: 18px 16px;
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

h2 {
  margin: 0;
  color: #172033;
  font-size: 22px;
  line-height: 1.1;
}

p {
  margin: 8px 0 0;
  color: #52657d;
  font-size: 13px;
  line-height: 1.6;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.stat-card {
  background: #fff;
  border: 1px solid #dce8ff;
  border-radius: 14px;
  padding: 12px 8px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(22, 93, 255, .06);
}

.stat-card span {
  display: block;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.stat-card strong {
  display: block;
  margin-top: 5px;
  color: #172033;
  font-size: 19px;
  line-height: 1.1;
}

.content-card {
  padding: 8px 12px 14px;
}

.work-card {
  padding: 14px;
  margin-top: 10px;
  border: 1px solid #dce8ff;
  border-radius: 14px;
  background: #fbfdff;
  box-shadow: 0 2px 12px rgba(22, 93, 255, .06);
  cursor: pointer;
}

.work-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.work-title {
  color: #172033;
  font-size: 15px;
  font-weight: 800;
}

.work-sub {
  margin-top: 4px;
  color: #94a3b8;
  font-size: 12px;
}

.work-detail {
  margin-top: 10px;
  color: #475569;
  font-size: 13px;
  line-height: 1.6;
}

.reply-text {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #f0f5ff;
  color: #165dff;
  font-size: 12px;
  line-height: 1.5;
}

.amount {
  color: #f97316;
  font-size: 18px;
  font-weight: 900;
}

.work-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #edf1f7;
}

@media (max-width: 420px) {
  .stats-row {
    grid-template-columns: 1fr;
  }
}
</style>
