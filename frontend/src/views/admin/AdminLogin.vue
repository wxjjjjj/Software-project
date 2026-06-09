<template>
  <div class="login-page">
    <div class="login-card">
      <h2>管理员登录</h2>

      <div class="form-item">
        <label>管理员账号</label>
        <input v-model.trim="form.username" type="text" placeholder="请输入管理员账号" />
      </div>

      <div class="form-item">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" />
      </div>

      <button class="login-btn" :disabled="loading" @click="handleAdminLogin">
        {{ loading ? '登录中...' : '登录' }}
      </button>

      <div class="footer-links footer-links--center">
        <router-link to="/login">返回普通用户登录</router-link>
      </div>

      <p v-if="error" class="error-text">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const form = ref({
  username: '',
  password: '',
})

async function handleAdminLogin() {
  error.value = ''

  if (!form.value.username || !form.value.password) {
    error.value = '请输入账号密码'
    return
  }

  loading.value = true
  try {
    const response = await fetch('/api/admin/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      error.value = data.detail || '管理员登录失败：权限不足或密码错误'
      return
    }

    const sessionData = {
      userId: data.userId,
      username: data.username,
      role: 'admin',
      token: 'admin-token-' + data.userId,
      ownerVerified: true,
    }

    localStorage.setItem('session', JSON.stringify(sessionData))
    router.push('/admin/users')
  } catch {
    error.value = '网络错误，请确保网关和后端服务已启动'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at top right, rgba(22, 93, 255, 0.12), transparent 28%),
    #f4f7fb;
}

.login-card {
  width: min(100%, 340px);
  padding: 28px 22px 22px;
  border: 1px solid #dce8ff;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 10px 28px rgba(22, 93, 255, 0.08);
}

h2 {
  margin: 0 0 22px;
  text-align: center;
  color: #172033;
}

.form-item {
  margin-bottom: 14px;
}

.form-item label {
  display: block;
  margin-bottom: 6px;
  color: #52657d;
  font-size: 13px;
}

.form-item input {
  width: 100%;
  border: 1px solid #d8e2f0;
  border-radius: 10px;
  padding: 10px 12px;
  font-size: 14px;
  box-sizing: border-box;
}

.login-btn {
  width: 100%;
  border: none;
  border-radius: 10px;
  padding: 12px;
  background: #165dff;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.footer-links {
  margin-top: 14px;
  display: flex;
  gap: 12px;
  font-size: 13px;
}

.footer-links--center {
  justify-content: center;
}

.footer-links a {
  color: #165dff;
  text-decoration: none;
}

.error-text {
  margin: 14px 0 0;
  color: #d14343;
  font-size: 13px;
}
</style>
