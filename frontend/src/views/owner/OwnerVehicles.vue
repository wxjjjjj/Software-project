<template>
  <div class="vehicle-page">
    <div class="stat-banner">
      <div class="sb-item">
        <div class="sb-num">{{ totalCount }}</div>
        <div class="sb-label">我的车辆</div>
      </div>
      <div class="sb-divider"></div>
      <div class="sb-item">
        <div class="sb-num">{{ verifiedCount }}</div>
        <div class="sb-label">已认证</div>
      </div>
      <div class="sb-divider"></div>
      <div class="sb-item" @click="goPendingVerify">
        <div class="sb-num orange">{{ pendingCount }}</div>
        <div class="sb-label">待认证</div>
        <div class="sb-pulse" v-if="pendingCount > 0"></div>
      </div>
    </div>

    <div class="quick-actions">
      <button type="button" class="qa-card qa-fire" @click="goCreateVehicle">
        <div class="qa-icon">🚗</div>
        <div class="qa-info">
          <div class="qa-title">新增车辆</div>
          <div class="qa-sub">快速录入车辆信息</div>
        </div>
        <span class="qa-arrow">›</span>
      </button>
      <button type="button" class="qa-card qa-notes" @click="goPendingVerify">
        <div class="qa-icon">🪪</div>
        <div class="qa-info">
          <div class="qa-title">车辆认证</div>
          <div class="qa-sub">{{ verifyActionHint }}</div>
        </div>
        <span class="qa-badge" v-if="pendingCount > 0">{{ pendingCount }}</span>
        <span class="qa-arrow">›</span>
      </button>
    </div>

    <div class="section-label">
      <span class="section-dot"></span>
      车辆列表
      <span class="section-count">共 {{ vehicles.length }} 辆</span>
    </div>

    <section class="page-card list-card">
      <div class="loading-wrap" v-if="loading">
        <van-loading size="24px">加载中...</van-loading>
      </div>

      <van-empty description="还没有车辆，先新增一辆吧" v-else-if="vehicles.length === 0" />

      <div class="vehicle-list" v-else>
        <article
          class="vehicle-item"
          :class="{
            'v-verified': item.verified,
            'v-pending': !item.verified,
            'v-disabled': item.status === 'disabled'
          }"
          v-for="item in vehicles"
          :key="item.vehicleId"
        >
          <div class="item-main">
            <div class="title-row">
              <div class="plate">{{ item.plateNo }}</div>
              <span class="seat-badge">{{ item.seatCapacity }}座</span>
            </div>
            <div class="meta">{{ item.brand }} · {{ item.color }}</div>
            <div class="tags">
              <van-tag :type="vehicleVerifyTagType(item)">{{ vehicleVerifyText(item) }}</van-tag>
              <van-tag :type="vehicleServiceTagType(item)">
                {{ vehicleServiceText(item) }}
              </van-tag>
            </div>
          </div>

          <div class="item-actions">
            <van-button size="small" type="primary" plain @click="startEdit(item)">编辑</van-button>
            <van-button
              v-if="!item.verified"
              size="small"
              type="success"
              plain
              :disabled="isVehicleVerifyPending(item)"
              @click="goVerify(item.vehicleId)"
            >
              {{ isVehicleVerifyPending(item) ? '审核中' : '去认证' }}
            </van-button>
            <van-button
              size="small"
              :type="item.status === 'available' ? 'warning' : 'success'"
              plain
              @click="toggleStatus(item)"
            >
              {{ item.status === 'available' ? '停用' : '启用' }}
            </van-button>
            <van-button size="small" type="danger" plain @click="removeVehicle(item.vehicleId)">删除</van-button>
          </div>
        </article>
      </div>
    </section>

    <van-action-sheet
      v-model:show="showVerifySheet"
      title="选择要认证的车辆"
      :actions="verifySheetActions"
      cancel-text="取消"
      close-on-click-action
      @select="onVerifyActionSelect"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showNotify, showConfirmDialog } from 'vant'
import {
  deleteOwnerVehicle,
  fetchOwnerVehicles,
  updateOwnerVehicleStatus
} from '../../api/ride'

