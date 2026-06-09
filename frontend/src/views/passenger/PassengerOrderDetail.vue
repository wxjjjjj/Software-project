<template>
  <div class="detail-page">
    <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />

    <template v-else-if="order">
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

      <div class="seat-progress-wrap">
        <div class="sp-label">座位占用</div>
        <div class="sp-bar">
          <div
            class="sp-fill"
            :style="{ width: `${Math.min((order.seats_joined / order.seats_needed) * 100, 100)}%` }"
          ></div>
        </div>
        <div class="sp-pct">{{ Math.round((order.seats_joined / order.seats_needed) * 100) }}%</div>
      </div>

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

      <div class="passenger-card" v-if="acceptedDriverProfile">
        <div class="pc-header">
          <span>接单车主</span>
          <span class="pc-count">1 人</span>
        </div>
        <RouterLink class="passenger-row" :to="driverProfileRoute">
          <div class="avatar avatar-owner">{{ avatarText(acceptedDriverProfile.userId) }}</div>
          <div class="passenger-main">
            <div class="passenger-name">
              {{ displayName(acceptedDriverProfile.userId) }}
              <van-tag type="warning" plain>车主</van-tag>
              <van-tag v-if="acceptedDriverProfile.userId === String(userId)" type="success" plain>我</van-tag>
            </div>
            <div class="passenger-meta">
              {{ driverMetaText }}
            </div>
          </div>
        </RouterLink>
      </div>

      <div class="tags-wrap" v-if="order.tags?.length">
        <div class="tw-header">订单标签</div>
        <div class="tw-chips">
          <span v-for="tag in order.tags" :key="tag" class="tag-chip" style="cursor: default">{{ tag }}</span>
        </div>
      </div>

      <div class="passenger-card">
        <div class="pc-header">
          <span>参与乘客</span>
          <span class="pc-count">{{ passengers.length }} 人</span>
        </div>
        <div v-if="passengers.length" class="passenger-list">
          <RouterLink
            v-for="passenger in passengers"
            :key="passenger.record_id || passenger.passenger_id"
            class="passenger-row"
            :to="buildUserProfileRoute(passenger.passenger_id, 'passenger')"
          >
            <div class="avatar">{{ avatarText(passenger.passenger_id) }}</div>
            <div class="passenger-main">
              <div class="passenger-name">
                {{ displayName(passenger.passenger_id) }}
                <van-tag v-if="String(passenger.passenger_id) === String(order.passenger_id)" type="primary" plain>发起人</van-tag>
                <van-tag v-if="String(passenger.passenger_id) === String(userId)" type="success" plain>我</van-tag>
              </div>
              <div class="passenger-meta">
                {{ fmtTime(passenger.join_time) }} 加入 · {{ payStatusLabel(passenger.pay_status) }}
              </div>
            </div>
          </RouterLink>
        </div>
        <van-empty v-else image-size="56" description="暂无参与乘客" />
      </div>

      <div class="action-area" v-if="order.status !== 'completed'">
        <van-button
          v-if="canJoin"
          round
          block
          type="primary"
          size="large"
          :loading="acting"
          loading-text="加入中…"
          @click="handleJoin"
        >
          加入拼车
        </van-button>

        <div class="joined-tip" v-if="hasJoined && order.status === 'published'">
          <span class="jt-icon">✓</span>
          你已加入，等待车主接单
        </div>

        <van-button
          v-if="canCancel"
          round
          block
          plain
          type="danger"
          :loading="acting"
          loading-text="取消中…"
          class="cancel-btn"
          @click="handleCancel"
        >
          取消订单{{ order.status !== 'published' ? '（将扣除信誉分）' : '' }}
        </van-button>

        <div v-if="showOpsActions" class="ops-actions">
          <van-button
            v-if="!isDriverView && order.status === 'locked'"
            round
            block
            type="primary"
            @click="router.push(`/passenger/payment/${orderId}`)"
          >
            去支付
          </van-button>
          <van-button
            v-if="canOpenOrderChat"
            round
            block
            plain
            type="default"
            :style="{ marginTop: isDriverView || order.status !== 'locked' ? '0' : '8px' }"
            @click="router.push(`/${isDriverView ? 'driver' : 'passenger'}/chat/${orderId}`)"
          >
            进入聊天
          </van-button>
        </div>
      </div>

      <div class="ended-wrap" v-if="order.status === 'completed'">
        <van-empty image="success" description="行程已完成" />
      </div>
    </template>

    <van-empty v-else description="订单不存在" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { fetchUserProfiles, getCachedUsername } from '@/api/account.js'
import { STATUS_MAP, formatTime, getUserId, rideApi } from '@/api/ride.js'

const route = useRoute()
const router = useRouter()
const orderId = route.params.id

const order = ref(null)
const loading = ref(true)
const acting = ref(false)
const userNames = ref({})
const userId = getUserId()

const statusLabel = (status) => STATUS_MAP[status]?.label || status
const statusType = (status) => STATUS_MAP[status]?.type || 'default'
const fmtTime = (value) => formatTime(value)

