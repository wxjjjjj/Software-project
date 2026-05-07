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
          :rules="[{ validator: plateValidator, message: '请输入规范车牌号，例如 沪A12345 或 沪AD12345' }]"
        />

        <van-field
          v-model.trim="form.brand"
          name="brand"
          label="品牌型号"
          placeholder="输入一个字可联想完整车型"
          @focus="showModelSuggestions = true"
          @blur="hideModelSuggestions"
          :rules="[{ required: true, message: '请输入品牌型号' }]"
        />
        <div v-if="showModelSuggestions && filteredModelSuggestions.length" class="model-suggestions">
          <button
            v-for="model in filteredModelSuggestions"
            :key="model"
            type="button"
            class="model-chip"
            @mousedown.prevent="selectModel(model)"
          >
            {{ model }}
          </button>
        </div>

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
const showModelSuggestions = ref(false)

const PLATE_NO_PATTERN = /^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-HJ-NP-Z0-9]{5,6}$/
const VEHICLE_MODEL_SUGGESTIONS = [
  '比亚迪秦PLUS',
  '比亚迪宋PLUS',
  '比亚迪汉',
  '比亚迪海豹',
  '比亚迪海豚',
  '比亚迪元PLUS',
  '特斯拉Model 3',
  '特斯拉Model Y',
  '丰田凯美瑞',
  '丰田卡罗拉',
  '丰田雷凌',
  '丰田亚洲龙',
  '本田雅阁',
  '本田思域',
  '本田CR-V',
  '本田皓影',
  '大众朗逸',
  '大众帕萨特',
  '大众速腾',
  '大众迈腾',
  '大众途观L',
  '日产轩逸',
  '日产天籁',
  '日产逍客',
  '吉利星瑞',
  '吉利星越L',
  '吉利帝豪',
  '长安逸动',
  '长安CS75 PLUS',
  '哈弗H6',
  '哈弗大狗',
  '奇瑞瑞虎8',
  '奇瑞艾瑞泽8',
  '领克03',
  '领克08',
  '蔚来ET5',
  '蔚来ES6',
  '小鹏G6',
  '理想L6',
  '理想L7',
  '问界M5',
  '问界M7',
  '奔驰C级',
  '奔驰E级',
  '宝马3系',
  '宝马5系',
  '奥迪A4L',
  '奥迪A6L',
  '红旗H5',
  '五菱缤果',
  '五菱宏光MINIEV',
  '小鹏P7',
]

const form = reactive({
  plateNo: '',
  brand: '',
  color: '',
  seatCapacity: 4
})

const editVehicleId = computed(() => {
  const id = String(route.params.vehicleId || '').trim()
  return id || null
})

const isEditing = computed(() => editVehicleId.value !== null)
const filteredModelSuggestions = computed(() => {
  const keyword = form.brand.trim().toLowerCase()
  if (!keyword) {
    return VEHICLE_MODEL_SUGGESTIONS.slice(0, 8)
  }
  return VEHICLE_MODEL_SUGGESTIONS
    .filter((model) => model.toLowerCase().includes(keyword))
    .slice(0, 8)
})

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

function normalizePlateNo(value) {
  return String(value || '').trim().toUpperCase()
}

function plateValidator(value) {
  return PLATE_NO_PATTERN.test(normalizePlateNo(value))
}

function hideModelSuggestions() {
  window.setTimeout(() => {
    showModelSuggestions.value = false
  }, 120)
}

function selectModel(model) {
  form.brand = model
  showModelSuggestions.value = false
}

function goBack() {
  router.push('/me/vehicles')
}

function vehicleErrorMessage(error) {
  const message = error?.message || ''
  if (message.includes('plate_no already exists')) {
    return '车牌号已存在，请换一个未登记的车牌号'
  }
  return message || '保存失败'
}

async function onSubmit() {
  if (submitting.value) {
    return
  }

  const payload = {
    plate_no: normalizePlateNo(form.plateNo),
    brand: form.brand,
    color: form.color,
    seat_capacity: Number(form.seatCapacity)
  }

  if (!plateValidator(payload.plate_no)) {
    showNotify({ type: 'warning', message: '请输入规范车牌号，例如 沪A12345 或 沪AD12345' })
    return
  }

  const duplicate = vehicles.value.some(
    (item) => item.plateNo === payload.plate_no && String(item.vehicleId) !== String(editVehicleId.value)
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
    router.push('/me/vehicles')
  } catch (error) {
    if ((error?.message || '').includes('plate_no already exists')) {
      showNotify({ type: 'danger', message: vehicleErrorMessage(error) })
      return
    }
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

.model-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 0 4px 4px;
}

.model-chip {
  border: 1px solid #dbe6ff;
  border-radius: 999px;
  background: #f4f7ff;
  color: #165dff;
  font-size: 12px;
  padding: 6px 10px;
  cursor: pointer;
}

.model-chip:active {
  background: #e8efff;
}

.form-actions {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}
</style>