// 页面状态：列表与加载态。
const vehicles = ref([])
const loading = ref(false)
const showVerifySheet = ref(false)
const router = useRouter()
const totalCount = computed(() => vehicles.value.length)
const verifiedCount = computed(() => vehicles.value.filter((item) => item.verified).length)
const pendingCount = computed(() => vehicles.value.filter((item) => !item.verified && !isVehicleVerifyPending(item)).length)
const reviewPendingCount = computed(() => vehicles.value.filter(isVehicleVerifyPending).length)
const pendingVehicles = computed(() => vehicles.value.filter((item) => !item.verified))
const verifyActionHint = computed(() => {
  if (pendingCount.value > 0) {
    return '还有 ' + pendingCount.value + ' 辆待认证'
  }
  if (reviewPendingCount.value > 0) {
    return '还有 ' + reviewPendingCount.value + ' 辆审核中'
  }
  return '全部车辆已认证'
})
const verifySheetActions = computed(() => pendingVehicles.value.map((item) => ({
  name: isVehicleVerifyPending(item)
    ? `${item.plateNo} · 该车辆认证正在审核`
    : `${item.plateNo} · ${item.brand} · ${item.color}`,
  vehicleId: item.vehicleId,
  disabled: isVehicleVerifyPending(item)
})))

// 页面进入时先拉取车辆列表。
onMounted(() => {
  refreshVehicles()
})

function normalizeVerified(value) {
  // 避免把字符串 "0" / "false" 当成真值，导致前端误显示已认证。
  if (typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    return value !== 0
  }
  if (typeof value === 'string') {
    const text = value.trim().toLowerCase()
    if (['1', 'true', 'yes', 'y', 'on'].includes(text)) {
      return true
    }
    if (['0', 'false', 'no', 'n', 'off', ''].includes(text)) {
      return false
    }
  }
  return Boolean(value)
}

function normalizeVehicle(item) {
  // 兼容后端字段差异，统一成页面使用的数据结构。
  return {
    vehicleId: item.vehicleId ?? item.vehicle_id ?? item.id,
    plateNo: String(item.plateNo ?? item.plate_no ?? '').toUpperCase(),
    brand: String(item.brand ?? ''),
    color: String(item.color ?? ''),
    seatCapacity: Number(item.seatCapacity ?? item.seat_capacity ?? 4),
    verified: normalizeVerified(item.verified),
    verifyStatus: String(item.verifyStatus ?? item.verify_status ?? '').toLowerCase(),
    status: item.status === 'disabled' ? 'disabled' : 'available'
  }
}

function isVehicleVerifyPending(item) {
  return item.verifyStatus === 'pending'
}

function vehicleVerifyText(item) {
  if (item.verified || item.verifyStatus === 'approved') {
    return '已认证'
  }
  return isVehicleVerifyPending(item) ? '审核中' : '待认证'
}

function vehicleVerifyTagType(item) {
  if (item.verified || item.verifyStatus === 'approved') {
    return 'success'
  }
  return isVehicleVerifyPending(item) ? 'primary' : 'warning'
}

function vehicleServiceText(item) {
  if (item.status === 'disabled') {
    return '已停用'
  }
  return item.verified ? '可接单' : '待认证不可接单'
}

function vehicleServiceTagType(item) {
  if (item.status === 'disabled') {
    return 'default'
  }
  return item.verified ? 'primary' : 'warning'
}

async function refreshVehicles() {
  // 拉取最新数据；后端会根据开关决定走 Mock 还是数据库。
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
    showNotify({ type: 'danger', message: error.message || '车辆列表加载失败' })
  } finally {
    loading.value = false
  }
}

function startEdit(item) {
  router.push(`/me/vehicles/${item.vehicleId}/edit`)
}

function goCreateVehicle() {
  router.push('/me/vehicles/create')
}

async function goPendingVerify() {
  if (pendingVehicles.value.length === 0) {
    const message = reviewPendingCount.value > 0
      ? '该车辆认证正在审核'
      : '当前没有待认证车辆'
    showNotify({ type: reviewPendingCount.value > 0 ? 'warning' : 'success', message })
    return
  }

  if (pendingVehicles.value.length === 1 && isVehicleVerifyPending(pendingVehicles.value[0])) {
    showNotify({ type: 'warning', message: '该车辆认证正在审核' })
    return
  }

  const submittableVehicles = pendingVehicles.value.filter((item) => !isVehicleVerifyPending(item))
  if (submittableVehicles.length === 1 && pendingVehicles.value.length === 1) {
    goVerify(submittableVehicles[0].vehicleId)
    return
  }

  showVerifySheet.value = true
}

