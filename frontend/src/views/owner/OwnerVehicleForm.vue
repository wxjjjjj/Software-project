<template>
  <div class="vehicle-form-page">
    <section class="page-card">
      <h2>{{ isEditing ? '编辑车辆信息' : '新增车辆并提交认证' }}</h2>
      <p class="hint">
        {{ isEditing ? '修改车辆基础信息后保存。' : '填写车辆信息和审核资料，提交后等待管理员在“车辆审核”中处理。' }}
      </p>

      <van-form @submit="onSubmit" class="vehicle-form">
        <div class="section-title">车辆信息</div>

        <van-field
          v-model.trim="form.plateNo"
          name="plateNo"
          label="车牌号"
          placeholder="例如：粤A12345"
          :rules="[{ required: true, message: '请输入车牌号' }]"
        />

        <van-field
          v-model.trim="form.brand"
          name="brand"
          label="品牌型号"
          placeholder="例如：比亚迪秦"
          :rules="[{ required: true, message: '请输入品牌型号' }]"
        />

        <van-field
          v-model.trim="form.color"
          name="color"
          label="车辆颜色"
          placeholder="例如：白色"
          :rules="[{ required: true, message: '请输入车辆颜色' }]"
        />

        <van-field
          v-model.number="form.seatCapacity"
          name="seatCapacity"
          label="座位数"
          type="digit"
          placeholder="4"
          :rules="[{ validator: seatValidator, message: '座位数请输入 2-9' }]"
        />

        <template v-if="!isEditing">
          <div class="section-title">认证资料</div>
          <p class="cert-hint">车主姓名、身份证号和驾驶证号会优先带入车主认证时填写的信息，你可以在提交前核对。</p>

          <van-field
            v-model.trim="form.ownerName"
            name="ownerName"
            label="车主姓名"
            placeholder="请输入真实姓名"
            :rules="[{ required: true, message: '请填写车主姓名' }]"
          />

          <van-field
            v-model.trim="form.idNo"
            name="idNo"
            label="身份证号"
            placeholder="请输入身份证号"
            :rules="[{ required: true, message: '请填写身份证号' }]"
          />

          <van-field
            v-model.trim="form.driverLicenseNo"
            name="driverLicenseNo"
            label="驾驶证号"
            placeholder="请输入驾驶证号"
            :rules="[{ required: true, message: '请填写驾驶证号' }]"
          />

          <van-field
            v-model.trim="form.vehicleLicenseNo"
            name="vehicleLicenseNo"
            label="行驶证号"
            placeholder="请输入行驶证号"
            :rules="[{ required: true, message: '请填写行驶证号' }]"
          />

          <van-field
            v-model.trim="form.contactPhone"
            name="contactPhone"
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
            placeholder="可填写车辆用途、证件补充说明等"
          />
        </template>

        <div class="form-actions">
          <van-button plain type="default" block @click="goBack">返回车辆主页</van-button>
          <van-button type="primary" native-type="submit" block :loading="submitting">
            {{ isEditing ? '保存修改' : '提交车辆认证申请' }}
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
  deleteOwnerVehicle,
  fetchOwnerVehicles,
  submitVehicleVerifyRequest,
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
  seatCapacity: 4,
  ownerName: '',
  idNo: '',
  driverLicenseNo: '',
  vehicleLicenseNo: '',
  contactPhone: '',
  remark: ''
})

const editVehicleId = computed(() => {
  const id = String(route.params.vehicleId || '').trim()
  return id || null
})

const isEditing = computed(() => editVehicleId.value !== null)

