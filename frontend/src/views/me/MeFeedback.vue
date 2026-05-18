<template>
  <div class="page-card">
    <h2 style="margin:0 0 8px;color:#172033;">反馈投诉</h2>
    <p style="margin:0 0 16px;color:#65758b;font-size:13px;line-height:1.6;">
      投诉功能已接入运营域。请选择您的身份进入对应的投诉页面。
    </p>

    <div class="feedback-links">
      <van-button
        type="primary"
        block
        @click="$router.push('/passenger/feedback')"
        style="margin-bottom:12px"
      >
        乘客投诉页（提交投诉 / 我的投诉）
      </van-button>
      <van-button
        v-if="isDriver"
        type="primary"
        block
        @click="$router.push('/driver/feedback')"
        style="margin-bottom:12px"
      >
        车主投诉页（提交投诉 / 我的投诉）
      </van-button>
      <van-button
        v-if="isAdmin"
        type="danger"
        block
        @click="$router.push('/admin/feedback')"
      >
        管理端投诉处理（审核 + 提现管理）
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const isDriver = ref(false)
const isAdmin = ref(false)

function getSession() {
  try { return JSON.parse(localStorage.getItem('session') || '{}') }
  catch { return {} }
}

onMounted(() => {
  const session = getSession()
  if (session.role === 'admin') {
    isAdmin.value = true
  } else if (session.role === 'driver' || session.ownerVerified === true) {
    isDriver.value = true
  }
})
</script>

<style scoped>
.feedback-links { margin-top: 8px; }
</style>
