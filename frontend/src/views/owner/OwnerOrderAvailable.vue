<template>
  <div class="available-page">

    <!-- 提示横幅 -->
    <div class="tip-banner">
      <span class="tip-icon">ℹ</span>
      <span>以下为招募中的订单，选择车辆后接单，状态将变为已锁单</span>
    </div>

    <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
    <van-empty v-else-if="!orders.length" description="暂无可接订单" />
    <template v-else>
      <div
        v-for="(o, i) in orders"
        :key="o.order_id"
        class="order-card"
        :style="{ animationDelay: `${i * 0.05}s` }"
      >
        <div class="card-head">
          <van-tag type="primary">招募中</van-tag>
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
              <span class="mini-fill" :style="{ width: `${Math.min((o.seats_joined||0)/(o.seats_needed||1)*100,100)}%` }"></span>
            </span>
            剩 {{ o.remaining_seats }} 座
          </span>
        </div>
        <div class="card-tags" v-if="o.tags?.length">
          <span v-for="t in o.tags" :key="t" class="mini-tag">{{ t }}</span>
        </div>
        <div class="card-action">
          <button class="btn-detail" @click="goDetail(o)">详情</button>
          <button class="btn-accept" @click="openAccept(o)">接单 →</button>
        </div>
      </div>
    </template>

    <!-- 接单弹出层 -->
    <van-popup
      v-model:show="showPopup"
      position="bottom"
      round
      :style="{ minHeight: '42%', maxHeight: '80%' }"
    >
      <div class="popup-inner">
        <div class="popup-header">
          <span class="popup-title">选择车辆接单</span>
          <button class="popup-close-btn" @click="showPopup = false">×</button>
        </div>

        <!-- 路线展示 -->
        <div class="popup-route" v-if="currentOrder">
          <span class="nd s"></span>
          <span class="popup-loc">{{ currentOrder.start_loc }}</span>
          <div class="popup-dash"><span></span></div>
          <span class="nd e"></span>
          <span class="popup-loc">{{ currentOrder.end_loc }}</span>
        </div>

        <!-- 车辆列表 -->
        <van-loading v-if="vehicleLoading" class="veh-loading" type="spinner" />
        <van-empty
          v-else-if="!vehicles.length"
          description="暂无可用车辆，请先在账号中添加车辆"
          image-size="80"
        />
        <div v-else class="vehicle-list">
          <div
            v-for="v in vehicles"
            :key="v.vehicle_id"
            class="vehicle-card"
            :class="{ selected: selectedVehicleId === v.vehicle_id }"
            @click="selectedVehicleId = v.vehicle_id"
          >
            <div class="vehicle-check">
              <span v-if="selectedVehicleId === v.vehicle_id" class="check-mark">✓</span>
            </div>
            <div class="vehicle-info">
              <div class="vehicle-plate">{{ v.plate_no }}</div>
              <div class="vehicle-detail">{{ v.brand }} · {{ v.color }} · {{ v.seat_capacity }} 座</div>
            </div>
          </div>
        </div>

        <div class="popup-actions">
          <button class="popup-btn cancel" @click="showPopup = false">取消</button>
          <button
            class="popup-btn confirm"
            :class="{ disabled: !selectedVehicleId || accepting }"
            :disabled="!selectedVehicleId || accepting"
            @click="confirmAccept"
          >{{ accepting ? '接单中…' : '确认接单' }}</button>
        </div>
      </div>
    </van-popup>

  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showSuccessToast } from 'vant'
import { rideApi, formatTime } from '@/api/ride.js'

const router = useRouter()
const orders            = ref([])
const loading           = ref(true)
const showPopup         = ref(false)
const currentOrder      = ref(null)
const vehicles          = ref([])
const vehicleLoading    = ref(false)
const selectedVehicleId = ref('')
const accepting         = ref(false)

const fmtTime = (s) => formatTime(s)

onMounted(() => loadOrders())

function goDetail(o) {
  router.push(`/driver/orders/${o.order_id}`)
}