onMounted(async () => {
  await loadVehicles()
  await hydrateCertificationFields()
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

function certStorageKey(userId) {
  return `driver-cert-${userId || 'anonymous'}`
}

function readStoredCertification() {
  const session = readSession()
  try {
    return JSON.parse(localStorage.getItem(certStorageKey(session.userId)) || '{}')
  } catch {
    return {}
  }
}

async function hydrateCertificationFields() {
  const session = readSession()
  const saved = readStoredCertification()

  form.ownerName = saved.real_name || ''
  form.idNo = saved.id_card || ''
  form.driverLicenseNo = saved.driver_license_no || ''
  form.contactPhone = saved.contact_phone || ''

  if (!session.userId || (form.ownerName && form.idNo && form.contactPhone)) {
    return
  }

  try {
    const res = await fetch(`/api/users/profile/${session.userId}`)
    if (!res.ok) return
    const data = await res.json()
    form.ownerName = form.ownerName || data.real_name || ''
    form.idNo = form.idNo || data.id_card || ''
    form.contactPhone = form.contactPhone || data.phone || ''
  } catch {
    // 保持用户可手动填写。
  }
}

function resolveOwnerUserId() {
  const session = readSession()
  const userId = session.userId || session.username
  return userId ? String(userId) : 'dev-user-1'
}

function normalizePlateNoInput(value) {
  return String(value || '')
    .trim()
    .toUpperCase()
    .replace(/[\s\-·•.]/g, '')
}

function normalizeVehicle(item) {
  return {
    vehicleId: String(item.vehicleId ?? item.vehicle_id ?? item.id ?? ''),
    plateNo: normalizePlateNoInput(item.plateNo ?? item.plate_no ?? ''),
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
  const target = vehicles.value.find((item) => String(item.vehicleId) === String(vehicleId))
  if (!target) {
    showNotify({ type: 'warning', message: '未找到要编辑的车辆，请重新选择' })
    router.replace('/me/vehicles')
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
  router.push('/me/vehicles')
}

function vehicleErrorMessage(error) {
  const message = error?.message || ''
  if (message.includes('plate_no already exists')) {
    return '车牌号已存在，请换一个未登记的车牌号'
  }
  if (message.includes('plate_no format is invalid')) {
    return '车牌号格式不正确，请填写类似“粤A12345”或“粤A·12345”的格式'
  }
  if (message.includes('plate_no cannot be empty')) {
    return '请输入车牌号'
  }
  if (message.includes('seat_capacity must be between 2 and 9')) {
    return '座位数请输入 2-9 之间的整数'
  }
  if (message.includes('verification request already pending')) {
    return '该车辆认证申请已在审核中'
  }
  if (message.includes('vehicle already verified')) {
    return '该车辆已认证通过'
  }
  return message || '保存失败'
}

function validateVerificationPayload() {
  if (isEditing.value) return ''
  if (!form.ownerName || !form.idNo || !form.driverLicenseNo || !form.vehicleLicenseNo) {
    return '请填写完整认证资料'
  }
  if (!/^\d{17}[\dXx]$/.test(form.idNo)) {
    return '身份证号格式不正确'
  }
  return ''
}

async function onSubmit() {
  if (submitting.value) {
    return
  }

  const verificationMessage = validateVerificationPayload()
  if (verificationMessage) {
    showNotify({ type: 'warning', message: verificationMessage })
    return
  }

  const payload = {
    plate_no: normalizePlateNoInput(form.plateNo),
    brand: String(form.brand || '').trim(),
    color: String(form.color || '').trim(),
    seat_capacity: Number(form.seatCapacity)
  }

  const duplicate = vehicles.value.some(
    (item) => normalizePlateNoInput(item.plateNo) === payload.plate_no && String(item.vehicleId) !== String(editVehicleId.value)
  )
  if (duplicate) {
    showNotify({ type: 'warning', message: '车牌号已存在' })
    return
  }

  submitting.value = true
  let createdVehicleId = ''
  try {
    if (isEditing.value) {
      await updateOwnerVehicle(editVehicleId.value, payload)
      showNotify({ type: 'success', message: '车辆信息已更新' })
    } else {
      const created = await createOwnerVehicle({
        owner_id: resolveOwnerUserId(),
        ...payload
      })
      const vehicleId = String(created.vehicle_id ?? created.vehicleId ?? '')
      if (!vehicleId) {
        throw new Error('车辆已创建，但未返回车辆ID，无法提交认证申请')
      }
      createdVehicleId = vehicleId
      await submitVehicleVerifyRequest(vehicleId, {
        owner_name: form.ownerName,
        id_no: form.idNo,
        driver_license_no: form.driverLicenseNo,
        vehicle_license_no: form.vehicleLicenseNo,
        contact_phone: form.contactPhone,
        remark: form.remark
      })
      showNotify({ type: 'success', message: '车辆认证申请已提交，请等待管理员审核' })
    }
    router.push('/me/vehicles')
  } catch (error) {
    if (createdVehicleId) {
      try {
        await deleteOwnerVehicle(createdVehicleId)
      } catch {
        // 清理失败时保留后端错误提示，避免遮蔽真正的提交失败原因。
      }
    }
    showNotify({ type: 'danger', message: vehicleErrorMessage(error) })
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

h2 {
  margin: 0;
  color: #172033;
  font-size: 21px;
}

.hint,
.cert-hint {
  margin: 6px 0 12px;
  color: #5f6c80;
  font-size: 13px;
  line-height: 1.6;
}

.vehicle-form {
  display: grid;
  gap: 8px;
}

.section-title {
  margin-top: 6px;
  color: #165dff;
  font-size: 13px;
  font-weight: 800;
}

.cert-hint {
  margin: -2px 0 4px;
  padding: 10px 12px;
  border: 1px solid #dbeafe;
  border-radius: 12px;
  background: #eff6ff;
}

.form-actions {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}
</style>
