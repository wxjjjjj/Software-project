<template>
  <div class="mine-page">
    <van-tabs v-model:active="activeTab" @change="onTabChange">
      <van-tab title="全部" name="" />
      <van-tab title="招募中" name="published" />
      <van-tab title="已锁单" name="locked" />
      <van-tab title="已完成" name="completed" />
    </van-tabs>

    <div class="list-wrap">
      <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
      <van-empty v-else-if="!filtered.length" description="暂无相关订单" />
      <template v-else>
        <div
          v-for="(o, i) in filtered"
          :key="o.order_id"
          class="order-card"
          :class="`s-${o.status}`"
          :style="{ animationDelay: `${i * 0.05}s` }"
          @click="$router.push(`/passenger/orders/${o.order_id}`)"
        >
          <div class="card-head">
            <van-tag :type="statusType(o.status)">{{ statusLabel(o.status) }}</van-tag>
            <span class="my-badge" v-if="o.passenger_id === userId">我发布</span>
            <span class="card-price">¥{{ o.expected_price }}</span>
          </div>
          <div class="card-route">
            <div class="route-node">
              <span class="nd s"></span>
              <span class="nd-name">{{ o.start_loc }}</span>
            </div>
            <div class="route-dash"><span></span></div>
            <div class="route-node">
              <span class="nd e"></span>
              <span class="nd-name">{{ o.end_loc }}</span>
            </div>
          </div>
          <div class="card-meta">
            <span>🕐 {{ fmtTime(o.depart_time_from) }}</span>
            <span class="seats-info">
              <span class="mini-bar">
                <span class="mini-fill" :style="{ width: `${Math.min(o.seats_joined/o.seats_needed*100,100)}%` }"></span>
              </span>
              {{ o.seats_joined }}/{{ o.seats_needed }} 人
            </span>
          </div>
          <div class="card-tags" v-if="o.tags?.length">
            <span v-for="t in o.tags" :key="t" class="mini-tag">{{ t }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { rideApi, STATUS_MAP, formatTime, getUserId } from '@/api/ride.js'

const orders    = ref([])
const loading   = ref(true)
const activeTab = ref('')
const userId    = getUserId()

const statusLabel = (s) => STATUS_MAP[s]?.label || s
const statusType  = (s) => STATUS_MAP[s]?.type  || 'default'
const fmtTime     = (s) => formatTime(s)

const visibleOrders = computed(() => orders.value.filter(o => o.status !== 'cancelled'))
const filtered = computed(() =>
  activeTab.value ? visibleOrders.value.filter(o => o.status === activeTab.value) : visibleOrders.value
)

onMounted(() => loadOrders())

async function loadOrders() {
  loading.value = true
  try {
    const res = await rideApi.listMyOrders()
    orders.value = res.items || []
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

function onTabChange() {}
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
  cursor: pointer; position: relative;
  border-left: 3px solid #e2e8f0;
  animation: fadeUp .28s ease both;
  transition: transform .14s;
}
.order-card:active { transform: scale(.985); }
.order-card.s-published { border-left-color: #165DFF; }
.order-card.s-locked    { border-left-color: #f97316; }
.order-card.s-completed { border-left-color: #10b981; }
.order-card.s-full      { border-left-color: #f59e0b; }

.card-head {
  display: flex; align-items: center; gap: 7px;
  margin-bottom: 10px;
}
.my-badge {
  font-size: 10px; font-weight: 700; color: #165DFF;
  background: #eff6ff; border: 1px solid #bfdbfe;
  border-radius: 20px; padding: 1px 7px;
}
.card-price { margin-left: auto; font-size: 16px; font-weight: 800; color: #f97316; }

.card-route {
  display: flex; align-items: center;
  gap: 0; margin-bottom: 9px;
}
.route-node { display: flex; align-items: center; gap: 6px; }
.nd {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.nd.s { background: #165DFF; }
.nd.e { background: #f97316; }
.nd-name { font-size: 15px; font-weight: 700; color: #1e293b; }
.route-dash {
  flex: 1; padding: 0 8px;
}
.route-dash span {
  display: block; height: 1.5px;
  background: repeating-linear-gradient(90deg,#cbd5e1 0,#cbd5e1 4px,transparent 4px,transparent 8px);
}

.card-meta {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12px; color: #64748b; margin-bottom: 6px;
}
.seats-info { display: flex; align-items: center; gap: 6px; }
.mini-bar { width: 36px; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
.mini-fill { height: 100%; background: #165DFF; border-radius: 2px; }

.card-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.mini-tag {
  padding: 2px 8px; border-radius: 20px; font-size: 11px;
  background: #f0f5ff; color: #165DFF; border: 1px solid #dce8ff;
}
.page-loading { display: flex; justify-content: center; padding: 40px 0; }
</style>
