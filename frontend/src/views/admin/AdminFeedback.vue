<template>
  <div class="page-card">
    <!-- 统计概览 -->
    <van-row gutter="8" class="stats-row">
      <van-col span="8"><div class="stat-card">钱包数<br><strong>{{ stats.walletCount }}</strong></div></van-col>
      <van-col span="8"><div class="stat-card">支付总额<br><strong>¥{{ stats.payAmount }}</strong></div></van-col>
      <van-col span="8"><div class="stat-card">待处理投诉<br><strong>{{ stats.pending }}</strong></div></van-col>
    </van-row>

    <!-- 功能页签：投诉管理 / 提现管理 -->
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
      <van-cell
        v-for="item in list"
        :key="item.ticketId"
        clickable
        @click="openHandle(item)"
      >
        <template #title>
          <span>投诉 #{{ item.ticketId }}</span>
          <van-tag :type="statusTag(item.status)" style="margin-left:8px">{{ statusText(item.status) }}</van-tag>
        </template>
        <template #label>
          <div>投诉人: {{ item.plaintiffId }} | 时间: {{ formatTime(item.createdAt) }}</div>
          <div>{{ item.detail }}</div>
          <div v-if="item.adminReply" class="reply-text">回复: {{ item.adminReply }}</div>
        </template>
      </van-cell>
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
      <van-cell
        v-for="item in withdrawals"
        :key="item.walletId"
      >
        <template #title>
          <span>用户 #{{ item.userId }}</span>
        </template>
        <template #label>
          <div>余额: ¥{{ item.balance }} | 冻结: ¥{{ item.frozenAmount }}</div>
        </template>
        <template #value>
          <van-button size="mini" type="success" @click="doApprove(item.userId)">通过</van-button>
          <van-button size="mini" type="danger" @click="doReject(item.userId)">驳回</van-button>
        </template>
      </van-cell>
    </van-list>
    <van-empty v-if="!wdLoading && withdrawals.length === 0" description="暂无提现申请" />
    </template>

    <!-- 投诉处理弹窗 -->
    <van-dialog
      v-model:show="showDialog"
      title="处理投诉"
      show-cancel-button
      :before-close="doHandle"
    >
      <van-cell title="投诉编号" :value="currentItem?.ticketId" />
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
import { ref, onMounted } from 'vue'
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

function statusText(s) { return STATUS_MAP[s] || '未知' }
function statusTag(s) { return STATUS_TAG[s] || 'default' }

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
.stats-row { margin-bottom: 12px; }
.stat-card {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 4px;
  text-align: center;
  font-size: 12px;
}
.stat-card strong { font-size: 18px; display: block; margin-top: 4px; }
.reply-text { color: #1989fa; font-size: 12px; margin-top: 4px; }
</style>
