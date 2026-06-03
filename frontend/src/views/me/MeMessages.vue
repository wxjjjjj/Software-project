<template>
  <div class="page-card">
    <van-tabs v-model:active="roleTab">
      <van-tab title="我的行程" name="orders" />
    </van-tabs>

    <div class="list-wrap">
      <van-loading v-if="loading" style="padding:40px 0;text-align:center" type="spinner" />
      <van-empty v-else-if="!orders.length" description="暂无订单，聊天功能将在参与订单后可用" />

      <template v-else>
        <div
          v-for="o in orders"
          :key="o.order_id"
          class="order-card"
          :class="'s-' + (o.status || '')"
        >
          <div class="card-head">
            <span class="card-id">订单 #{{ o.order_id }}</span>
            <van-tag v-if="o.status === 'locked'" type="primary">已锁单</van-tag>
            <van-tag v-else-if="o.status === 'completed'" type="success">已完成</van-tag>
            <van-tag v-else type="warning">招募中</van-tag>
          </div>
          <div class="card-route">
            <span class="loc">{{ o.start_loc }}</span>
            <span class="loc-arrow">→</span>
            <span class="loc">{{ o.end_loc }}</span>
          </div>
          <div class="card-action">
            <button class="btn-chat" @click="goChat(o)">
              💬 进入聊天
            </button>
            <button class="btn-detail" @click="goDetail(o)">
              订单详情
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { rideApi } from '@/api/ride.js'

const router = useRouter()
const roleTab = ref('orders')
const orders = ref([])
const loading = ref(true)
const isDriver = ref(false)

function getSession() {
  try { return JSON.parse(localStorage.getItem('session') || '{}') }
  catch { return {} }
}

function isOwnerVerified(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value !== 0
  if (typeof value === 'string') return ['1', 'true', 'yes', 'y', 'on'].includes(value.trim().toLowerCase())
  return Boolean(value)
}

onMounted(async () => {
  const session = getSession()
  const verified = isOwnerVerified(session.ownerVerified)
  isDriver.value = session.role === 'driver' || verified

  console.log('[MeMessages] session:', JSON.stringify(session))
  console.log('[MeMessages] isDriver:', isDriver.value, 'verified:', verified)

  loading.value = true
  try {
    if (isDriver.value && verified) {
      console.log('[MeMessages] calling listDriverOrders')
      const res = await rideApi.listDriverOrders()
      orders.value = (res.items || res || []).filter(o => o.status !== 'cancelled')
    } else {
      console.log('[MeMessages] calling listMyOrders')
      const res = await rideApi.listMyOrders()
      console.log('[MeMessages] listMyOrders response:', res)
      orders.value = (res.items || res || []).filter(o => o.status !== 'cancelled')
    }
    console.log('[MeMessages] filtered orders:', orders.value.length)
  } catch (e) {
    console.error('[MeMessages] error:', e)
    orders.value = []
  } finally {
    loading.value = false
  }
})

function goChat(o) {
  const prefix = isDriver.value ? '/driver' : '/passenger'
  router.push(`${prefix}/chat/${o.order_id}`)
}

function goDetail(o) {
  const prefix = isDriver.value ? '/driver' : '/passenger'
  router.push(`${prefix}/orders/${o.order_id}`)
}
</script>

<style scoped>
.list-wrap { padding-top: 8px; }
.order-card {
  background: #fff; border-radius: 14px; padding: 12px 16px;
  margin-bottom: 10px; box-shadow: 0 2px 12px rgba(22,93,255,.06);
}
.card-head {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.card-id { font-weight: 700; font-size: 14px; color: #1e293b; }
.card-route {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; color: #475569; margin-bottom: 10px;
}
.loc-arrow { color: #94a3b8; }
.card-action {
  display: flex; gap: 8px; justify-content: flex-end;
  padding-top: 8px; border-top: 1px solid #f1f5f9;
}
.btn-chat {
  background: #8b5cf6; color: #fff; border: none;
  padding: 6px 14px; border-radius: 20px; font-size: 13px;
  font-weight: 600; cursor: pointer;
}
.btn-detail {
  background: #fff; color: #165DFF; border: 1.5px solid #c7d7ff;
  padding: 6px 14px; border-radius: 20px; font-size: 13px;
  font-weight: 600; cursor: pointer;
}
</style>
