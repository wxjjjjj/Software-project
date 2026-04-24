<template>
  <div class="admin-users-container">
    <!-- 顶部标题栏 -->
    <div class="header-section">
      <div class="title-group">
        <h1>用户管理</h1>
        <span class="subtitle">共 {{ userList.length }} 人</span>
      </div>
      <button class="refresh-btn" @click="fetchUsers">刷新</button>
    </div>

    <!-- 1. PC端显示的表格布局 (仅在宽屏显示) -->
    <div class="pc-table-view">
      <div class="table-card">
        <table class="user-table">
          <thead>
            <tr>
              <th width="60">ID</th>
              <th>用户名</th>
              <th>身份状态</th>
              <th width="200">管理操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in userList" :key="user.userId">
              <td>{{ user.userId }}</td>
              <td class="username-text">{{ user.username }}</td>
              <td>
                <div class="status-group">
                  <span :class="['tag', user.passenger_status]">客:{{ user.passenger_status === 'active' ? '正常' : '封禁' }}</span>
                  <span :class="['tag', user.driver_status]">车:{{ getDriverStatusShort(user.driver_status) }}</span>
                </div>
              </td>
              <td class="action-cell">
                <span v-if="user.username === 'admin'" class="admin-txt">无法操作</span>
                <template v-else>
                  <button @click="updateStatus(user.userId, 'passenger', user.passenger_status === 'active' ? 'banned' : 'active')"
                          :class="['mini-btn', user.passenger_status === 'active' ? 'ban' : 'unban']">
                    {{ user.passenger_status === 'active' ? '封乘客' : '解乘客' }}
                  </button>
                  <button v-if="user.driver_status !== 'unapplied' && user.driver_status !== 'pending'"
                          @click="updateStatus(user.userId, 'driver', user.driver_status === 'active' ? 'banned' : 'active')"
                          :class="['mini-btn', user.driver_status === 'active' ? 'ban' : 'unban']">
                    {{ user.driver_status === 'active' ? '封车主' : '解车主' }}
                  </button>
                </template>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 2. 移动端显示的卡片布局 (仅在窄屏显示) -->
    <div class="mobile-list-view">
      <div v-for="user in userList" :key="user.userId" class="user-item-card">
        <div class="card-header">
          <span class="user-id">#{{ user.userId }}</span>
          <span class="user-name">{{ user.username }}</span>
          <span v-if="user.username === 'admin'" class="admin-badge">管理员</span>
        </div>
        
        <div class="card-body">
          <div class="status-row">
            <span class="label">拼车人:</span>
            <span :class="['status-val', user.passenger_status]">{{ user.passenger_status === 'active' ? '正常' : '已封禁' }}</span>
          </div>
          <div class="status-row">
            <span class="label">车主身份:</span>
            <span :class="['status-val', user.driver_status]">{{ getDriverStatusText(user.driver_status) }}</span>
          </div>
        </div>

        <div v-if="user.username !== 'admin'" class="card-footer">
          <button @click="updateStatus(user.userId, 'passenger', user.passenger_status === 'active' ? 'banned' : 'active')"
                  :class="['mob-btn', user.passenger_status === 'active' ? 'ban' : 'unban']">
            {{ user.passenger_status === 'active' ? '封禁乘客身份' : '解封乘客身份' }}
          </button>
          
          <button v-if="user.driver_status !== 'unapplied' && user.driver_status !== 'pending'"
                  @click="updateStatus(user.userId, 'driver', user.driver_status === 'active' ? 'banned' : 'active')"
                  :class="['mob-btn', user.driver_status === 'active' ? 'ban' : 'unban']">
            {{ user.driver_status === 'active' ? '封禁车主身份' : '解封车主身份' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const userList = ref([])
const fetchUsers = async () => {
  try {
    const res = await fetch('/api/users/admin/users')
    if (res.ok) {
      const data = await res.json()
      userList.value = data.items
    }
  } catch (err) { console.error(err) }
}

const updateStatus = async (userId, identity, newStatus) => {
  if (!confirm('确认修改该身份状态吗？')) return
  try {
    const res = await fetch('/api/users/admin/update-status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, target_identity: identity, new_status: newStatus })
    })
    if (res.ok) fetchUsers()
  } catch (err) { alert('网络错误') }
}

const getDriverStatusText = (s) => ({
  'unapplied': '未申请', 'pending': '审核中', 'approved': '已通过', 'active': '正常', 'banned': '已封禁'
}[s] || s)

const getDriverStatusShort = (s) => ({
  'unapplied': '无', 'pending': '审', 'approved': '优', 'active': '正', 'banned': '封'
}[s] || s)

onMounted(fetchUsers)
</script>

<style scoped>
/* 基础样式 */
.admin-users-container { padding: 15px; background: #f5f7f9; min-height: 100vh; }
.header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h1 { font-size: 20px; color: #333; margin: 0; }
.subtitle { font-size: 12px; color: #999; }
.refresh-btn { padding: 6px 15px; background: #409eff; color: white; border: none; border-radius: 20px; font-size: 13px; }

/* PC端布局样式 */
.pc-table-view { display: block; }
.table-card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
.user-table { width: 100%; border-collapse: collapse; }
.user-table th { background: #fafafa; padding: 12px; text-align: left; font-size: 13px; }
.user-table td { padding: 12px; border-top: 1px solid #f0f0f0; font-size: 13px; }
.status-group { display: flex; gap: 4px; }
.tag { padding: 2px 6px; border-radius: 4px; font-size: 11px; }
.mini-btn { padding: 4px 8px; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px; font-size: 11px; }

/* 移动端布局样式 (重点) */
.mobile-list-view { display: none; }
.user-item-card { background: white; border-radius: 12px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
.card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; border-bottom: 1px solid #f0f0f0; padding-bottom: 10px; }
.user-id { color: #409eff; font-weight: bold; font-size: 14px; }
.user-name { font-weight: 600; color: #333; flex: 1; }
.admin-badge { font-size: 10px; background: #f0f0f0; padding: 2px 6px; border-radius: 10px; color: #999; }

.card-body { margin-bottom: 15px; }
.status-row { display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 14px; }
.label { color: #666; }
.status-val.active { color: #52c41a; font-weight: bold; }
.status-val.banned { color: #f5222d; font-weight: bold; }

.card-footer { display: flex; flex-direction: column; gap: 8px; }
.mob-btn { width: 100%; padding: 10px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; }

/* 颜色定义 */
.active, .unban { background: #f6ffed; color: #52c41a; border: 1px solid #b7eb8f; }
.banned, .ban { background: #fff1f0; color: #f5222d; border: 1px solid #ffa39e; }
.unapplied { background: #f5f5f5; color: #999; }
.admin-txt { color: #ccc; font-size: 12px; }

/* 响应式媒体查询：关键！ */
@media (max-width: 768px) {
  .pc-table-view { display: none; } /* 隐藏表格 */
  .mobile-list-view { display: block; } /* 显示卡片 */
}
</style>