<template>
  <div class="verify-page">
    <section class="page-card">
      <h2>车主-车辆认证资料提交</h2>
      <p class="hint">请填写真实信息，管理员审核通过后车辆将显示为已认证。</p>

      <van-form @submit="onSubmit" class="verify-form">
        <van-notice-bar
          v-if="currentVehiclePending"
          class="pending-notice"
          type="warning"
          text="该车辆认证正在审核，暂时不能重复提交。"
        />

        <van-field
          v-model.trim="form.vehicleId"
          name="vehicleId"
          label="车辆ID"
          placeholder="请输入需要认证的车辆ID"
          :readonly="readonlyVehicleId"
          :rules="[{ validator: vehicleIdValidator, message: '请输入合法车辆ID' }]"
        />

        <van-field
          :model-value="displayPlateNo"
          name="plateNo"
          label="车牌号"
          placeholder="将根据车辆ID自动读取"
          readonly
        />

        <van-field
          v-model.trim="form.owner_name"
          name="owner_name"
          label="车主姓名"
          placeholder="请输入真实姓名"
          :rules="[{ required: true, message: '请填写车主姓名' }]"
        />

        <van-field
          v-model.trim="form.id_no"
          name="id_no"
          label="身份证号"
          placeholder="请输入身份证号"
          :rules="[{ required: true, message: '请填写身份证号' }]"
        />

        <van-field
          v-model.trim="form.driver_license_no"
          name="driver_license_no"
          label="驾驶证号"
          placeholder="请输入驾驶证号"
          :rules="[{ required: true, message: '请填写驾驶证号' }]"
        />

        <van-field
          v-model.trim="form.vehicle_license_no"
          name="vehicle_license_no"
          label="行驶证号"
          placeholder="请输入行驶证号"
          :rules="[{ required: true, message: '请填写行驶证号' }]"
        />

        <van-field
          v-model.trim="form.contact_phone"
          name="contact_phone"
          label="联系电话"
          type="tel"
          placeholder="用于审核联系，可选"
        />

        <van-field
          v-model.trim="form.remark"
          name="remark"
          label="补充说明"
          type="textarea"
          rows="2"
          autosize
          maxlength="200"
          show-word-limit
          placeholder="可填写车辆用途等补充信息"
        />

        <van-button
          type="primary"
          native-type="submit"
          block
          :loading="submitting"
          :disabled="currentVehiclePending"
        >
          {{ currentVehiclePending ? '该车辆认证正在审核' : '提交认证申请' }}
        </van-button>

        <van-button plain type="default" block @click="goBackToVehicles">
          返回车辆主页
        </van-button>
      </van-form>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showNotify } from 'vant'
import { fetchOwnerVehicles, submitVehicleVerifyRequest } from '../../api/ride'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const vehicles = ref([])

const routeVehicleId = computed(() => String(route.params.vehicleId || '').trim())
const readonlyVehicleId = computed(() => routeVehicleId.value.length > 0)

const form = reactive({
  vehicleId: routeVehicleId.value,
  owner_name: '',
  id_no: '',
  driver_license_no: '',
  vehicle_license_no: '',
  contact_phone: '',
  remark: ''
})

const currentVehicle = computed(() => {
  const currentId = String(form.vehicleId || '').trim()
  return vehicles.value.find((item) => String(item.vehicleId) === currentId) || null
})

const currentVehiclePending = computed(() => currentVehicle.value?.verifyStatus === 'pending')
const displayPlateNo = computed(() => currentVehicle.value?.plateNo || '')

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
    plateNo: String(item.plateNo ?? item.plate_no ?? '').toUpperCase(),
    verified: normalizeVerified(item.verified),
    verifyStatus: String(item.verifyStatus ?? item.verify_status ?? '').toLowerCase()
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
  } catch {
    vehicles.value = []
  }
}

function vehicleIdValidator(value) {
  return String(value || '').trim().length > 0
}

async function onSubmit() {
  const vehicleId = String(form.vehicleId || '').trim()
  if (!vehicleIdValidator(vehicleId)) {
    showNotify({ type: 'warning', message: '请输入合法车辆ID' })
    return
  }

  if (currentVehiclePending.value) {
    showNotify({ type: 'warning', message: '该车辆认证正在审核' })
    return
  }

  if (submitting.value) {
    return
  }

  submitting.value = true
  try {
    await submitVehicleVerifyRequest(vehicleId, {
      owner_name: form.owner_name,
      id_no: form.id_no,
      driver_license_no: form.driver_license_no,
      vehicle_license_no: form.vehicle_license_no,
      contact_phone: form.contact_phone,
      remark: form.remark
    })
    showNotify({ type: 'success', message: '认证资料已提交，请等待审核' })
    router.push('/me/vehicles')
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '提交失败' })
  } finally {
    submitting.value = false
  }
}

function goBackToVehicles() {
  router.push('/me/vehicles')
}

onMounted(loadVehicles)
</script>

<style scoped>
.verify-page {
  display: grid;
  gap: 12px;
}

.hint {
  margin: 6px 0 12px;
  color: #5f6c80;
  font-size: 13px;
}

.verify-form {
  display: grid;
  gap: 8px;
}

.pending-notice {
  margin-bottom: 2px;
  border-radius: 12px;
  overflow: hidden;
}
</style>
