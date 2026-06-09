<template>
  <div class="mine-page">
    <van-tabs v-model:active="activeTab">
      <van-tab title="全部"   name="" />
      <van-tab title="进行中" name="locked" />
      <van-tab title="已完成" name="completed" />
    </van-tabs>

    <div class="list-wrap">
      <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
      <van-empty v-else-if="!filtered.length" description="暂无相关接单记录" />
      <template v-else>
        <div
          v-for="(o, i) in filtered"
          :key="o.order_id"
          class="order-card"
          :class="`s-${o.status}`"
          :style="{ animationDelay: `${i * 0.05}s` }"
        >
          <div class="card-head">
            <van-tag :type="statusType(o.status)">{{ statusLabel(o.status) }}</van-tag>
            <span class="card-price">¥{{ o.expected_price }}</span>
          </div>
          <div class="card-route">
            <span class="nd s"></span>
            <span class="nd-name">{{ o.start_loc }}</span>
            <div class="route-dash"><span></span></div>
            <span class="nd e"></span>
            <span class="nd-name">{{ o.end_loc }}</span>
          </div>
          <div class="card-meta">
            <span>🕐 {{ fmtTime(o.depart_time_from) }}</span>
            <span>👥 {{ o.seats_joined }} 人</span>
            <span v-if="o.locked_time" class="lock-time">🔒 {{ fmtTime(o.locked_time) }}</span>
          </div>
          <div class="veh-row" v-if="o.vehicle_id">
            <span class="veh-icon">🚗</span>
            <span class="veh-id">{{ o.vehicle_id }}</span>
          </div>
          <!-- 锁单操作 -->
          <div class="card-action">
            <button class="btn-detail" @click="goDetail(o)">详情</button>
            <button v-if="o.status !== 'completed'" class="btn-chat" @click="goChat(o)">💬 聊天</button>    <!-- yzr -->
            <button v-if="o.status === 'locked'" class="btn-complete" @click="handleComplete(o)">✓ 标记完成</button>
            <button v-if="o.status === 'locked'" class="btn-cancel"   @click="handleCancel(o)">取消接单</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showToast, showSuccessToast } from 'vant'
import { rideApi, STATUS_MAP, formatTime } from '@/api/ride.js'

const router = useRouter()
const orders    = ref([])
const loading   = ref(true)
const activeTab = ref('')

const statusLabel = (s) => STATUS_MAP[s]?.label || s
const statusType  = (s) => STATUS_MAP[s]?.type  || 'default'
const fmtTime     = (s) => formatTime(s)

const visibleOrders = computed(() => orders.value.filter(o => o.status !== 'cancelled'))
const filtered = computed(() =>
  activeTab.value ? visibleOrders.value.filter(o => o.status === activeTab.value) : visibleOrders.value
)

onMounted(() => loadOrders())

function goDetail(o) {
  router.push(`/driver/orders/${o.order_id}`)
}

// yzr: 跳转聊天
function goChat(o) {
  router.push(`/driver/chat/${o.order_id}`)
}

async function loadOrders() {
  loading.value = true
  try {
    const res = await rideApi.listDriverOrders()
    orders.value = res.items || []
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

async function handleComplete(o) {
  try {
    await showConfirmDialog({ title: '标记完成', message: '确认行程已完成？' })
  } catch { return }
  try {
    await rideApi.completeOrder(o.order_id)
    showSuccessToast('行程已完成！')
    await loadOrders()
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}

async function handleCancel(o) {
  try {
    await showConfirmDialog({ title: '取消接单', message: '取消锁单订单将扣除信誉分，确认吗？' })
  } catch { return }
  try {
    await rideApi.cancelOrder(o.order_id)
    showSuccessToast('已取消')
    await loadOrders()
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}
</script>

<style scoped>
.mine-page { padding-bottom: 24px; }
.list-wrap  { padding-top: 8px; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.order-card {
  background: #fff; border-radius: 16px;
  padding: 13px 16px; margin-bottom: 10px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
  border-left: 3px solid #e2e8f0;
  animation: fadeUp .28s ease both;
}
.order-card.s-locked    { border-left-color: #f97316; }
.order-card.s-completed { border-left-color: #10b981; }

.card-head {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 9px;
}
.card-price { margin-left: auto; font-size: 16px; font-weight: 800; color: #f97316; }

.card-route {
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 8px;
}
.nd { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.nd.s { background: #165DFF; }
.nd.e { background: #f97316; }
.nd-name { font-size: 15px; font-weight: 700; color: #1e293b; }
.route-dash { flex: 1; }
.route-dash span {
  display: block; height: 1.5px;
  background: repeating-linear-gradient(90deg,#cbd5e1 0,#cbd5e1 4px,transparent 4px,transparent 8px);
}

.card-meta {
  display: flex; gap: 12px; flex-wrap: wrap;
  font-size: 12px; color: #64748b; margin-bottom: 4px;
}
.lock-time { color: #f97316; }

.veh-row {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #94a3b8; margin-bottom: 4px;
}
.veh-icon { font-size: 13px; }
.veh-id   { font-family: monospace; font-size: 12px; }

/* 操作按钮 */
.card-action {
  display: flex; gap: 8px; justify-content: flex-end;
  margin-top: 10px; padding-top: 10px;
  border-top: 1px solid #f1f5f9;
}
.btn-detail, .btn-complete, .btn-cancel, .btn-chat {
  padding: 6px 14px; border-radius: 20px; border: none;
  font-size: 13px; font-weight: 600; cursor: pointer;
  transition: opacity .15s, transform .15s;
}
.btn-detail:active, .btn-complete:active, .btn-cancel:active, .btn-chat:active { transform: scale(.95); }
.btn-detail {
  background: #fff; color: #165DFF;
  border: 1.5px solid #c7d7ff;
}
.btn-complete {
  background: #10b981; color: #fff;
  box-shadow: 0 3px 10px rgba(16,185,129,.3);
}
.btn-cancel {
  background: transparent; color: #ef4444;
  border: 1.5px solid #fca5a5;
}
.btn-chat {                                             /* yzr */
  background: #fff; color: #8b5cf6;
  border: 1.5px solid #c4b5fd;
}
.page-loading { display: flex; justify-content: center; padding: 40px 0; }
</style>
