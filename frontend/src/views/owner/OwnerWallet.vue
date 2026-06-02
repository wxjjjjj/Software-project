<template>
  <div class="page-card">
    <div class="balance-card">
      <div class="balance-label">可用余额</div>
      <div class="balance-amount">¥{{ balance }}</div>
      <div class="balance-sub">冻结: ¥{{ frozen }}</div>
    </div>

    <van-button type="primary" block @click="showWithdraw = true" :disabled="balance <= 0">
      申请提现
    </van-button>

    <van-list
      v-model:loading="logLoading"
      :finished="logFinished"
      finished-text="没有更多了"
      @load="loadLogs"
    >
      <van-cell
        v-for="item in logs"
        :key="item.logId"
        :title="item.remark || bizTypeLabel(item.bizType)"
        :label="formatTime(item.createdAt)"
      >
        <template #value>
          <span :class="item.amountChange >= 0 ? 'green' : 'red'">
            {{ item.amountChange >= 0 ? '+' : '' }}{{ item.amountChange }}
          </span>
        </template>
      </van-cell>
    </van-list>

    <van-empty v-if="!logLoading && logs.length === 0" description="暂无流水" />

    <van-dialog
      v-model:show="showWithdraw"
      title="申请提现"
      show-cancel-button
      :before-close="doWithdraw"
    >
      <van-field
        v-model="withdrawAmount"
        label="金额"
        type="number"
        placeholder="请输入提现金额"
      />
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { showToast } from 'vant'
import { walletInfo, walletLogs, walletWithdraw, getUserId } from '../../api/ops.js'

const balance = ref(0)
const frozen = ref(0)
const logs = ref([])
const logLoading = ref(false)
const logFinished = ref(false)
const logPage = ref(1)
const showWithdraw = ref(false)
const withdrawAmount = ref('')

const BIZ_LABELS = { 1: '支付', 2: '提现', 3: '退款', 4: '充值' }

function bizTypeLabel(t) { return BIZ_LABELS[t] || '其他' }

function formatTime(t) {
  if (!t) return ''
  return t.slice(0, 19).replace('T', ' ')
}

onMounted(async () => {
  try {
    const info = await walletInfo(getUserId())
    balance.value = info.balance
    frozen.value = info.frozenAmount
  } catch { showToast('获取钱包信息失败') }
})

async function loadLogs() {
  logLoading.value = true
  try {
    const data = await walletLogs(getUserId(), logPage.value)
    logs.value.push(...data.items)
    logPage.value++
    if (logs.value.length >= data.total) logFinished.value = true
  } catch {
    showToast('加载流水失败')
  } finally {
    logLoading.value = false
  }
}

async function doWithdraw(action) {
  if (action !== 'confirm') return true
  const amt = parseFloat(withdrawAmount.value)
  if (!amt || amt <= 0) { showToast('请输入有效金额'); return false }
  if (amt > balance.value) { showToast('余额不足'); return false }
  try {
    await walletWithdraw({ userId: getUserId(), amount: amt })
    showToast('提现申请已提交')
    balance.value -= amt
    frozen.value += amt
    withdrawAmount.value = ''
    return true
  } catch (e) {
    showToast(e.message || '提现失败')
    return false
  }
}
</script>

<style scoped>
.balance-card {
  background: linear-gradient(135deg, #1989fa, #07c160);
  color: #fff;
  border-radius: 12px;
  padding: 24px 16px;
  margin-bottom: 16px;
  text-align: center;
}
.balance-label { font-size: 14px; opacity: 0.9; }
.balance-amount { font-size: 36px; font-weight: bold; margin: 8px 0; }
.balance-sub { font-size: 12px; opacity: 0.8; }
.green { color: #07c160; font-weight: bold; }
.red { color: #ee0a24; font-weight: bold; }
</style>
