<template>
  <div class="vehicle-page">
    <section class="stat-banner">
      <div class="sb-item">
        <div class="sb-num">{{ totalCount }}</div>
        <div class="sb-label">车辆申请</div>
      </div>
      <div class="sb-divider"></div>
      <div class="sb-item">
        <div class="sb-num">{{ approvedCount }}</div>
        <div class="sb-label">已通过</div>
      </div>
      <div class="sb-divider"></div>
      <div class="sb-item">
        <div class="sb-num orange">{{ pendingCount }}</div>
        <div class="sb-label">审核中</div>
      </div>
    </section>

    <button type="button" class="apply-card" @click="goCreateVehicle">
      <div>
        <div class="apply-title">提交新的车辆认证申请</div>
        <div class="apply-sub">填写车辆信息与行驶证号，提交后等待管理员审核。</div>
      </div>
      <span class="apply-arrow">›</span>
    </button>

    <section class="page-card list-card">
      <div class="section-head">
        <div>
          <h3>我的车辆认证</h3>
          <p>申请审核中可以撤回；审核通过后车辆将用于车主接单。</p>
        </div>
        <van-button size="small" plain type="primary" :loading="loading" @click="refreshVehicles">
          刷新
        </van-button>
      </div>

      <div class="loading-wrap" v-if="loading">
        <van-loading size="24px">加载中...</van-loading>
      </div>

      <van-empty description="还没有车辆认证申请" v-else-if="vehicles.length === 0" />

      <div class="vehicle-list" v-else>
        <article
          v-for="item in vehicles"
          :key="item.vehicleId"
          class="vehicle-item"
          :class="`is-${statusTone(item)}`"
        >
          <div class="vehicle-main">
            <div class="title-row">
              <div class="plate">{{ item.plateNo || '未命名车辆' }}</div>
              <van-tag :type="statusTagType(item)">{{ statusText(item) }}</van-tag>
            </div>

            <div class="meta">{{ item.brand || '未填写型号' }} · {{ item.color || '未填写颜色' }} · {{ item.seatCapacity }}座</div>
            <div class="hint">{{ statusHint(item) }}</div>
          </div>

          <div v-if="isPending(item)" class="actions">
            <van-button
              size="small"
              type="danger"
              plain
              :loading="withdrawingId === item.pendingRequestId"
              @click="withdrawRequest(item)"
            >
              撤回申请
            </van-button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showConfirmDialog, showNotify } from 'vant'
import { fetchOwnerVehicles, withdrawVehicleVerifyRequest } from '../../api/ride'

const router = useRouter()
const vehicles = ref([])
const loading = ref(false)
const withdrawingId = ref('')

const totalCount = computed(() => vehicles.value.length)
const approvedCount = computed(() => vehicles.value.filter((item) => item.verified || item.verifyStatus === 'approved').length)
const pendingCount = computed(() => vehicles.value.filter(isPending).length)

onMounted(refreshVehicles)

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
    vehicleId: String(item.vehicleId ?? item.vehicle_id ?? item.id ?? ''),
    pendingRequestId: String(item.pendingRequestId ?? item.pending_request_id ?? ''),
    plateNo: String(item.plateNo ?? item.plate_no ?? '').toUpperCase(),
    brand: String(item.brand ?? ''),
    color: String(item.color ?? ''),
    seatCapacity: Number(item.seatCapacity ?? item.seat_capacity ?? 4),
    verified: normalizeVerified(item.verified),
    verifyStatus: String(item.verifyStatus ?? item.verify_status ?? '').toLowerCase(),
    status: item.status === 'disabled' ? 'disabled' : 'available'
  }
}

function isPending(item) {
  return item.verifyStatus === 'pending'
}

function statusText(item) {
  if (item.verified || item.verifyStatus === 'approved') return '已通过'
  if (isPending(item)) return '审核中'
  if (item.verifyStatus === 'rejected') return '已驳回'
  return '未提交'
}

function statusHint(item) {
  if (item.verified || item.verifyStatus === 'approved') {
    return '车辆已认证，可用于车主接单。'
  }
  if (isPending(item)) {
    return '管理员审核前可以撤回申请，撤回后该车辆记录会同步移除。'
  }
  if (item.verifyStatus === 'rejected') {
    return '申请已被驳回，请重新提交新的车辆认证申请。'
  }
  return '该车辆没有有效认证申请，建议重新提交新的车辆认证申请。'
}

