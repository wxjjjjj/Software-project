<template>
  <div class="detail-page">
    <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />

    <template v-else-if="order">
      <!-- 路线卡 -->
      <div class="route-card">
        <van-tag :type="statusType(order.status)" class="route-status-tag">{{ statusLabel(order.status) }}</van-tag>
        <div class="route-viz">
          <div class="rv-col rv-start">
            <div class="rv-label">出发地</div>
            <div class="rv-name">{{ order.start_loc }}</div>
          </div>
          <div class="rv-mid">
            <div class="rv-dot rv-dot-s"></div>
            <div class="rv-line"></div>
            <div class="rv-plane">✈</div>
            <div class="rv-line"></div>
            <div class="rv-dot rv-dot-e"></div>
          </div>
          <div class="rv-col rv-end">
            <div class="rv-label">目的地</div>
            <div class="rv-name">{{ order.end_loc }}</div>
          </div>
        </div>
        <div class="route-time">🕐 {{ fmtTime(order.depart_time_from) }} ~ {{ fmtTime(order.depart_time_to) }}</div>
      </div>

      <!-- 数据行 -->
      <div class="stats-strip">
        <div class="stat-item">
          <div class="stat-val">{{ order.seats_joined }}/{{ order.seats_needed }}</div>
          <div class="stat-key">已加入/需要</div>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-item">
          <div class="stat-val seats">{{ order.remaining_seats }}</div>
          <div class="stat-key">剩余座位</div>
        </div>
        <div class="stat-sep"></div>
        <div class="stat-item">
          <div class="stat-val price">¥{{ order.expected_price }}</div>
          <div class="stat-key">预期总价</div>
        </div>
      </div>

      <!-- 座位进度条 -->
      <div class="seat-progress-wrap">
        <div class="sp-label">座位占用</div>
        <div class="sp-bar">
          <div
            class="sp-fill"
            :style="{ width: `${Math.min(order.seats_joined / order.seats_needed * 100, 100)}%` }"
          ></div>
        </div>
        <div class="sp-pct">{{ Math.round(order.seats_joined / order.seats_needed * 100) }}%</div>
      </div>

      <!-- 车辆信息（如已接单） -->
      <div class="info-row-card" v-if="order.vehicle_id || order.locked_time">
        <div class="irc-item" v-if="order.vehicle_id">
          <span class="irc-icon">🚗</span>
          <span class="irc-label">车辆</span>
          <span class="irc-val">{{ order.vehicle_id }}</span>
        </div>
        <div class="irc-item" v-if="order.locked_time">
          <span class="irc-icon">🔒</span>
          <span class="irc-label">接单时间</span>
          <span class="irc-val">{{ fmtTime(order.locked_time) }}</span>
        </div>
      </div>

      <!-- 标签 -->
      <div class="tags-wrap" v-if="order.tags?.length">
        <div class="tw-header">订单标签</div>
        <div class="tw-chips">
          <span v-for="t in order.tags" :key="t" class="tag-chip" style="cursor:default">{{ t }}</span>
        </div>
      </div>

      <!-- 操作区 -->
      <div class="action-area" v-if="order.status !== 'cancelled' && order.status !== 'completed'">
        <van-button
          v-if="canJoin"
          round block type="primary" size="large"
          :loading="acting" loading-text="加入中…"
          @click="handleJoin"
        >加入拼车</van-button>

        <div class="joined-tip" v-if="hasJoined && order.status === 'published'">
          <span class="jt-icon">✓</span> 你已加入，等待车主接单
        </div>

        <van-button
          v-if="canCancel"
          round block plain type="danger"
          :loading="acting" loading-text="取消中…"
          class="cancel-btn"
          @click="handleCancel"
        >取消订单{{ order.status !== 'published' ? '（将扣除信誉分）' : '' }}</van-button>
      </div>

      <div class="ended-wrap" v-if="order.status === 'completed'">
        <van-empty image="success" description="行程已完成" />
      </div>
      <div class="ended-wrap" v-if="order.status === 'cancelled'">
        <van-empty description="订单已取消" />
      </div>
    </template>

    <van-empty v-else description="订单不存在" />
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showToast, showSuccessToast } from 'vant'
import { rideApi, STATUS_MAP, formatTime, getUserId } from '@/api/ride.js'

const route   = useRoute()
const router  = useRouter()
const orderId = route.params.id

const order   = ref(null)
const loading = ref(true)
const acting  = ref(false)
const userId  = getUserId()

const statusLabel = (s) => STATUS_MAP[s]?.label || s
const statusType  = (s) => STATUS_MAP[s]?.type  || 'default'
const fmtTime     = (s) => formatTime(s)

const isPublisher = computed(() => order.value?.passenger_id === userId)
const hasJoined   = computed(() => isPublisher.value)
const canJoin     = computed(() =>
  order.value?.status === 'published' &&
  (order.value?.remaining_seats || 0) > 0 &&
  !isPublisher.value
)
const canCancel = computed(() =>
  isPublisher.value || order.value?.owner_id === userId
)

