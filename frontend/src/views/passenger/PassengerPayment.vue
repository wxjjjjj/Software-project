<template>
  <div class="page-card">
    <van-cell-group>
      <van-cell title="订单编号" :value="orderId" />
      <van-cell title="可用余额" :value="'¥' + balance" />
    </van-cell-group>

    <van-field
      v-model="amount"
      label="支付金额"
      type="number"
      placeholder="请输入金额"
      :rules="[{ validator: v => v > 0, message: '金额必须大于0' }]"
    />

    <van-field
      v-model="remark"
      label="备注"
      placeholder="可选备注"
    />

    <van-button
      type="primary"
      block
      :loading="paying"
      loading-text="支付中..."
      :disabled="!amount || amount <= 0"
      @click="handlePay"
    >
      确认支付 ¥{{ amount || 0 }}
    </van-button>

    <van-empty v-if="paid" description="支付成功！" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { walletInfo, payOrder, getUserId } from '../../api/ops.js'

const route = useRoute()
const orderId = route.params.orderId
const amount = ref('')
const remark = ref('')
const balance = ref(0)
const paying = ref(false)
const paid = ref(false)

onMounted(async () => {
  try {
    const info = await walletInfo(getUserId())
    balance.value = info.balance
  } catch {
    showToast('获取钱包信息失败')
  }
})

async function handlePay() {
  const amt = parseFloat(amount.value)
  if (!amt || amt <= 0) { showToast('请输入有效金额'); return }
  if (amt > balance.value) { showToast('余额不足'); return }
  paying.value = true
  try {
    const uid = getUserId()
    await payOrder(orderId, {
      payerUserId: uid,
      payeeUserId: uid === 1 ? 2 : 1,
      amount: amt,
      idempotencyKey: `pay_${orderId}_${Date.now()}`
    })
    paid.value = true
    showToast('支付成功')
    balance.value -= amt
  } catch (e) {
    showToast(e.message || '支付失败')
  } finally {
    paying.value = false
  }
}
</script>
