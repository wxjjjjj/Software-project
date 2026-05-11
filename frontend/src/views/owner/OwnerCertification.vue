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
          <label>品牌型号</label>
          <input v-model="form.car_model" placeholder="如：特斯拉 Model 3" />
        </div>
        <div class="form-item">
          <label>车身颜色</label>
          <input v-model="form.car_color" placeholder="如：黑色" />
        </div>
        <div class="form-item">
          <label>座位数</label>
          <input v-model="form.seats" placeholder="如：5" />
        </div>
        <button class="submit-btn" @click="handleApply" :disabled="loading">
          {{ loading ? '提交中...' : '提交认证申请' }}
        </button>
      </div>

      <!-- 情况 2：审核中 - 显示等待提示 -->
      <div v-else-if="status === 'pending'" class="status-box pending">
        <div class="icon">⏳</div>
        <h3>认证审核中</h3>
        <p>您的资料已提交，请耐心等待管理员审核。</p>
        <button class="refresh-btn-small" @click="fetchStatus">刷新进度</button>
      </div>

      <!-- 情况 3：已通过 - 变身为“个人中心”，展示资料和名下车辆 -->
      <div v-else-if="status === 'approved' || status === 'active'" class="status-box success">
        <div class="icon-success">✔️</div>
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
        <div class="icon">🚫</div>
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
  car_color: '',
  seats: ''
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
  const session = JSON.parse(localStorage.getItem('session') || '{}')
  
  // 更新状态
  session.role = 'driver'
  session.ownerVerified = true
  localStorage.setItem('session', JSON.stringify(session))
  
  // 跳转即可，不需要 reload()
  // Layout.vue 会在路由跳转后检测到 session 变化并更新菜单
  router.push('/driver/home')
}

onMounted(fetchStatus)
</script>

<style scoped>
/* 容器及卡片框架 */
.certification-container { padding: 20px; display: flex; justify-content: center; background: #f8f9fa; min-height: 80vh; }
.page-card { background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); width: 100%; max-width: 450px; }

/* 统一大标题样式 */
h2 { text-align: center; margin-bottom: 25px; font-size: 20px; font-weight: 700; color: #1e293b; }

/* 统一状态标题 */
h3 { font-size: 16px; font-weight: 800; color: #1e293b; margin-bottom: 10px; }

/* 统一模块小标题 */
h4 { margin: 0 0 10px 0; color: #94a3b8; font-size: 13px; font-weight: 700; text-transform: uppercase; }

/* 提示条 */
.tips { color: #f97316; background: #fff7ed; border: 1px solid #ffedd5; padding: 12px; border-radius: 8px; font-size: 12px; margin-bottom: 20px; }

/* 表单排版统一 */
.form-item { margin-bottom: 15px; }
.form-item label { display: block; margin-bottom: 6px; font-weight: 700; font-size: 14px; color: #1e293b; }
.form-item input { 
  width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; 
  box-sizing: border-box; font-size: 14px; color: #1e293b; transition: border-color 0.2s;
}
.form-item input:focus { border-color: #165DFF; outline: none; }
.form-item input::placeholder { color: #94a3b8; }

/* 按钮统一 */
.submit-btn { 
  width: 100%; padding: 14px; background: #165DFF; color: white; border: none; 
  border-radius: 12px; cursor: pointer; font-weight: 700; font-size: 15px; margin-top: 10px; transition: opacity 0.2s;
}
.submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.submit-btn:active:not(:disabled) { transform: scale(0.98); }

.home-btn { 
  margin-top: 25px; width: 100%; padding: 14px; background: #10b981; color: white; 
  border: none; border-radius: 12px; cursor: pointer; font-weight: 700; font-size: 15px; 
}
.home-btn:active { transform: scale(0.98); }

.refresh-btn-small { 
  background: white; border: 1px solid #e2e8f0; color: #64748b; padding: 6px 14px; 
  border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; margin-top: 10px; 
}
.refresh-btn-small:active { background: #f8fafc; }

/* 状态展示区样式 */
.status-box { text-align: center; padding: 30px 0; }
.status-box p { font-size: 13px; color: #64748b; margin: 0; }
.icon { font-size: 48px; margin-bottom: 15px; }
.icon-success { font-size: 48px; color: #10b981; margin-bottom: 10px; }

/* 个人信息与车辆列表区块统一 */
.user-profile-section, .vehicle-list-section {
  text-align: left; background: #f8fafc; border: 1px solid #f1f5f9; 
  padding: 15px; border-radius: 12px; margin-top: 15px;
}
.info-row { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 13px; color: #64748b; }
.info-row b { font-weight: 800; color: #1e293b; }

.no-data { font-size: 13px; color: #94a3b8; text-align: center; padding: 10px 0; }
.car-card { background: white; border: 1px solid #e2e8f0; padding: 12px; border-radius: 12px; margin-bottom: 8px; }
.car-main { display: flex; align-items: baseline; }
.plate { font-weight: 700; font-size: 15px; color: #1e293b; margin-right: 10px; }
.model { color: #64748b; font-size: 12px; }

/* 辅助与状态类 */
.text-red { color: #ef4444 !important; }
.score-tip { font-size: 12px; color: #ef4444 !important; margin-top: 8px; font-weight: 700; }
.status-tag.active { 
  background: #eff6ff; color: #165DFF; padding: 2px 8px; 
  border-radius: 6px; font-size: 11px; font-weight: 700; 
}

/* 简单的 loading 动画 */
.loader {
  border: 3px solid #f1f5f9; border-radius: 50%; border-top: 3px solid #165DFF;
  width: 24px; height: 24px; animation: spin 1s linear infinite; margin: 0 auto 15px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>