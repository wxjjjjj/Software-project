<template>
  <div class="verify-page">
    <section class="page-card">
      <h2>车主-车辆认证资料提交</h2>
      <p class="hint">请填写真实信息，管理员审核通过后车辆将显示为已认证。</p>

      <van-form @submit="onSubmit" class="verify-form">
        <van-field
          v-model.number="form.vehicleId"
          name="vehicleId"
          label="车辆ID"
          type="digit"
          placeholder="请输入需要认证的车辆ID"
          :readonly="readonlyVehicleId"
          :rules="[{ validator: vehicleIdValidator, message: '请输入合法车辆ID' }]"
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

        <van-button type="primary" native-type="submit" block :loading="submitting">
          提交认证申请
        </van-button>

        <van-button plain type="default" block @click="goBackToVehicles">
          返回车辆主页
        </van-button>
      </van-form>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showNotify } from 'vant'
import { submitVehicleVerifyRequest } from '../../api/ride'

const route = useRoute()
const router = useRouter()
const submitting = ref(false)

const routeVehicleId = computed(() => {
  const id = Number(route.params.vehicleId)
  return Number.isInteger(id) && id > 0 ? id : null
})

const readonlyVehicleId = computed(() => routeVehicleId.value !== null)

const form = reactive({
  vehicleId: routeVehicleId.value ?? null,
  owner_name: '',
  id_no: '',
  driver_license_no: '',
  vehicle_license_no: '',
  contact_phone: '',
  remark: ''
})

function vehicleIdValidator(value) {
  const num = Number(value)
  return Number.isInteger(num) && num > 0
}

async function onSubmit() {
  const vehicleId = Number(form.vehicleId)
  if (!vehicleIdValidator(vehicleId)) {
    showNotify({ type: 'warning', message: '请输入合法车辆ID' })
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
    router.push('/driver/vehicles')
  } catch (error) {
    showNotify({ type: 'danger', message: error.message || '提交失败' })
  } finally {
    submitting.value = false
  }
}

function goBackToVehicles() {
  router.push('/driver/vehicles')
}
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
</style>

