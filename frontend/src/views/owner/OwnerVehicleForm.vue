<template>
  <div class="vehicle-form-page">
    <section class="page-card">
      <h2>{{ isEditing ? '车主-编辑车辆信息' : '车主-新增车辆' }}</h2>
      <p class="hint">{{ isEditing ? '修改车辆信息后保存，便于接单时快速选择。' : '请填写车辆基础信息，提交后可在车辆主页继续管理。' }}</p>

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
          <van-button plain type="default" block @click="goBack">返回车辆主页</van-button>
          <van-button type="primary" native-type="submit" block :loading="submitting">
            {{ isEditing ? '保存修改' : '提交新增' }}
          </van-button>
        </div>
      </van-form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showNotify } from 'vant'
import {
  createOwnerVehicle,
  fetchOwnerVehicles,
  updateOwnerVehicle
} from '../../api/ride'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const vehicles = ref([])

const form = reactive({
  plateNo: '',
  brand: '',
  color: '',
  seatCapacity: 4
})

const editVehicleId = computed(() => {
  const id = Number(route.params.vehicleId)
  return Number.isInteger(id) && id > 0 ? id : null
})

const isEditing = computed(() => editVehicleId.value !== null)

onMounted(async () => {
  await loadVehicles()
  if (isEditing.value) {
    hydrateFormByVehicleId(editVehicleId.value)
  }
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
  return 'dev-user-1'
}

function normalizeVehicle(item) {
  return {
    vehicleId: item.vehicleId ?? item.vehicle_id ?? item.id,
    plateNo: String(item.plateNo ?? item.plate_no ?? '').toUpperCase(),
    brand: String(item.brand ?? ''),
    color: String(item.color ?? ''),
    seatCapacity: Number(item.seatCapacity ?? item.seat_capacity ?? 4)
  }
}

async function loadVehicles() {
  try {
    const data = await fetchOwnerVehicles()
    const rawItems = Array.isArray(data.items)
      ? data.items
      : Array.isArray(data.vehicles)
        ? data.vehicles
        : []
    vehicles.value = rawItems.map(normalizeVehicle)
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '车辆信息加载失败' })
  }
}

function hydrateFormByVehicleId(vehicleId) {
  const target = vehicles.value.find((item) => item.vehicleId === vehicleId)
  if (!target) {
    showNotify({ type: 'warning', message: '未找到要编辑的车辆，请重新选择' })
    router.replace('/driver/vehicles')
    return
  }
  form.plateNo = target.plateNo
  form.brand = target.brand
  form.color = target.color
  form.seatCapacity = target.seatCapacity
}

function seatValidator(value) {
  const num = Number(value)
  return Number.isInteger(num) && num >= 2 && num <= 9
}

function goBack() {
  router.push('/driver/vehicles')
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
    (item) => item.plateNo === payload.plate_no && item.vehicleId !== editVehicleId.value
  )
  if (duplicate) {
    showNotify({ type: 'warning', message: '车牌号已存在' })
    return
  }

  submitting.value = true
  try {
    if (isEditing.value) {
      await updateOwnerVehicle(editVehicleId.value, payload)
      showNotify({ type: 'success', message: '车辆信息已更新' })
    } else {
      await createOwnerVehicle({
        owner_id: resolveOwnerUserId(),
        ...payload
      })
      showNotify({ type: 'success', message: '车辆添加成功' })
    }
    router.push('/driver/vehicles')
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '保存失败' })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.vehicle-form-page {
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
</style>