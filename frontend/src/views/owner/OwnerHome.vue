<template>
  <div class="owner-home">
    <!-- 统计横幅 -->
    <div class="stat-banner">
      <div class="sb-item" @click="$router.push('/driver/orders/available')">
        <div class="sb-num">{{ stats.available }}</div>
        <div class="sb-label">待接订单</div>
        <div class="sb-pulse" v-if="stats.available > 0"></div>
      </div>
      <div class="sb-divider"></div>
      <div class="sb-item">
        <div class="sb-num orange">{{ stats.locked }}</div>
        <div class="sb-label">进行中</div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-actions">
      <router-link to="/driver/orders/available" class="qa-card qa-fire">
        <div class="qa-icon">🔥</div>
        <div class="qa-info">
          <div class="qa-title">可接订单</div>
          <div class="qa-sub">附近 {{ stats.available }} 条招募中</div>
        </div>
        <span class="qa-badge" v-if="stats.available > 0">{{ stats.available }}</span>
        <span class="qa-arrow">›</span>
      </router-link>
      <router-link to="/driver/orders/mine" class="qa-card qa-notes">
        <div class="qa-icon">📋</div>
        <div class="qa-info">
          <div class="qa-title">我的接单</div>
          <div class="qa-sub">{{ stats.locked }} 条进行中</div>
        </div>
        <span class="qa-arrow">›</span>
      </router-link>
    </div>

    <!-- 最近接单 -->
    <div class="section-label">
      <span class="section-dot"></span>最近接单
    </div>
    <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
    <van-empty v-else-if="!recentOrders.length" description="暂无接单记录" />
    <template v-else>
      <div
        v-for="(o, i) in recentOrders"
        :key="o.order_id"
        class="order-card"
        :class="`s-${o.status}`"
        :style="{ animationDelay: `${i * 0.06}s` }"
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
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { rideApi, STATUS_MAP, formatTime } from '@/api/ride.js'

const recentOrders = ref([])
const loading = ref(true)
const stats   = ref({ available: 0, locked: 0 })

const statusLabel = (s) => STATUS_MAP[s]?.label || s
const statusType  = (s) => STATUS_MAP[s]?.type  || 'default'
const fmtTime     = (s) => formatTime(s)

onMounted(async () => {
  try {
    const [driverRes, searchRes] = await Promise.all([
      rideApi.listDriverOrders(),
      rideApi.searchOrders({}),
    ])
    recentOrders.value     = (driverRes.items || []).slice(0, 5)
    stats.value.locked     = (driverRes.items || []).filter(o => o.status === 'locked').length
    stats.value.available  = (searchRes.items || []).length
  } catch {
    recentOrders.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.owner-home { padding-bottom: 24px; }

/* 统计横幅 */
.stat-banner {
  display: flex; align-items: center;
  background: linear-gradient(135deg, #0f3fa8 0%, #165DFF 60%, #4f8bff 100%);
  border-radius: 20px; padding: 20px 0;
  margin-bottom: 12px; color: #fff;
}
.sb-item {
  flex: 1; text-align: center; position: relative; cursor: pointer;
}
.sb-num   { font-size: 36px; font-weight: 900; line-height: 1; margin-bottom: 4px; }
.sb-num.orange { color: #fbbf24; }
.sb-label { font-size: 12px; opacity: .75; }
.sb-divider { width: 1px; background: rgba(255,255,255,.2); height: 40px; align-self: center; }
.sb-pulse {
  position: absolute; top: 4px; right: calc(50% - 24px);
  width: 8px; height: 8px; border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 0 0 rgba(74,222,128,.4);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%   { box-shadow: 0 0 0 0 rgba(74,222,128,.4); }
  70%  { box-shadow: 0 0 0 8px rgba(74,222,128,0); }
  100% { box-shadow: 0 0 0 0 rgba(74,222,128,0); }
}

/* 快捷入口 */
.quick-actions { display: flex; flex-direction: column; gap: 10px; margin-bottom: 6px; }
.qa-card {
  display: flex; align-items: center; gap: 14px;
  padding: 14px 16px; border-radius: 16px;
  text-decoration: none; position: relative;
  transition: transform .14s;
}
.qa-card:active { transform: scale(.97); }
.qa-fire  { background: #fff7ed; }
.qa-notes { background: #f0fdf4; }
.qa-icon  { font-size: 24px; }
.qa-title { font-size: 14px; font-weight: 700; color: #1e293b; }
.qa-sub   { font-size: 11px; color: #94a3b8; margin-top: 2px; }
.qa-badge {
  margin-left: auto; background: #ef4444; color: #fff;
  font-size: 11px; font-weight: 700;
  padding: 2px 7px; border-radius: 10px;
}
.qa-arrow { font-size: 20px; color: #cbd5e1; margin-left: auto; }
.qa-badge + .qa-arrow { margin-left: 6px; }

/* 段落标签 */
.section-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: #1e293b;
  padding: 8px 2px 10px;
}
.section-dot { width: 8px; height: 8px; border-radius: 50%; background: #165DFF; flex-shrink: 0; }

/* 订单卡片 */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
.order-card {
  background: #fff; border-radius: 16px;
  padding: 13px 16px; margin-bottom: 10px;
  box-shadow: 0 2px 12px rgba(22,93,255,.07);
  border-left: 3px solid #e2e8f0;
  animation: fadeUp .28s ease both;
}
.order-card.s-locked    { border-left-color: #f97316; }
.order-card.s-completed { border-left-color: #10b981; }
.order-card.s-cancelled { border-left-color: #cbd5e1; opacity: .7; }

.card-head {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 9px;
}
.card-price { margin-left: auto; font-size: 16px; font-weight: 800; color: #f97316; }

.card-route {
  display: flex; align-items: center; gap: 6px;
  margin-bottom: 7px;
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

.card-meta { display: flex; gap: 12px; font-size: 12px; color: #64748b; }
.page-loading { display: flex; justify-content: center; padding: 40px 0; }
</style>
