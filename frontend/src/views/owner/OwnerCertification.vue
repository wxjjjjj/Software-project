<template>
  <div class="certification-container">
    <div class="page-card">
      <h2>车主认证中心</h2>

      <!-- 0. 加载状态 -->
      <div v-if="status === 'loading'" class="status-box">
        <div class="loader"></div>
        <p>正在同步账号状态...</p>
      </div>

      <!-- 情况 1：未申请 - 显示认证表单 -->
      <div v-else-if="status === 'unapplied'" class="auth-form">
        <p class="tips">请填写您的车辆信息，管理员将在 1-3 个工作日内完成审核。</p>
        <div class="form-item">
          <label>车牌号码</label>
          <input v-model="form.license_plate" placeholder="如：沪A88888" />
        </div>
        <div class="form-item">
          <label>车辆型号</label>
          <input v-model="form.car_model" placeholder="如：特斯拉 Model 3" />
        </div>
        <div class="form-item">
          <label>车身颜色</label>
          <input v-model="form.car_color" placeholder="如：黑色" />
        </div>
        <button class="submit-btn" @click="handleApply" :disabled="loading">
          {{ loading ? '提交中...' : '提交认证申请' }}
        </button>
      </div>

      <!-- 情况 2：审核中 - 显示等待提示 -->
      <div v-else-if="status === 'pending'" class="status-box pending">
        <div class="icon"></div>
        <h3>认证审核中</h3>
        <p>您的资料已提交，请耐心等待管理员审核。</p>
        <button class="refresh-btn-small" @click="fetchStatus">刷新进度</button>
      </div>

      <!-- 情况 3：已通过 - 变身为“个人中心”，展示资料和名下车辆 -->
      <div v-else-if="status === 'approved' || status === 'active'" class="status-box success">
        <div class="icon-success"></div>
        <h3>认证已通过</h3>
        
        <div class="user-profile-section">
          <h4>个人信息</h4>
          <div class="info-row">
            <span>拼车人信誉：</span>
            <b :class="{ 'text-red': profile.passenger_score < 60 }">{{ profile.passenger_score }} 分</b>
          </div>
          <div class="info-row">
            <span>车主信誉：</span>
            <b :class="{ 'text-red': profile.driver_score < 60 }">{{ profile.driver_score }} 分</b>
          </div>
          <div class="info-row">
            <span>账号状态：</span>
            <span class="status-tag active">{{ profile.account_status === 'active' ? '正常' : '限制中' }}</span>
          </div>
        </div>

        <div class="vehicle-list-section">
          <h4>名下车辆信息</h4>
          <div v-if="vehicles.length === 0" class="no-data">未查得关联车辆</div>
          <div v-for="car in vehicles" :key="car.id" class="car-card">
            <div class="car-main">
              <span class="plate">{{ car.license_plate }}</span>
              <span class="model">{{ car.car_model }} ({{ car.car_color }})</span>
            </div>
          </div>
        </div>

        <button class="home-btn" @click="handleEnterDriverHome">进入车主首页</button>
      </div>

      <!-- 情况 4：被封禁 -->
      <div v-else-if="status === 'banned'" class="status-box banned">
        <div class="icon"></div>
        <h3>车主权限已封禁</h3>
        <p>因信誉分过低或违规，您的车主身份已被停用。</p>
        <p class="score-tip">当前车主评分：{{ profile.driver_score }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const status = ref('loading')
const loading = ref(false)
const profile = ref({})  // 存储个人资料（信誉分等）
const vehicles = ref([]) // 存储名下车辆

const form = ref({
  license_plate: '',
  car_model: '',
  car_color: ''
})

// 获取数据：包括状态、资料和车辆列表
const fetchStatus = async () => {
  const session = JSON.parse(localStorage.getItem('session') || '{}')
  if (!session.userId) {
    router.push('/login')
    return
  }
  
  try {
    // 1. 获取个人详细资料（含分数和认证状态）
    const resProfile = await fetch(`/api/users/profile/${session.userId}`)
    if (resProfile.ok) {
      const data = await resProfile.json()
      profile.value = data
      status.value = data.driver_status || 'unapplied'

      // 同步本地 Session 权限
      if ((status.value === 'approved' || status.value === 'active') && !session.ownerVerified) {
        session.ownerVerified = true
        session.role = 'driver'
        localStorage.setItem('session', JSON.stringify(session))
      }
    }

    // 2. 如果是车主或审核中，获取车辆列表
    if (status.value !== 'unapplied') {
      const resCars = await fetch(`/api/users/driver/cars/${session.userId}`)
      if (resCars.ok) {
        vehicles.value = await resCars.json()
      }
    }
  } catch (err) {
    console.error('获取认证状态失败', err)
    status.value = 'unapplied'
  }
}

// 提交申请
const handleApply = async () => {
  if (!form.value.license_plate || !form.value.car_model) {
    alert('请填写完整的车辆信息')
    return
  }

  const session = JSON.parse(localStorage.getItem('session') || '{}')
  loading.value = true
  
  try {
    const res = await fetch(`/api/users/driver/apply/${session.userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })

    if (res.ok) {
      alert('申请提交成功！请等待管理员审核')
      status.value = 'pending'
      fetchStatus() // 刷新列表
    } else {
      alert('提交失败，请检查内容')
    }
  } catch (err) {
    alert('网络错误')
  } finally {
    loading.value = false
  }
}

// 进入车主首页（带状态刷新）
const handleEnterDriverHome = () => {
  router.push('/driver/home').then(() => {
    window.location.reload()
  })
}

onMounted(fetchStatus)
</script>

<style scoped>
.certification-container { padding: 20px; display: flex; justify-content: center; background: #f8f9fa; min-height: 80vh; }
.page-card { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); width: 100%; max-width: 450px; }
h2 { text-align: center; margin-bottom: 25px; color: #2c3e50; }

.tips { color: #856404; background: #fff3cd; border: 1px solid #ffeeba; padding: 12px; border-radius: 8px; font-size: 13px; margin-bottom: 20px; }
.form-item { margin-bottom: 15px; }
.form-item label { display: block; margin-bottom: 6px; font-weight: bold; font-size: 14px; color: #34495e; }
.form-item input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; }

.submit-btn { width: 100%; padding: 14px; background: #1890ff; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; margin-top: 10px; }

/* 状态展示区样式 */
.status-box { text-align: center; padding: 30px 0; }
.icon { font-size: 50px; margin-bottom: 15px; }
.icon-success { font-size: 50px; color: #52c41a; margin-bottom: 10px; }

/* 个人信息与车辆列表 */
.user-profile-section, .vehicle-list-section {
  text-align: left; background: #fcfcfc; border: 1px solid #f0f0f0; padding: 15px; border-radius: 10px; margin-top: 15px;
}
h4 { margin: 0 0 10px 0; color: #7f8c8d; font-size: 13px; text-transform: uppercase; }
.info-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
.car-card { background: white; border: 1px solid #eee; padding: 10px; border-radius: 6px; margin-bottom: 8px; }
.plate { font-weight: bold; color: #333; margin-right: 10px; }
.model { color: #666; font-size: 13px; }

.text-red { color: #f5222d; }
.status-tag.active { background: #e6f7ff; color: #1890ff; padding: 2px 8px; border-radius: 4px; font-size: 12px; }

.home-btn { margin-top: 25px; width: 100%; padding: 12px; background: #52c41a; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }
.refresh-btn-small { background: none; border: 1px solid #ddd; color: #999; padding: 4px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; margin-top: 10px; }
</style>