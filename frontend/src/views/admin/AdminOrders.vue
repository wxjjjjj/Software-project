<template>
  <div class="admin-orders">
    <!-- 顶部标题栏 -->
    <div class="admin-header">
      <div class="ah-title">订单管理</div>
      <div class="ah-total">共 <b>{{ filtered.length }}</b> 条</div>
    </div>

    <!-- 搜索 -->
    <div class="search-wrap">
      <span class="sw-icon">🔍</span>
      <input v-model="searchText" placeholder="搜索出发地 / 目的地…" class="sw-input" />
      <span v-if="searchText" class="sw-clear" @click="searchText = ''">×</span>
    </div>

    <!-- 状态筛选 -->
    <div class="filter-chips">
      <span
        v-for="opt in statusOptions"
        :key="opt.value"
        class="f-chip"
        :class="{ active: statusFilter === opt.value }"
        @click="statusFilter = opt.value"
      >{{ opt.text }}</span>
    </div>

    <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
    <van-empty v-else-if="!filtered.length" description="暂无订单数据" />
    <template v-else>
      <div
        v-for="(o, i) in filtered"
        :key="o.order_id"
        class="order-card"
        :class="`s-${o.status}`"
        :style="{ animationDelay: `${i * 0.04}s` }"
      >
        <div class="card-head">
          <van-tag :type="statusType(o.status)" size="medium">{{ statusLabel(o.status) }}</van-tag>
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
          <span>👥 {{ o.seats_joined }}/{{ o.seats_needed }} 人</span>
        </div>
        <div class="card-ids">
          <span class="id-item">发单 <code>{{ o.passenger_id }}</code></span>
          <span class="id-item" v-if="o.owner_id">车主 <code>{{ o.owner_id }}</code></span>
        </div>
        <div class="card-tags" v-if="o.tags?.length">
          <span v-for="t in o.tags" :key="t" class="mini-tag">{{ t }}</span>
        </div>
        <div class="card-action" v-if="o.status !== 'completed' && o.status !== 'cancelled'">
          <button class="btn-force-cancel" @click="forceCancel(o)">强制取消</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { showConfirmDialog, showToast, showSuccessToast } from 'vant'
import { rideApi, STATUS_MAP, formatTime } from '@/api/ride.js'

const orders       = ref([])
const loading      = ref(true)
const searchText   = ref('')
const statusFilter = ref('')

const statusLabel = (s) => STATUS_MAP[s]?.label || s
const statusType  = (s) => STATUS_MAP[s]?.type  || 'default'
const fmtTime     = (s) => formatTime(s)

const statusOptions = [
  { text: '全部',   value: '' },
  { text: '招募中', value: 'published' },
  { text: '已满员', value: 'full' },
  { text: '已锁单', value: 'locked' },
  { text: '已完成', value: 'completed' },
  { text: '已取消', value: 'cancelled' },
]

const filtered = computed(() => {
  let list = orders.value
  if (statusFilter.value) list = list.filter(o => o.status === statusFilter.value)
  if (searchText.value) {
    const kw = searchText.value.toLowerCase()
    list = list.filter(o =>
      o.start_loc?.toLowerCase().includes(kw) ||
      o.end_loc?.toLowerCase().includes(kw)
    )
  }
  return list
})

onMounted(() => loadOrders())

async function loadOrders() {
  loading.value = true
  try {
    const res = await rideApi.listAllOrders()
    orders.value = res.items || []
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

async function forceCancel(o) {
  try {
    await showConfirmDialog({
      title: '强制取消订单',
      message: `确认强制取消：${o.start_loc} → ${o.end_loc}？`,
    })
  } catch { return }
  try {
    await rideApi.cancelOrder(o.order_id)
    showSuccessToast('已强制取消')
    await loadOrders()
  } catch (e) {
    showToast(e.message || '操作失败')
  }
}
</script>

<style scoped>
.admin-orders { padding-bottom: 28px; }

/* 顶部 */
.admin-header {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 4px 2px 10px;
}
.ah-title { font-size: 18px; font-weight: 800; color: #1e293b; }
.ah-total { font-size: 13px; color: #94a3b8; }
.ah-total b { color: #165DFF; }

/* 搜索框 */
.search-wrap {
  display: flex; align-items: center; gap: 8px;
  background: #fff; border: 1.5px solid #e2e8f0;
  border-radius: 12px; padding: 9px 14px;
  margin-bottom: 10px;
  transition: border-color .15s;
}
.search-wrap:focus-within { border-color: #165DFF; }
.sw-icon  { font-size: 14px; opacity: .45; flex-shrink: 0; }
.sw-input {
  flex: 1; border: none; outline: none;
  font-size: 14px; color: #1e293b; background: transparent;
}
.sw-clear { font-size: 16px; color: #94a3b8; cursor: pointer; padding: 0 2px; }

/* 状态筛选 */
.filter-chips {
  display: flex; gap: 6px; flex-wrap: wrap;
  margin-bottom: 12px;
}
.f-chip {
  padding: 5px 12px; border-radius: 20px; font-size: 12px;
  border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  cursor: pointer; transition: all .15s; user-select: none;
}
.f-chip.active {
  background: #165DFF; border-color: #165DFF;
  color: #fff; box-shadow: 0 3px 10px rgba(22,93,255,.3);
}

/* 订单卡片 */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.order-card {
  background: #fff; border-radius: 16px;
  padding: 13px 16px; margin-bottom: 10px;
  box-shadow: 0 2px 12px rgba(22,93,255,.07);
  border-left: 3px solid #e2e8f0;
  animation: fadeUp .25s ease both;
}
.order-card.s-published { border-left-color: #165DFF; }
.order-card.s-full      { border-left-color: #f59e0b; }
.order-card.s-locked    { border-left-color: #f97316; }
.order-card.s-completed { border-left-color: #10b981; }
.order-card.s-cancelled { border-left-color: #cbd5e1; opacity: .65; }

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
  display: flex; gap: 12px; font-size: 12px; color: #64748b; margin-bottom: 5px;
}
.card-ids {
  display: flex; gap: 10px; flex-wrap: wrap;
  font-size: 11px; color: #94a3b8; margin-bottom: 4px;
}
code { font-family: monospace; background: #f8fafc; padding: 1px 5px; border-radius: 4px; }

.card-tags { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 4px; }
.mini-tag {
  padding: 2px 8px; border-radius: 20px; font-size: 11px;
  background: #f0f5ff; color: #165DFF; border: 1px solid #dce8ff;
}

.card-action {
  display: flex; justify-content: flex-end;
  padding-top: 10px; margin-top: 8px;
  border-top: 1px solid #f1f5f9;
}
.btn-force-cancel {
  padding: 6px 16px; border-radius: 20px;
  background: transparent; border: 1.5px solid #fca5a5;
  color: #ef4444; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all .15s;
}
.btn-force-cancel:hover { background: #fef2f2; }
.btn-force-cancel:active { transform: scale(.95); }
.page-loading { display: flex; justify-content: center; padding: 40px 0; }
</style>
