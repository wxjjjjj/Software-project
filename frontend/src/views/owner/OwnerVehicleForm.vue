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
  // 比亚迪系
  '比亚迪秦PLUS',
  '比亚迪秦L',
  '比亚迪汉',
  '比亚迪海豹',
  '比亚迪海豹06 DM-i',
  '比亚迪海豹07 DM-i',
  '比亚迪海豚',
  '比亚迪海鸥',
  '比亚迪元PLUS',
  '比亚迪元UP',
  '比亚迪宋PLUS',
  '比亚迪宋L',
  '比亚迪宋L DM-i',
  '比亚迪宋Pro DM-i',
  '比亚迪唐DM-i',
  '比亚迪驱逐舰05',
  '比亚迪护卫舰07',
  '比亚迪海狮05 DM-i',
  '比亚迪海狮06',
  '比亚迪海狮07 EV',
  '比亚迪夏',

  // 腾势 / 方程豹 / 仰望
  '腾势D9',
  '腾势N7',
  '腾势N8',
  '腾势N9',
  '腾势Z9GT',
  '方程豹豹5',
  '方程豹豹8',
  '方程豹钛3',
  '方程豹钛7',
  '仰望U7',
  '仰望U8',
  '仰望U9',

  // 特斯拉 / 小米 / 华为系
  '特斯拉Model 3',
  '特斯拉Model Y',
  '特斯拉Model S',
  '特斯拉Model X',
  '小米SU7',
  '小米YU7',
  '问界M5',
  '问界M7',
  '问界M8',
  '问界M9',
  '智界S7',
  '智界R7',
  '享界S9',
  '尊界S800',

  // 新势力
  '理想L6',
  '理想L7',
  '理想L8',
  '理想L9',
  '理想MEGA',
  '蔚来ET5',
  '蔚来ET5T',
  '蔚来ET7',
  '蔚来ES6',
  '蔚来ES8',
  '蔚来EC6',
  '蔚来EC7',
  '乐道L60',
  '乐道L90',
  '小鹏P7',
  '小鹏P7i',
  '小鹏P5',
  '小鹏G6',
  '小鹏G9',
  '小鹏X9',
  '小鹏MONA M03',
  '零跑T03',
  '零跑B10',
  '零跑B11',
  '零跑C01',
  '零跑C10',
  '零跑C11',
  '零跑C16',
  '哪吒L',
  '哪吒S',
  '哪吒X',

  // 吉利 / 领克 / 极氪
  '吉利星愿',
  '吉利星瑞',
  '吉利星越L',
  '吉利银河E5',
  '吉利银河L6',
  '吉利银河L7',
  '吉利银河E8',
  '吉利缤越',
  '吉利博越L',
  '吉利帝豪',
  '吉利熊猫',
  '领克03',
  '领克06',
  '领克07',
  '领克08',
  '领克09',
  '领克Z10',
  '极氪001',
  '极氪007',
  '极氪7X',
  '极氪009',
  '极氪X',
  '极氪MIX',

  // 长安 / 深蓝 / 阿维塔
  '长安逸动',
  '长安UNI-V',
  '长安UNI-K',
  '长安UNI-Z',
  '长安CS55 PLUS',
  '长安CS75 PLUS',
  '长安CS95',
  '长安启源A05',
  '长安启源A07',
  '长安启源Q05',
  '深蓝SL03',
  '深蓝S05',
  '深蓝S07',
  '深蓝G318',
  '阿维塔07',
  '阿维塔11',
  '阿维塔12',

  // 奇瑞 / 捷途 / 星途
  '奇瑞艾瑞泽8',
  '奇瑞风云A8',
  '奇瑞风云T9',
  '奇瑞瑞虎7 PLUS',
  '奇瑞瑞虎8',
  '奇瑞瑞虎8 PLUS',
  '奇瑞瑞虎9',
  '捷途旅行者',
  '捷途山海T2',
  '捷途X70 PLUS',
  '捷途X90 PLUS',
  '星途瑶光',
  '星途凌云',
  '星途揽月',
  '星纪元ES',
  '星纪元ET',

  // 长城系
  '哈弗H6',
  '哈弗大狗',
  '哈弗二代大狗',
  '哈弗猛龙',
  '哈弗枭龙MAX',
  '哈弗赤兔',
  '坦克300',
  '坦克400 Hi4-T',
  '坦克500 Hi4-T',
  '坦克700 Hi4-T',
  '魏牌蓝山',
  '魏牌高山',
  '欧拉好猫',
  '欧拉闪电猫',

  // 红旗 / 广汽 / 上汽 / 五菱
  '红旗H5',
  '红旗H6',
  '红旗H9',
  '红旗HS3',
  '红旗HS5',
  '红旗HS7',
  '红旗E-QM5',
  '广汽传祺影豹',
  '广汽传祺影酷',
  '广汽传祺GS3',
  '广汽传祺GS4',
  '广汽传祺GS8',
  '广汽传祺M6',
  '广汽传祺M8',
  '广汽埃安AION S',
  '广汽埃安AION Y',
  '广汽埃安AION V',
  '广汽埃安AION LX',
  '昊铂GT',
  '昊铂HT',
  '上汽荣威i5',
  '上汽荣威D7',
  '上汽荣威RX5',
  '上汽荣威RX9',
  'MG5',
  'MG7',
  'MG4 EV',
  'MG Cyberster',
  '智己L6',
  '智己L7',
  '智己LS6',
  '智己LS7',
  '五菱宏光MINIEV',
  '五菱缤果',
  '五菱星光',
  '五菱星光S',
  '五菱凯捷',
  '宝骏云朵',
  '宝骏悦也',
  '宝骏510',

  // 大众 / 丰田 / 本田 / 日产
  '大众朗逸',
  '大众帕萨特',
  '大众速腾',
  '大众迈腾',
  '大众途观L',
  '大众探岳',
  '大众探歌',
  '大众高尔夫',
  '大众ID.3',
  '大众ID.4 X',
  '大众ID.4 CROZZ',
  '大众ID.6 X',
  '大众ID.6 CROZZ',
  '丰田凯美瑞',
  '丰田卡罗拉',
  '丰田雷凌',
  '丰田亚洲龙',
  '丰田RAV4荣放',
  '丰田威兰达',
  '丰田锋兰达',
  '丰田汉兰达',
  '丰田赛那',
  '丰田格瑞维亚',
  '丰田普拉多',
  '丰田皇冠陆放',
  '丰田bZ3',
  '丰田bZ4X',
  '本田雅阁',
  '本田思域',
  '本田型格',
  '本田飞度',
  '本田CR-V',
  '本田皓影',
  '本田HR-V',
  '本田XR-V',
  '本田冠道',
  '本田奥德赛',
  '本田艾力绅',
  '日产轩逸',
  '日产天籁',
  '日产逍客',
  '日产奇骏',
  '日产探陆',
  '日产骐达',
  '日产ARIYA艾睿雅',

  // 美系 / 韩系 / 其他合资
  '别克GL8',
  '别克君威',
  '别克君越',
  '别克威朗',
  '别克昂科威',
  '别克昂科旗',
  '别克E5',
  '别克E4',
  '雪佛兰科鲁泽',
  '雪佛兰迈锐宝XL',
  '雪佛兰探界者',
  '福特蒙迪欧',
  '福特锐界L',
  '福特探险者',
  '福特电马',
  '马自达3昂克赛拉',
  '马自达CX-5',
  '马自达CX-50行也',
  '现代伊兰特',
  '现代索纳塔',
  '现代途胜L',
  '起亚K3',
  '起亚K5',
  '起亚狮铂拓界',

  // 豪华品牌
  '奔驰A级',
  '奔驰C级',
  '奔驰E级',
  '奔驰GLA',
  '奔驰GLB',
  '奔驰GLC',
  '奔驰GLE',
  '奔驰EQE',
  '宝马1系',
  '宝马3系',
  '宝马5系',
  '宝马X1',
  '宝马X3',
  '宝马X5',
  '宝马i3',
  '宝马iX3',
  '宝马i5',
  '奥迪A3',
  '奥迪A4L',
  '奥迪A6L',
  '奥迪Q3',
  '奥迪Q5L',
  '奥迪Q7',
  '奥迪Q4 e-tron',
  '奥迪Q5 e-tron',
  '雷克萨斯ES',
  '雷克萨斯RX',
  '雷克萨斯NX',
  '雷克萨斯UX',
  '沃尔沃S60',
  '沃尔沃S90',
  '沃尔沃XC40',
  '沃尔沃XC60',
  '沃尔沃XC90',
  '凯迪拉克CT4',
  '凯迪拉克CT5',
  '凯迪拉克CT6',
  '凯迪拉克XT4',
  '凯迪拉克XT5',
  '凯迪拉克XT6',
  '林肯冒险家',
  '林肯航海家',
  '保时捷Macan',
  '保时捷Cayenne',
  '保时捷Panamera',
  '保时捷Taycan',
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
