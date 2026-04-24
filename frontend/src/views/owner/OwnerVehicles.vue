<template>
  <div class="vehicle-page">
    <section class="page-card">
      <h2>我的车辆</h2>
      <p class="hint">维护车辆信息，便于接单时快速选择。</p>

      <van-form @submit="onSubmit" class="vehicle-form">
        <van-field
          v-model.trim="form.plateNo"
          name="plateNo"
          label="车牌号"
          placeholder="例如：沪A12345"
          :rules="[{ required: true, message: '请输入车牌号' }]"
        />
        <van-field
          v-model.trim="form.brand"
          name="brand"
          label="品牌"
          placeholder="例如：比亚迪秦"
          :rules="[{ required: true, message: '请输入品牌' }]"
        />
        <van-field
          v-model.trim="form.color"
          name="color"
          label="颜色"
          placeholder="例如：白色"
          :rules="[{ required: true, message: '请输入颜色' }]"
        />
        <van-field
          v-model.number="form.seatCapacity"
          name="seatCapacity"
          label="座位数"
          type="digit"
          placeholder="4"
          :rules="[{ validator: seatValidator, message: '座位数请输入 2-9' }]"
        />

        <div class="form-actions">
          <van-button
            plain
            type="default"
            block
            v-if="isEditing"
            @click="cancelEdit"
          >
            取消编辑
          </van-button>
          <van-button type="primary" native-type="submit" block>
            {{ isEditing ? '保存修改' : '新增车辆' }}
          </van-button>
        </div>
      </van-form>
    </section>

    <section class="page-card list-card">
      <div class="list-header">
        <h3>车辆列表</h3>
        <span class="count">共 {{ vehicles.length }} 辆</span>
      </div>

      <div class="loading-wrap" v-if="loading">
        <van-loading size="24px">加载中...</van-loading>
      </div>

      <van-empty description="还没有车辆，先新增一辆吧" v-else-if="vehicles.length === 0" />

      <div class="vehicle-list" v-else>
        <article class="vehicle-item" v-for="item in vehicles" :key="item.vehicleId">
          <div class="item-main">
            <div class="plate">{{ item.plateNo }}</div>
            <div class="meta">{{ item.brand }} · {{ item.color }} · {{ item.seatCapacity }}座</div>
            <div class="tags">
              <van-tag type="success" v-if="item.verified">已认证</van-tag>
              <van-tag type="warning" v-else>待认证</van-tag>
              <van-tag :type="item.status === 'available' ? 'primary' : 'default'">
                {{ item.status === 'available' ? '可接单' : '已停用' }}
              </van-tag>
            </div>
          </div>

          <div class="item-actions">
            <van-button size="small" type="primary" plain @click="startEdit(item)">编辑</van-button>
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
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { showNotify, showConfirmDialog } from 'vant'
import {
  createOwnerVehicle,
  deleteOwnerVehicle,
  fetchOwnerVehicles,
  updateOwnerVehicle,
  updateOwnerVehicleStatus
} from '../../api/ride'

// 页面状态：列表、编辑态、加载态、提交态。
const vehicles = ref([])
const editingId = ref(null)
const loading = ref(false)
const submitting = ref(false)

// 表单模型：新增与编辑共用。
const form = reactive({
  plateNo: '',
  brand: '',
  color: '',
  seatCapacity: 4
})

const isEditing = computed(() => editingId.value !== null)
const ownerUserId = computed(() => resolveOwnerUserId())

// 页面进入时先拉取车辆列表。
onMounted(() => {
  refreshVehicles()
})

function readSession() {
  try {
    return JSON.parse(localStorage.getItem('session') || '{}')
  } catch {
    return {}
  }
}

function resolveOwnerUserId() {
  const session = readSession()
  const userId = session.userId || session.username
  if (userId) {
    return String(userId)
  }
  // 开发阶段兜底，避免 session 缺失 userId 时页面不可用。
  return 'dev-user-1'
}

function normalizeVehicle(item) {
  // 兼容后端字段差异，统一成页面使用的数据结构。
  return {
    vehicleId: item.vehicleId ?? item.vehicle_id ?? item.id,
    ownerUserId: String(item.ownerUserId ?? item.owner_id ?? item.owner_user_id ?? ownerUserId.value),
    plateNo: String(item.plateNo ?? item.plate_no ?? '').toUpperCase(),
    brand: String(item.brand ?? ''),
    color: String(item.color ?? ''),
    seatCapacity: Number(item.seatCapacity ?? item.seat_capacity ?? 4),
    verified: Boolean(item.verified),
    status: item.status === 'disabled' ? 'disabled' : 'available'
  }
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

function seatValidator(value) {
  // 与后端保持一致：座位数范围 2~9。
  const num = Number(value)
  return Number.isInteger(num) && num >= 2 && num <= 9
}

async function onSubmit() {
  if (submitting.value) {
    return
  }

  const payload = {
    plate_no: form.plateNo.toUpperCase(),
    brand: form.brand,
    color: form.color,
    seat_capacity: Number(form.seatCapacity)
  }

  const duplicate = vehicles.value.some(
    (item) => item.plateNo === payload.plate_no && item.vehicleId !== editingId.value
  )
  if (duplicate) {
    showNotify({ type: 'warning', message: '车牌号已存在' })
    return
  }

  submitting.value = true
  try {
    // 编辑模式与新增模式共用提交入口。
    if (isEditing.value) {
      await updateOwnerVehicle(editingId.value, payload)
      showNotify({ type: 'success', message: '车辆信息已更新' })
    } else {
      await createOwnerVehicle({
        owner_id: ownerUserId.value,
        ...payload
      })
      showNotify({ type: 'success', message: '车辆添加成功' })
    }
    await refreshVehicles()
    resetForm()
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '保存失败' })
  } finally {
    submitting.value = false
  }
}

function startEdit(item) {
  // 把列表项回填到表单中，进入编辑状态。
  editingId.value = item.vehicleId
  form.plateNo = item.plateNo
  form.brand = item.brand
  form.color = item.color
  form.seatCapacity = item.seatCapacity
}

function cancelEdit() {
  resetForm()
}

function resetForm() {
  // 重置表单并退出编辑状态。
  editingId.value = null
  form.plateNo = ''
  form.brand = ''
  form.color = ''
  form.seatCapacity = 4
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

    if (editingId.value === id) {
      resetForm()
    }
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
}

.hint {
  margin: 6px 0 12px;
  color: #5f6c80;
  font-size: 13px;
}

.vehicle-form {
  display: grid;
  gap: 8px;
}

.form-actions {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}

.list-card {
  padding-top: 14px;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.list-header h3 {
  margin: 0;
  font-size: 16px;
}

.count {
  font-size: 12px;
  color: #77849a;
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
  border: 1px solid #e6edf7;
  border-radius: 10px;
  padding: 10px;
  background: linear-gradient(180deg, #ffffff 0%, #f9fbff 100%);
}

.item-main {
  display: grid;
  gap: 6px;
}

.plate {
  font-weight: 600;
  color: #1c2f50;
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
</style>