async function loadOrders() {
  loading.value = true
  try {
    const res = await rideApi.searchOrders({})
    orders.value = res.items || []
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

function normalizeVerified(value) {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value !== 0
  if (typeof value === 'string') {
    const text = value.trim().toLowerCase()
    if (['1', 'true', 'yes', 'y', 'on'].includes(text)) return true
    if (['0', 'false', 'no', 'n', 'off', ''].includes(text)) return false
  }
  return Boolean(value)
}

function normalizeVehicle(item) {
  return {
    vehicle_id: item.vehicle_id ?? item.vehicleId ?? item.id,
    plate_no: item.plate_no ?? item.plateNo ?? '',
    brand: item.brand ?? '',
    color: item.color ?? '',
    seat_capacity: item.seat_capacity ?? item.seatCapacity ?? 4,
    status: item.status === 'disabled' ? 'disabled' : 'available',
    verified: normalizeVerified(item.verified)
  }
}

async function openAccept(o) {
  currentOrder.value = o
  selectedVehicleId.value = ''
  showPopup.value = true

  vehicleLoading.value = true
  try {
    const res = await rideApi.listMyVehicles()
    vehicles.value = (res.items || [])
      .map(normalizeVehicle)
      .filter(v => v.status === 'available' && v.verified)
    if (vehicles.value.length === 1) {
      selectedVehicleId.value = vehicles.value[0].vehicle_id
    }
  } catch {
    vehicles.value = []
  } finally {
    vehicleLoading.value = false
  }
}

async function confirmAccept() {
  if (!selectedVehicleId.value) return
  const selected = vehicles.value.find((item) => item.vehicle_id === selectedVehicleId.value)
  if (!selected || selected.status !== 'available' || !selected.verified) {
    showToast('请选择本人已认证且可用的车辆')
    return
  }
  accepting.value = true
  try {
    await rideApi.acceptOrder(currentOrder.value.order_id, selectedVehicleId.value)
    showSuccessToast('接单成功！')
    showPopup.value = false
    await loadOrders()
  } catch (e) {
    showToast(e.message || '接单失败')
  } finally {
    accepting.value = false
  }
}
</script>

<style scoped>
.available-page { padding-bottom: 24px; }

/* 提示横幅 */
.tip-banner {
  display: flex; align-items: center; gap: 8px;
  background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px;
  padding: 10px 14px; margin-bottom: 12px;
  font-size: 12px; color: #3b82f6;
}
.tip-icon { font-size: 14px; flex-shrink: 0; }

/* 订单卡片 */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.order-card {
  background: #fff; border-radius: 16px;
  padding: 13px 16px; margin-bottom: 10px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
  border-left: 3px solid #165DFF;
  animation: fadeUp .28s ease both;
}

.card-head {
  display: flex; align-items: center; gap: 7px;
  margin-bottom: 10px;
}
.card-price { margin-left: auto; font-size: 16px; font-weight: 800; color: #f97316; }

.card-route {
  display: flex; align-items: center;
  gap: 0; margin-bottom: 9px;
}
.route-node { display: flex; align-items: center; gap: 6px; }
.nd { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.nd.s { background: #165DFF; }
.nd.e { background: #f97316; }
.nd-name { font-size: 15px; font-weight: 700; color: #1e293b; }
.route-dash { flex: 1; padding: 0 8px; }
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

.card-tags { display: flex; gap: 5px; flex-wrap: wrap; margin-bottom: 8px; }
.mini-tag {
  padding: 2px 8px; border-radius: 20px; font-size: 11px;
  background: #f0f5ff; color: #165DFF; border: 1px solid #dce8ff;
}

.card-action { display: flex; justify-content: flex-end; gap: 8px; }
.btn-detail {
  padding: 7px 16px; border-radius: 20px; border: 1px solid #c7d7ff;
  background: #fff; color: #165DFF; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all .15s;
}
.btn-detail:active { transform: scale(.96); background: #f0f5ff; }
.btn-accept {
  padding: 7px 20px; border-radius: 20px; border: none;
  background: #165DFF; color: #fff; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all .15s;
  box-shadow: 0 4px 14px rgba(22,93,255,.35);
}
.btn-accept:hover   { background: #1451d6; }
.btn-accept:active  { transform: scale(.96); }

.page-loading { display: flex; justify-content: center; padding: 40px 0; }

/* 弹出层 */
.popup-inner {
  padding: 20px 16px 32px; display: flex; flex-direction: column; gap: 14px;
}
.popup-header {
  display: flex; justify-content: space-between; align-items: center;
}
.popup-title { font-size: 17px; font-weight: 700; color: #1e293b; }
.popup-close-btn {
  width: 28px; height: 28px; border-radius: 50%;
  border: 1px solid #e2e8f0; background: #f8fafc;
  color: #64748b; font-size: 16px; cursor: pointer; line-height: 26px;
  text-align: center;
}

.popup-route {
  display: flex; align-items: center; gap: 6px;
  background: #f8faff; border: 1px solid #dce8ff; border-radius: 10px;
  padding: 10px 14px;
}
.popup-loc { font-size: 14px; font-weight: 600; color: #1e293b; }
.popup-dash { flex: 1; padding: 0 6px; }
.popup-dash span {
  display: block; height: 1.5px;
  background: repeating-linear-gradient(90deg,#cbd5e1 0,#cbd5e1 4px,transparent 4px,transparent 8px);
}

/* 车辆列表 */
.vehicle-list { display: flex; flex-direction: column; gap: 8px; }
.vehicle-card {
  display: flex; align-items: center; gap: 12px;
  background: #f8fafc; border: 2px solid #e2e8f0;
  border-radius: 12px; padding: 12px 14px;
  cursor: pointer; transition: all .15s;
}
.vehicle-card.selected { border-color: #165DFF; background: #f0f5ff; }
.vehicle-check {
  width: 22px; height: 22px; border-radius: 50%;
  border: 2px solid #e2e8f0; background: #fff; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  transition: all .15s;
}
.vehicle-card.selected .vehicle-check { border-color: #165DFF; background: #165DFF; }
.check-mark { color: #fff; font-size: 13px; font-weight: 700; }
.vehicle-info { flex: 1; }
.vehicle-plate { font-size: 16px; font-weight: 700; color: #1e293b; }
.vehicle-detail { font-size: 12px; color: #64748b; margin-top: 2px; }

.veh-loading { display: flex; justify-content: center; padding: 20px 0; }

/* 操作按钮 */
.popup-actions { display: flex; gap: 10px; }
.popup-btn {
  flex: 1; padding: 11px 0; border-radius: 24px;
  font-size: 14px; font-weight: 600; cursor: pointer;
  transition: all .15s; border: none;
}
.popup-btn.cancel {
  background: #f1f5f9; color: #64748b;
}
.popup-btn.cancel:active { background: #e2e8f0; }
.popup-btn.confirm {
  background: #165DFF; color: #fff;
  box-shadow: 0 4px 14px rgba(22,93,255,.35);
}
.popup-btn.confirm:active { transform: scale(.97); }
.popup-btn.disabled {
  background: #cbd5e1; color: #fff; box-shadow: none; cursor: not-allowed;
}
</style>