function statusTagType(item) {
  if (item.verified || item.verifyStatus === 'approved') return 'success'
  if (isPending(item)) return 'primary'
  if (item.verifyStatus === 'rejected') return 'danger'
  return 'warning'
}

function statusTone(item) {
  if (item.verified || item.verifyStatus === 'approved') return 'approved'
  if (isPending(item)) return 'pending'
  if (item.verifyStatus === 'rejected') return 'rejected'
  return 'draft'
}

async function refreshVehicles() {
  loading.value = true
  try {
    const data = await fetchOwnerVehicles()
    const rawItems = Array.isArray(data.items)
      ? data.items
      : Array.isArray(data.vehicles)
        ? data.vehicles
        : []
    vehicles.value = rawItems.map(normalizeVehicle)
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '车辆申请加载失败' })
  } finally {
    loading.value = false
  }
}

function goCreateVehicle() {
  router.push('/me/vehicles/create')
}

async function withdrawRequest(item) {
  if (!item.pendingRequestId) {
    showNotify({ type: 'warning', message: '未找到可撤回的申请' })
    return
  }

  try {
    await showConfirmDialog({
      title: '撤回车辆认证申请',
      message: '撤回后该车辆申请会从管理员审核列表中移除，是否继续？'
    })
  } catch {
    return
  }

  withdrawingId.value = item.pendingRequestId
  try {
    await withdrawVehicleVerifyRequest(item.pendingRequestId)
    showNotify({ type: 'success', message: '车辆认证申请已撤回' })
    await refreshVehicles()
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '撤回失败' })
  } finally {
    withdrawingId.value = ''
  }
}
</script>

<style scoped>
.vehicle-page {
  display: grid;
  gap: 12px;
  padding-bottom: 24px;
}

.stat-banner {
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #0f3fa8 0%, #165dff 60%, #4f8bff 100%);
  border-radius: 20px;
  padding: 20px 0;
  color: #fff;
}

.sb-item {
  flex: 1;
  text-align: center;
}

.sb-num {
  font-size: 32px;
  font-weight: 900;
  line-height: 1;
  margin-bottom: 4px;
}

.sb-num.orange {
  color: #fbbf24;
}

.sb-label {
  font-size: 12px;
  opacity: 0.78;
}

.sb-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.22);
}

.apply-card {
  width: 100%;
  border: 1px solid #dce8ff;
  border-radius: 18px;
  padding: 15px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  background: #f8fbff;
  text-align: left;
  box-shadow: 0 4px 16px rgba(22, 93, 255, 0.08);
}

.apply-title {
  color: #172033;
  font-size: 15px;
  font-weight: 800;
}

.apply-sub {
  margin-top: 4px;
  color: #65758b;
  font-size: 12px;
  line-height: 1.5;
}

.apply-arrow {
  color: #9bb4d8;
  font-size: 22px;
}

.list-card {
  display: grid;
  gap: 12px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.section-head h3 {
  margin: 0;
  color: #172033;
  font-size: 17px;
}

.section-head p {
  margin: 5px 0 0;
  color: #65758b;
  font-size: 12px;
  line-height: 1.5;
}

.loading-wrap {
  display: grid;
  place-items: center;
  min-height: 120px;
}

.vehicle-list {
  display: grid;
  gap: 10px;
}

.vehicle-item {
  border: 1px solid #e6eefb;
  border-left: 4px solid #cbd5e1;
  border-radius: 16px;
  padding: 14px;
  background: #fff;
  box-shadow: 0 3px 14px rgba(22, 93, 255, 0.06);
}

.vehicle-item.is-approved {
  border-left-color: #10b981;
}

.vehicle-item.is-pending {
  border-left-color: #165dff;
}

.vehicle-item.is-rejected {
  border-left-color: #ef4444;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.plate {
  color: #172033;
  font-size: 16px;
  font-weight: 900;
}

.meta {
  margin-top: 6px;
  color: #4d5f7a;
  font-size: 13px;
}

.hint {
  margin-top: 8px;
  color: #7b8aa1;
  font-size: 12px;
  line-height: 1.5;
}

.actions {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}
</style>
