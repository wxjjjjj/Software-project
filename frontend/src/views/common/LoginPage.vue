<template>
  <div class="login-page">
    <div class="login-card">
      <h2>用户登录</h2>
      <div class="form-item">
        <label>用户名</label>
        <input v-model="form.username" type="text" placeholder="请输入用户名" />
      </div>
      <div class="form-item">
        <label>密码</label>
        <input v-model="form.password" type="password" placeholder="请输入密码" />
      </div>
      <button class="login-btn" @click="handleLogin" :disabled="loading">
        {{ loading ? '登录中...' : '登录' }}
      </button>
      <div class="footer-links">
        <router-link to="/register">立即注册</router-link>
        <router-link to="/admin/login" class="admin-link">管理员入口</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const form = ref({ username: '', password: '' })

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    alert('请填写账号密码')
    return
  }
  
  loading.value = true
  try {
    // 对应网关转发的 /api/auth/{path} 逻辑
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    
    const data = await res.json()

    if (res.ok) {
      // 按照组长 index.js 的约定保存数据
      const sessionData = {
        token: 'token-' + data.userId, 
        role: data.role,               
        userId: data.userId,
        username: data.username,
        // 如果是司机且审核通过，设为 true
        ownerVerified: data.driver && data.driver.status === 'approved'
      }
      localStorage.setItem('session', JSON.stringify(sessionData))
      alert('登录成功！')
      
      // 根据角色跳转
      if (data.role === 'driver') {
        router.push('/driver/home')
      } else {
        router.push('/passenger/home')
      }
    } else {
      alert(data.detail || '登录失败：账号或密码错误')
    }
  } catch (err) {
    alert('请求失败，请检查 8000 网关和 8001 后端是否启动')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { height: 100vh; display: flex; align-items: center; justify-content: center; background: #f0f2f5; }
.login-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); width: 320px; }
h2 { text-align: center; margin-bottom: 25px; }
.form-item { margin-bottom: 15px; }
.form-item label { display: block; margin-bottom: 5px; font-size: 14px; }
.form-item input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
.login-btn { width: 100%; padding: 12px; background: #1890ff; color: white; border: none; border-radius: 6px; cursor: pointer; }
.footer-links { margin-top: 15px; display: flex; justify-content: space-between; font-size: 13px; }
</style>