onMounted(async () => {
  try {
    order.value = await rideApi.getOrderDetail(orderId)
  } catch {
    order.value = null
  } finally {
    loading.value = false
  }
})

async function handleJoin() {
  try {
    await showConfirmDialog({ title: '加入拼车', message: '确认加入本次拼车吗？' })
  } catch { return }
  acting.value = true
  try {
    await rideApi.joinOrder(orderId)
    showSuccessToast('加入成功！')
    order.value = await rideApi.getOrderDetail(orderId)
  } catch (e) {
    showToast(e.message || '操作失败')
  } finally {
    acting.value = false
  }
}

async function handleCancel() {
  const msg = order.value.status !== 'published'
    ? '取消锁单或满员订单将扣除信誉分，确认取消？'
    : '确认取消本订单？'
  try {
    await showConfirmDialog({ title: '取消订单', message: msg })
  } catch { return }
  acting.value = true
  try {
    await rideApi.cancelOrder(orderId)
    showSuccessToast('已取消')
    router.push('/passenger/orders/mine')
  } catch (e) {
    showToast(e.message || '操作失败')
  } finally {
    acting.value = false
  }
}
</script>

<style scoped>
.detail-page { padding-bottom: 32px; }

/* 路线卡 */
.route-card {
  background: linear-gradient(135deg, #0f3fa8 0%, #165DFF 60%, #4f8bff 100%);
  border-radius: 20px; padding: 18px 20px 16px;
  margin-bottom: 12px; position: relative; color: #fff;
}
.route-status-tag { position: absolute; top: 14px; right: 14px; opacity: .9; }
.route-viz {
  display: flex; align-items: center;
  gap: 0; margin-bottom: 12px; padding-top: 6px;
}
.rv-col { min-width: 0; flex-shrink: 0; max-width: 38%; }
.rv-start { text-align: left; }
.rv-end   { text-align: right; }
.rv-label { font-size: 10px; color: rgba(255,255,255,.6); margin-bottom: 3px; letter-spacing: .5px; }
.rv-name  { font-size: 17px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rv-mid {
  flex: 1; display: flex; align-items: center;
  padding: 0 10px; gap: 4px;
}
.rv-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
}
.rv-dot-s { background: #fff; }
.rv-dot-e { background: #fbbf24; }
.rv-line  { flex: 1; height: 1.5px; background: rgba(255,255,255,.35); }
.rv-plane { font-size: 14px; opacity: .85; }
.route-time { font-size: 12px; color: rgba(255,255,255,.75); text-align: center; }

/* 数据条 */
.stats-strip {
  display: flex; background: #fff; border-radius: 16px;
  padding: 14px 0; margin-bottom: 10px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
}
.stat-item  { flex: 1; text-align: center; }
.stat-sep   { width: 1px; background: #f1f5f9; }
.stat-val   { font-size: 20px; font-weight: 800; color: #1e293b; margin-bottom: 2px; }
.stat-val.seats { color: #165DFF; }
.stat-val.price { color: #f97316; }
.stat-key   { font-size: 11px; color: #94a3b8; }

/* 进度条 */
.seat-progress-wrap {
  display: flex; align-items: center; gap: 10px;
  background: #fff; border-radius: 12px;
  padding: 12px 16px; margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(22,93,255,.05);
}
.sp-label { font-size: 12px; color: #64748b; width: 54px; flex-shrink: 0; }
.sp-bar   { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.sp-fill  { height: 100%; background: linear-gradient(90deg, #165DFF, #60a5fa); border-radius: 3px; transition: width .5s ease; }
.sp-pct   { font-size: 12px; font-weight: 600; color: #165DFF; width: 36px; text-align: right; flex-shrink: 0; }

/* 附加信息 */
.info-row-card {
  background: #fff; border-radius: 14px;
  padding: 4px 0; margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(22,93,255,.05);
}
.irc-item {
  display: flex; align-items: center; gap: 12px;
  padding: 11px 16px; border-bottom: 1px solid #f8fafc;
}
.irc-item:last-child { border-bottom: none; }
.irc-icon  { font-size: 16px; width: 22px; text-align: center; }
.irc-label { font-size: 12px; color: #94a3b8; width: 56px; flex-shrink: 0; }
.irc-val   { font-size: 14px; color: #1e293b; font-weight: 500; }

/* 标签 */
.tags-wrap { margin-bottom: 14px; }
.tw-header { font-size: 12px; color: #94a3b8; margin-bottom: 8px; letter-spacing: .5px; }
.tw-chips  { display: flex; flex-wrap: wrap; gap: 8px; }

/* 操作区 */
.action-area { padding-top: 8px; }
.joined-tip {
  display: flex; align-items: center; gap: 6px;
  background: #f0fdf4; border: 1px solid #86efac;
  border-radius: 10px; padding: 10px 14px;
  font-size: 13px; color: #16a34a; margin-bottom: 10px;
}
.jt-icon { font-style: normal; font-weight: 700; }
.cancel-btn { margin-top: 10px; }
.ended-wrap { padding-top: 20px; }
.page-loading { display: flex; justify-content: center; padding: 60px 0; }
</style>
