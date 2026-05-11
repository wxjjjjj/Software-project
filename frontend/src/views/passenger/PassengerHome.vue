<template>
  <div class="home-page">
    <!-- 顶部横幅 -->
    <div class="hero-banner">
      <div class="hero-text">
        <div class="hero-label">拼车出行</div>
        <div class="hero-title">找到今天的<br>同路人</div>
        <div class="hero-sub">当前 <b>{{ orders.length }}</b> 条订单招募中</div>
      </div>
      <div class="hero-visual">
        <div class="hero-circle c1"></div>
        <div class="hero-circle c2"></div>
        <span class="hero-emoji">🚗</span>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <router-link to="/passenger/orders/publish" class="action-card ac-blue">
        <div class="ac-icon">＋</div>
        <div class="ac-text">
          <div class="ac-title">发布订单</div>
          <div class="ac-hint">招募同行人</div>
        </div>
      </router-link>
      <div class="action-col">
        <router-link to="/passenger/orders/search" class="action-card ac-teal">
          <div class="ac-icon sm">🔍</div>
          <div class="ac-title sm">搜索拼车</div>
        </router-link>
        <router-link to="/passenger/orders/mine" class="action-card ac-warm">
          <div class="ac-icon sm">📋</div>
          <div class="ac-title sm">我的订单</div>
        </router-link>
      </div>
    </div>

    <!-- 最新发布 -->
    <div class="section-label">
      <span class="section-dot"></span>最新招募
    </div>

    <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
    <van-empty v-else-if="!orders.length" image="search" description="暂无可拼订单" />
    <template v-else>
      <div
        v-for="(o, i) in orders"
        :key="o.order_id"
        class="order-card"
        :style="{ animationDelay: `${i * 0.06}s` }"
        @click="$router.push(`/passenger/orders/${o.order_id}`)"
      >
        <div class="card-head">
          <van-tag :type="statusType(o.status)" class="status-tag">{{ statusLabel(o.status) }}</van-tag>
          <span class="card-price">¥{{ o.expected_price }}</span>
        </div>
        <div class="card-route">
          <div class="route-node">
            <span class="node-dot start"></span>
            <span class="node-name">{{ o.start_loc }}</span>
          </div>
          <div class="route-track"><span class="track-line"></span></div>
          <div class="route-node">
            <span class="node-dot end"></span>
            <span class="node-name">{{ o.end_loc }}</span>
          </div>
        </div>
        <div class="card-footer">
          <span class="foot-item">🕐 {{ fmtTime(o.depart_time_from) }}</span>
          <span class="foot-seats">
            <span class="seat-bar">
              <span class="seat-fill" :style="{ width: `${Math.min(o.seats_joined / o.seats_needed * 100, 100)}%` }"></span>
            </span>
            剩 {{ o.remaining_seats }} 座
          </span>
        </div>
        <div class="card-tags" v-if="o.tags?.length">
          <span v-for="t in o.tags" :key="t" class="mini-tag">{{ t }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { rideApi, STATUS_MAP, formatTime } from '@/api/ride.js'

const orders  = ref([])
const loading = ref(true)

const statusLabel = (s) => STATUS_MAP[s]?.label || s
const statusType  = (s) => STATUS_MAP[s]?.type  || 'default'
const fmtTime     = (s) => formatTime(s)

onMounted(async () => {
  try {
    const res = await rideApi.searchOrders({})
    orders.value = res.items?.slice(0, 10) || []
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.home-page { padding-bottom: 28px; }

/* ── 横幅 ── */
.hero-banner {
  display: flex; justify-content: space-between; align-items: flex-end;
  background: linear-gradient(135deg, #0f3fa8 0%, #165DFF 55%, #4f8bff 100%);
  border-radius: 20px; padding: 22px 20px 20px;
  margin-bottom: 14px; overflow: hidden; position: relative;
}
.hero-label { font-size: 11px; color: rgba(255,255,255,.6); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px; }
.hero-title { font-size: 24px; font-weight: 800; color: #fff; line-height: 1.25; margin-bottom: 8px; }
.hero-sub   { font-size: 12px; color: rgba(255,255,255,.75); }
.hero-sub b { color: #fff; }
.hero-visual { position: relative; width: 72px; height: 72px; flex-shrink: 0; }
.hero-circle {
  position: absolute; border-radius: 50%;
  background: rgba(255,255,255,.12);
}
.c1 { width: 64px; height: 64px; top: 0; right: 0; }
.c2 { width: 40px; height: 40px; bottom: -8px; right: 16px; background: rgba(255,255,255,.08); }
.hero-emoji { position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); font-size: 32px; }

/* ── 快捷操作 ── */
.quick-actions {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 10px; margin-bottom: 6px;
}
.action-col { display: flex; flex-direction: column; gap: 10px; }
.action-card {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 16px; border-radius: 16px;
  text-decoration: none;
  transition: transform .14s, box-shadow .14s;
}
.action-card:active { transform: scale(.96); }
.ac-blue { background: #165DFF; box-shadow: 0 6px 18px rgba(22,93,255,.35); flex-direction: column; align-items: flex-start; padding: 18px; }
.ac-teal { background: #f0f9ff; }
.ac-warm { background: #fff7ed; }
.ac-icon { font-size: 26px; line-height: 1; color: #fff; margin-bottom: 8px; }
.ac-icon.sm { font-size: 20px; color: inherit; margin: 0; }
.ac-text {}
.ac-title { font-size: 15px; font-weight: 700; color: #fff; }
.ac-title.sm { font-size: 13px; font-weight: 600; color: #1e293b; }
.ac-hint  { font-size: 11px; color: rgba(255,255,255,.7); margin-top: 2px; }

/* ── 段落标签 ── */
.section-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: #1e293b;
  padding: 8px 2px 10px; letter-spacing: .4px;
}
.section-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: #165DFF; flex-shrink: 0;
}

/* ── 订单卡片 ── */
@keyframes slideUp {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
.order-card {
  background: #fff; border-radius: 16px;
  padding: 14px 16px; margin-bottom: 10px;
  box-shadow: 0 2px 14px rgba(22,93,255,.08);
  cursor: pointer;
  animation: slideUp .3s ease both;
  transition: transform .15s, box-shadow .15s;
}
.order-card:active { transform: scale(.985); box-shadow: 0 1px 6px rgba(22,93,255,.05); }

.card-head {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 10px;
}
.card-price { font-size: 18px; font-weight: 800; color: #f97316; }

.card-route {
  display: flex; align-items: center; gap: 0;
  margin-bottom: 10px;
}
.route-node { display: flex; align-items: center; gap: 7px; min-width: 0; }
.node-dot {
  width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
  border: 2px solid currentColor;
}
.node-dot.start { color: #165DFF; background: #165DFF; }
.node-dot.end   { color: #f97316; background: #f97316; }
.node-name {
  font-size: 15px; font-weight: 700; color: #1e293b;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.route-track {
  flex: 1; display: flex; align-items: center;
  padding: 0 8px; min-width: 20px;
}
.track-line {
  width: 100%; height: 1.5px;
  background: repeating-linear-gradient(90deg, #cbd5e1 0, #cbd5e1 4px, transparent 4px, transparent 8px);
}

.card-footer {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12px; color: #64748b; margin-bottom: 6px;
}
.foot-seats { display: flex; align-items: center; gap: 6px; }
.seat-bar {
  width: 40px; height: 4px; background: #e2e8f0;
  border-radius: 2px; overflow: hidden;
}
.seat-fill {
  height: 100%; background: #165DFF; border-radius: 2px;
  transition: width .3s;
}

.card-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.mini-tag {
  padding: 2px 8px; border-radius: 20px; font-size: 11px;
  background: #f0f5ff; color: #165DFF; border: 1px solid #dce8ff;
}
.page-loading { display: flex; justify-content: center; padding: 40px 0; }
</style>
