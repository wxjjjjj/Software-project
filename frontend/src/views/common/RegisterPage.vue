<template>
  <div class="register-page">
    <div class="register-card">
      <h2>新用户注册</h2>

      <div class="form-item">
        <label>用户名</label>
        <input v-model.trim="form.username" placeholder="用户名 (3-20位)" />
      </div>

      <div class="form-item">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="密码 (6位以上)" />
      </div>

      <div class="form-item">
        <label>手机号</label>
        <input v-model.trim="form.phone" placeholder="手机号 (11位)" />
      </div>

      <div class="form-item">
        <label>真实姓名</label>
        <input v-model.trim="form.real_name" placeholder="真实姓名" />
      </div>

      <div class="form-item">
        <label>身份证号</label>
        <input v-model.trim="form.id_card" placeholder="身份证号 (18位)" />
      </div>

      <button class="reg-btn" :disabled="loading" @click="handleRegister">
        {{ loading ? '注册中...' : '提交注册' }}
      </button>

      <div class="footer">
        <router-link to="/login">已有账号？去登录</router-link>
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
  phone: '',
  real_name: '',
  id_card: ''
})

const handleRegister = async () => {
  error.value = ''

  if (!form.value.username || !form.value.password || !form.value.phone || !form.value.real_name || !form.value.id_card) {
    error.value = '请填写完整注册信息'
    return
  }

  loading.value = true
  try {
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })

    const data = await res.json().catch(() => ({}))

    if (res.ok) {
      alert('注册成功，欢迎加入！请登录。')
      router.push('/login')
      return
    }

    if (Array.isArray(data.detail)) {
      error.value = '校验失败：\n' + data.detail.map((err) => `${err.loc[1]}: ${err.msg}`).join('\n')
      return
    }

    error.value = '注册失败：' + (data.detail || '未知错误')
  } catch {
    error.value = '网络请求错误，请检查网关是否开启'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(circle at top right, rgba(22, 93, 255, 0.12), transparent 28%),
    #f4f7fb;
}

.register-card {
  width: min(100%, 380px);
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

.form-item input:focus {
  border-color: #165dff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.1);
}

.reg-btn {
  width: 100%;
  border: none;
  border-radius: 10px;
  padding: 12px;
  background: #165dff;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.reg-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.footer {
  margin-top: 14px;
  text-align: center;
  font-size: 13px;
}

.footer a {
  color: #165dff;
  text-decoration: none;
}

.error-text {
  white-space: pre-line;
  margin: 14px 0 0;
  color: #d14343;
  font-size: 13px;
}
</style>