const isDriverView = computed(() => route.path.startsWith('/driver/'))
const viewerRole = computed(() => (isDriverView.value ? 'driver' : 'passenger'))
const isPublisher = computed(() => String(order.value?.passenger_id || '') === String(userId))
const passengers = computed(() => order.value?.passengers || [])
const hasJoined = computed(() =>
  isPublisher.value || passengers.value.some((passenger) => String(passenger.passenger_id || '') === String(userId))
)
const canJoin = computed(() =>
  !isDriverView.value &&
  order.value?.status === 'published' &&
  Number(order.value?.remaining_seats || 0) > 0 &&
  !hasJoined.value
)
const canCancel = computed(() =>
  !isDriverView.value &&
  (isPublisher.value || String(order.value?.owner_id || '') === String(userId))
)

const hasAcceptedDriver = computed(() => {
  if (!order.value) return false
  const ownerId = String(order.value.owner_id || '')
  if (!ownerId) return false
  return order.value.status === 'locked' || Boolean(order.value.locked_time) || Boolean(order.value.vehicle_id)
})

const showOpsActions = computed(() => {
  if (!order.value) return false
  if (order.value.status === 'completed') return false

  if (isDriverView.value) {
    return String(order.value.owner_id || '') === String(userId) || hasAcceptedDriver.value
  }

  return hasJoined.value
})

const canOpenOrderChat = computed(() => {
  if (!order.value) return false
  if (!showOpsActions.value) return false

  const targetIds = new Set()
  const addTarget = (value) => {
    const id = String(value || '')
    if (!id || id === String(userId)) return
    targetIds.add(id)
  }

  if (hasAcceptedDriver.value) {
    addTarget(order.value.owner_id)
  }

  for (const passenger of passengers.value) {
    addTarget(passenger.passenger_id)
  }

  return targetIds.size > 0
})

const acceptedDriverProfile = computed(() => {
  if (!hasAcceptedDriver.value) return null
  const ownerId = String(order.value?.owner_id || '')
  if (!ownerId) return null
  return {
    userId: ownerId,
    vehicleId: order.value?.vehicle_id,
    lockedTime: order.value?.locked_time,
  }
})

const driverProfileRoute = computed(() => {
  if (!acceptedDriverProfile.value) return '/me/profile'
  return buildUserProfileRoute(acceptedDriverProfile.value.userId, 'driver')
})

const driverMetaText = computed(() => {
  if (!acceptedDriverProfile.value) return ''

  const parts = []
  if (acceptedDriverProfile.value.lockedTime) {
    parts.push(`${fmtTime(acceptedDriverProfile.value.lockedTime)} 接单`)
  }
  if (acceptedDriverProfile.value.vehicleId) {
    parts.push(`车辆 ${acceptedDriverProfile.value.vehicleId}`)
  }
  return parts.join(' · ') || '已接单车主'
})

function buildUserProfileRoute(targetUserId, targetRole) {
  return {
    path: `/users/${targetUserId}`,
    query: {
      orderId: orderId,
      viewer: viewerRole.value,
      target: targetRole,
      username: displayName(targetUserId),
    },
  }
}

function displayName(id) {
  const key = String(id || '').trim()
  return userNames.value[key] || getCachedUsername(key)
}

function avatarText(id) {
  return displayName(id).slice(0, 1).toUpperCase()
}

function payStatusLabel(status) {
  return ({
    pending: '待支付',
    paid: '已支付',
    refunded: '已退款',
  })[status] || status || '未知'
}

onMounted(async () => {
  try {
    order.value = await rideApi.getOrderDetail(orderId)
    await syncUserNames()
  } catch {
    order.value = null
  } finally {
    loading.value = false
  }
})

async function syncUserNames() {
  if (!order.value) return

  const ids = new Set()
  const addId = (value) => {
    const id = String(value || '').trim()
    if (id) ids.add(id)
  }

  addId(order.value.passenger_id)
  addId(order.value.owner_id)
  for (const passenger of passengers.value) {
    addId(passenger.passenger_id)
  }

  const profiles = await fetchUserProfiles(Array.from(ids))
  userNames.value = Object.entries(profiles).reduce((map, [id, profile]) => {
    map[id] = profile.username
    return map
  }, { ...userNames.value })
}

async function handleJoin() {
  try {
    await showConfirmDialog({
      title: '加入拼车',
      message: '确认加入本次拼车吗？',
    })
  } catch {
    return
  }

  acting.value = true
  try {
    await rideApi.joinOrder(orderId)
    showSuccessToast('加入成功！')
    order.value = await rideApi.getOrderDetail(orderId)
    await syncUserNames()
  } catch (error) {
    showToast(error.message || '操作失败')
  } finally {
    acting.value = false
  }
}