function onVerifyActionSelect(action) {
  if (action?.disabled) {
    showNotify({ type: 'warning', message: '该车辆认证正在审核' })
    return
  }
  if (action?.vehicleId) {
    goVerify(action.vehicleId)
  }
}

function goVerify(vehicleId) {
  router.push(`/me/vehicles/${vehicleId}/verify`)
}

async function toggleStatus(item) {
  // 车辆状态在可用和停用之间切换。
  const nextStatus = item.status === 'available' ? 'disabled' : 'available'
  try {
    await updateOwnerVehicleStatus(item.vehicleId, nextStatus)
    showNotify({ type: 'success', message: nextStatus === 'available' ? '车辆已启用' : '车辆已停用' })
    await refreshVehicles()
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '状态更新失败' })
  }
}

async function removeVehicle(id) {
  try {
    // 删除前确认，防止误操作。
    await showConfirmDialog({
      title: '删除车辆',
      message: '删除后无法恢复，是否继续？'
    })

    await deleteOwnerVehicle(id)
    await refreshVehicles()
    showNotify({ type: 'success', message: '已删除车辆' })
  } catch (error) {
    if (error?.message) {
      showNotify({ type: 'danger', message: error.message })
    }
  }
}
</script>

<style scoped>
.vehicle-page {
  display: grid;
  gap: 12px;
  padding-bottom: 24px;
}

/* 统计横幅 */
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
  position: relative;
  cursor: pointer;
}

.sb-num {
  font-size: 34px;
  font-weight: 900;
  line-height: 1;
  margin-bottom: 4px;
}

.sb-num.orange {
  color: #fbbf24;
}

.sb-label {
  font-size: 12px;
  opacity: 0.75;
}

.sb-divider {
  width: 1px;
  background: rgba(255, 255, 255, 0.2);
  height: 42px;
  align-self: center;
}

.sb-pulse {
  position: absolute;
  top: 3px;
  right: calc(50% - 24px);
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #4ade80;
  box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4);
  }
  70% {
    box-shadow: 0 0 0 8px rgba(74, 222, 128, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
  }
}

/* 快捷入口 */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.qa-card {
  width: 100%;
  border: none;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  border-radius: 16px;
  text-decoration: none;
  position: relative;
  transition: transform 0.14s;
  text-align: left;
}

.qa-card:active {
  transform: scale(0.97);
}

.qa-fire {
  background: #fff7ed;
}

.qa-notes {
  background: #f0fdf4;
}

.qa-icon {
  font-size: 24px;
}

.qa-title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
}

.qa-sub {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.qa-badge {
  margin-left: auto;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 10px;
}

.qa-arrow {
  font-size: 20px;
  color: #cbd5e1;
  margin-left: auto;
}

.qa-badge + .qa-arrow {
  margin-left: 6px;
}

/* 段落标签 */
.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
  padding: 8px 2px 0;
}

.section-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #165dff;
  flex-shrink: 0;
}

.section-count {
  margin-left: auto;
  font-size: 12px;
  color: #7b8aa1;
  font-weight: 500;
}

.list-card {
  padding-top: 12px;
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
  background: #fff;
  border-radius: 16px;
  padding: 13px 16px;
  box-shadow: 0 2px 12px rgba(22, 93, 255, 0.07);
  border-left: 3px solid #e2e8f0;
}

.item-main {
  display: grid;
  gap: 6px;
}

.vehicle-item.v-verified {
  border-left-color: #10b981;
}

.vehicle-item.v-pending {
  border-left-color: #f97316;
}

.vehicle-item.v-disabled {
  border-left-color: #94a3b8;
  opacity: 0.86;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.plate {
  font-weight: 700;
  color: #1e293b;
  font-size: 15px;
}

.seat-badge {
  font-size: 12px;
  line-height: 1;
  color: #165dff;
  background: #eff6ff;
  border: 1px solid #dbeafe;
  border-radius: 999px;
  padding: 4px 8px;
}

.meta {
  font-size: 13px;
  color: #4d5f7a;
}

.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.item-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.item-actions :deep(.van-button) {
  border-radius: 10px;
}

@media (max-width: 420px) {
  .item-actions :deep(.van-button) {
    flex: 1 1 calc(50% - 8px);
  }

  .sb-num {
    font-size: 28px;
  }
}
</style>

