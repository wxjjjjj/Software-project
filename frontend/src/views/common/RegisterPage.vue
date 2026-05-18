<template>
  <div class="register-page">
    <div class="register-card">
      <h2>新用户注册</h2>
      <div class="form-item">
        <input v-model="form.username" placeholder="用户名 (3-20位)" />
      </div>
      <div class="form-item">
        <input v-model="form.password" type="password" placeholder="密码 (6位以上)" />
      </div>
      <div class="form-item">
        <input v-model="form.phone" placeholder="手机号 (11位)" />
      </div>
      <div class="form-item">
        <input v-model="form.real_name" placeholder="真实姓名" />
      </div>
      <div class="form-item">
        <input v-model="form.id_card" placeholder="身份证号 (18位)" />
      </div>
      <button class="reg-btn" @click="handleRegister">提交注册</button>
      <div class="footer">
        <router-link to="/login">已有账号？去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const form = ref({
  username: '', password: '', phone: '', real_name: '', id_card: ''
})

const handleRegister = async () => {
  // 基础非空校验
  if (!form.value.username || !form.value.password || !form.value.phone || !form.value.real_name || !form.value.id_card) {
    alert('请填写完整注册信息')
    return
  }

  try {
    // 匹配网关：@app.api_route("/api/auth/{path:path}") -> 转发到 8001
    const res = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })

    if (res.ok) {
      alert('注册成功，欢迎加入！请登录。')
      router.push('/login')
    } else {
      const data = await res.json()
      // 如果 detail 是数组，说明是 Pydantic 校验错误，我们把它转成文字
      if (Array.isArray(data.detail)) {
        const errorMsg = data.detail.map(err => `${err.loc[1]}: ${err.msg}`).join('\n')
        alert('校验失败：\n' + errorMsg)
      } else {
        alert('注册失败: ' + (data.detail || '未知错误'))
      }
    }
  } catch (err) {
    alert('网络请求错误，请检查网关是否开启')
  }
}


</script>

<style scoped>
.register-page { height: 100vh; display: flex; align-items: center; justify-content: center; background: #f4f7f6; }
.register-card { background: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); width: 380px; }
h2 { text-align: center; color: #333; margin-bottom: 30px; }
.form-item { margin-bottom: 15px; }
.form-item input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; box-sizing: border-box; font-size: 14px; }
.form-item input:focus { border-color: #52c41a; outline: none; box-shadow: 0 0 0 2px rgba(82,196,26,0.1); }
.reg-btn { width: 100%; padding: 14px; background: #52c41a; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background 0.3s; }
.reg-btn:hover { background: #45a616; }
.footer { margin-top: 20px; text-align: center; font-size: 14px; }
</style>