async function handleCancel() {
  const message = order.value.status !== 'published'
    ? '取消锁单或满员订单将扣除信誉分，确认取消？'
    : '确认取消本订单？'

  try {
    await showConfirmDialog({
      title: '取消订单',
      message,
    })
  } catch {
    return
  }

  acting.value = true
  try {
    await rideApi.cancelOrder(orderId)
    showSuccessToast('已取消')
    router.push('/passenger/orders/mine')
  } catch (error) {
    showToast(error.message || '操作失败')
  } finally {
    acting.value = false
  }
}
</script>

<style scoped>
.detail-page { padding-bottom: 32px; }

.route-card {
  background: linear-gradient(135deg, #0f3fa8 0%, #165DFF 60%, #4f8bff 100%);
  border-radius: 20px;
  padding: 18px 20px 16px;
  margin-bottom: 12px;
  position: relative;
  color: #fff;
}

.route-status-tag { position: absolute; top: 14px; right: 14px; opacity: 0.9; }

.route-viz {
  display: flex;
  align-items: center;
  gap: 0;
  margin-bottom: 12px;
  padding-top: 6px;
}

.rv-col { min-width: 0; flex-shrink: 0; max-width: 38%; }
.rv-start { text-align: left; }
.rv-end { text-align: right; }
.rv-label { font-size: 10px; color: rgba(255, 255, 255, 0.6); margin-bottom: 3px; letter-spacing: 0.5px; }
.rv-name { font-size: 17px; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.rv-mid {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 10px;
  gap: 4px;
}

.rv-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.rv-dot-s { background: #fff; }
.rv-dot-e { background: #fbbf24; }
.rv-line { flex: 1; height: 1.5px; background: rgba(255, 255, 255, 0.35); }
.rv-plane { font-size: 14px; opacity: 0.85; }
.route-time { font-size: 12px; color: rgba(255, 255, 255, 0.75); text-align: center; }

.stats-strip {
  display: flex;
  background: #fff;
  border-radius: 16px;
  padding: 14px 0;
  margin-bottom: 10px;
  box-shadow: 0 2px 14px rgba(22, 93, 255, 0.07);
}

.stat-item { flex: 1; text-align: center; }
.stat-sep { width: 1px; background: #f1f5f9; }
.stat-val { font-size: 20px; font-weight: 800; color: #1e293b; margin-bottom: 2px; }
.stat-val.seats { color: #165DFF; }
.stat-val.price { color: #f97316; }
.stat-key { font-size: 11px; color: #94a3b8; }

.seat-progress-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(22, 93, 255, 0.05);
}

.sp-label { font-size: 12px; color: #64748b; width: 54px; flex-shrink: 0; }
.sp-bar { flex: 1; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.sp-fill { height: 100%; background: linear-gradient(90deg, #165DFF, #60a5fa); border-radius: 3px; transition: width 0.5s ease; }
.sp-pct { font-size: 12px; font-weight: 600; color: #165DFF; width: 36px; text-align: right; flex-shrink: 0; }

.info-row-card {
  background: #fff;
  border-radius: 14px;
  padding: 4px 0;
  margin-bottom: 10px;
  box-shadow: 0 2px 10px rgba(22, 93, 255, 0.05);
}

.irc-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 16px;
  border-bottom: 1px solid #f8fafc;
}

.irc-item:last-child { border-bottom: none; }
.irc-icon { font-size: 16px; width: 22px; text-align: center; }
.irc-label { font-size: 12px; color: #94a3b8; width: 56px; flex-shrink: 0; }
.irc-val { font-size: 14px; color: #1e293b; font-weight: 500; }

.tags-wrap { margin-bottom: 14px; }
.tw-header { font-size: 12px; color: #94a3b8; margin-bottom: 8px; letter-spacing: 0.5px; }
.tw-chips { display: flex; flex-wrap: wrap; gap: 8px; }

.action-area { padding-top: 8px; }

.joined-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 10px;
  padding: 10px 14px;
  font-size: 13px;
  color: #16a34a;
  margin-bottom: 10px;
}

.jt-icon { font-style: normal; font-weight: 700; }
.cancel-btn { margin-top: 10px; }
.ops-actions { padding-top: 8px; }
.ended-wrap { padding-top: 20px; }
.page-loading { display: flex; justify-content: center; padding: 60px 0; }

.passenger-card {
  background: #fff;
  border-radius: 14px;
  padding: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 10px rgba(22, 93, 255, 0.05);
}

.pc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.pc-count {
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}

.passenger-list {
  display: grid;
  gap: 8px;
}

.passenger-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding: 9px 8px;
  border-radius: 10px;
  background: #f8fbff;
  text-decoration: none;
}

.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  background: #e7efff;
  color: #165DFF;
  font-size: 14px;
  font-weight: 800;
}

.avatar-owner {
  background: #fff7ed;
  color: #ea580c;
}

.passenger-main {
  min-width: 0;
  flex: 1;
}

.passenger-name {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  color: #1e293b;
  font-size: 13px;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.passenger-meta {
  margin-top: 2px;
  color: #64748b;
  font-size: 11px;
}
</style>
