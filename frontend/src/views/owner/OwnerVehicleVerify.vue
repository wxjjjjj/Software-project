<template>
  <div class="verify-page">
    <section class="page-card verify-card">
      <div class="form-head">
        <div class="head-copy">
          <div class="eyebrow">车辆认证</div>
          <h2>认证资料提交</h2>
          <p class="hint">请填写真实信息，管理员审核通过后车辆将显示为已认证。</p>
        </div>
        <div class="head-badge">审核</div>
      </div>

      <van-form @submit="onSubmit" class="verify-form">
        <van-notice-bar
          v-if="currentVehiclePending"
          class="pending-notice"
          type="warning"
          text="该车辆认证正在审核，无法提交新的认证"
        />

        <div class="form-fields">
          <van-field
            :model-value="displayPlateNo"
            name="plateNo"
            label="车牌号"
            placeholder="正在读取车辆信息"
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
        </div>

        <div class="form-actions">
          <van-button
            class="action-button action-button--primary"
            type="primary"
            native-type="submit"
            block
            :loading="submitting"
            :disabled="currentVehiclePending"
          >
            {{ currentVehiclePending ? '该车辆认证正在审核' : '提交认证申请' }}
          </van-button>

          <van-button class="action-button action-button--ghost" plain type="default" block @click="goBackToVehicles">
            返回车辆主页
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
import { fetchOwnerVehicles, submitVehicleVerifyRequest } from '../../api/ride'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)
const vehicles = ref([])

const routeVehicleId = computed(() => {
  const id = String(route.params.vehicleId || '').trim()
  return id || null
})

const form = reactive({
  vehicleId: routeVehicleId.value ?? null,
  owner_name: '',
  id_no: '',
  driver_license_no: '',
  vehicle_license_no: '',
  contact_phone: '',
  remark: ''
})

const currentVehicle = computed(() => vehicles.value.find((item) => String(item.vehicleId) === String(form.vehicleId)))
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
    vehicleId: item.vehicleId ?? item.vehicle_id ?? item.id,
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
  padding-bottom: 24px;
}

.verify-card {
  position: relative;
  overflow: hidden;
  padding: 0;
  border-color: #dbeafe;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 44%);
}

.verify-card::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 4px;
  background: linear-gradient(90deg, #165dff 0%, #10b981 100%);
}

.form-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 22px 16px 16px;
}

.head-copy {
  min-width: 0;
  display: grid;
  gap: 6px;
}

.eyebrow {
  color: #165dff;
  font-size: 12px;
  font-weight: 800;
}

h2 {
  margin: 0;
  color: #172033;
  font-size: 25px;
  line-height: 1.16;
}

.hint {
  margin: 0;
  color: #52657d;
  font-size: 13px;
  line-height: 1.65;
}

.head-badge {
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  min-height: 30px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #bbf7d0;
  background: #ecfdf5;
  color: #047857;
  font-size: 12px;
  font-weight: 800;
}

.verify-form {
  display: grid;
  gap: 14px;
  padding: 0 16px 16px;
}

.pending-notice {
  border-radius: 12px;
  overflow: hidden;
}

.form-fields {
  overflow: hidden;
  border: 1px solid #edf2fb;
  border-radius: 14px;
  background: #fff;
}

.form-fields :deep(.van-cell) {
  align-items: center;
  padding: 14px 14px;
  background: transparent;
}

.form-fields :deep(.van-field__label) {
  width: 82px;
  color: #334155;
  font-weight: 700;
}

.form-fields :deep(.van-field__control) {
  color: #172033;
  font-weight: 600;
}

.form-fields :deep(.van-field__control::placeholder) {
  color: #a8b6c8;
  font-weight: 500;
}

.form-fields :deep(.van-field__word-limit) {
  color: #64748b;
  font-weight: 600;
}

.form-actions {
  display: grid;
  gap: 8px;
}

.action-button {
  height: 44px;
  border-radius: 12px;
  font-weight: 700;
}

.action-button--primary {
  box-shadow: 0 8px 18px rgba(22, 93, 255, 0.18);
}

.action-button--ghost {
  color: #33506f;
  background: #f8fbff;
  border-color: #dbeafe;
}

@media (max-width: 360px) {
  .form-head {
    flex-direction: column;
  }

  .head-badge {
    align-self: flex-start;
  }
}
</style>
