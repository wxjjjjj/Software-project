<template>
  <div class="admin-users-container">
    <!-- 顶部标题栏 -->
    <div class="header-section">
      <div class="title-group">
        <h1>用户管理</h1>
        <span class="subtitle">共 <b>{{ userList.length }}</b> 人</span>
      </div>
      <button class="refresh-btn" @click="fetchUsers">
        <span class="icon">↻</span> 刷新
      </button>
    </div>

    <!-- 1. PC端显示的表格布局 (仅在宽屏显示) -->
    <div class="pc-table-view">
      <div class="table-card">
        <table class="user-table">
          <thead>
            <tr>
              <th width="80">ID</th>
              <th>用户名</th>
              <th>身份状态</th>
              <th width="220" class="text-right">管理操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(user, i) in userList" :key="user.userId" :style="{ animationDelay: `${i * 0.04}s` }">
              <td class="id-cell"><code>#{{ user.userId }}</code></td>
              <td class="username-text">
                {{ user.username }}
                <span v-if="user.username === 'admin'" class="admin-badge">Admin</span>
              </td>
              <td>
                <div class="status-group">
                  <span :class="['status-tag', user.passenger_status]">
                    客: {{ user.passenger_status === 'active' ? '正常' : '封禁' }}
                  </span>
                  <span :class="['status-tag', user.driver_status]">
                    车: {{ getDriverStatusShort(user.driver_status) }}
                  </span>
                </div>
              </td>
              <td class="action-cell text-right">
                <span v-if="user.username === 'admin'" class="admin-txt">系统保留</span>
                <template v-else>
                  <button @click="updateStatus(user.userId, 'passenger', user.passenger_status === 'active' ? 'banned' : 'active')"
                          :class="['action-btn', user.passenger_status === 'active' ? 'btn-danger' : 'btn-success']">
                    {{ user.passenger_status === 'active' ? '封乘客' : '解乘客' }}
                  </button>
                  <button v-if="user.driver_status !== 'unapplied' && user.driver_status !== 'pending'"
                          @click="updateStatus(user.userId, 'driver', user.driver_status === 'active' ? 'banned' : 'active')"
                          :class="['action-btn', user.driver_status === 'active' ? 'btn-danger' : 'btn-success']">
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
      <div v-for="(user, i) in userList" :key="user.userId" class="user-item-card" :style="{ animationDelay: `${i * 0.05}s` }">
        <div class="card-header">
          <span class="user-id"><code>#{{ user.userId }}</code></span>
          <span class="user-name">{{ user.username }}</span>
          <span v-if="user.username === 'admin'" class="admin-badge">管理员</span>
        </div>
        
        <div class="card-body">
          <div class="status-row">
            <span class="label">拼车人身份</span>
            <span :class="['status-tag', user.passenger_status]">{{ user.passenger_status === 'active' ? '正常' : '已封禁' }}</span>
          </div>
          <div class="status-row">
            <span class="label">车主身份</span>
            <span :class="['status-tag', user.driver_status]">{{ getDriverStatusText(user.driver_status) }}</span>
          </div>
        </div>

        <div v-if="user.username !== 'admin'" class="card-footer">
          <button @click="updateStatus(user.userId, 'passenger', user.passenger_status === 'active' ? 'banned' : 'active')"
                  :class="['mob-btn', user.passenger_status === 'active' ? 'btn-danger' : 'btn-success']">
            {{ user.passenger_status === 'active' ? '封禁乘客' : '解封乘客' }}
          </button>
          
          <button v-if="user.driver_status !== 'unapplied' && user.driver_status !== 'pending'"
                  @click="updateStatus(user.userId, 'driver', user.driver_status === 'active' ? 'banned' : 'active')"
                  :class="['mob-btn', user.driver_status === 'active' ? 'btn-danger' : 'btn-success']">
            {{ user.driver_status === 'active' ? '封禁车主' : '解封车主' }}
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
/* 基础动画 */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 基础框架 */
.admin-users-container { padding: 20px; background: #f8fafc; min-height: 100vh; padding-bottom: 40px; }
.header-section { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; padding: 0 4px; }
.title-group h1 { font-size: 20px; font-weight: 800; color: #1e293b; margin: 0 0 4px 0; }
.subtitle { font-size: 13px; color: #94a3b8; }
.subtitle b { color: #165DFF; }

/* 刷新按钮 */
.refresh-btn { 
  display: flex; align-items: center; gap: 4px;
  padding: 6px 14px; background: #fff; color: #1e293b; 
  border: 1.5px solid #e2e8f0; border-radius: 20px; 
  font-size: 13px; font-weight: 700; cursor: pointer;
  transition: all 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}
.refresh-btn:active { background: #f1f5f9; transform: scale(0.96); }
.refresh-btn .icon { font-size: 14px; font-weight: bold; color: #165DFF; }

/* 代码字体小标签 */
code { font-family: monospace; background: #f1f5f9; padding: 2px 6px; border-radius: 6px; font-size: 12px; color: #64748b; }

/* --- PC端布局样式 --- */
.pc-table-view { display: block; }
.table-card { 
  background: white; border-radius: 16px; overflow: hidden; 
  box-shadow: 0 4px 20px rgba(22,93,255,.05); border: 1px solid #e2e8f0;
}
.user-table { width: 100%; border-collapse: collapse; text-align: left; }
.user-table th { background: #f8fafc; padding: 14px 16px; font-size: 13px; font-weight: 700; color: #64748b; border-bottom: 1px solid #e2e8f0; }
.user-table td { padding: 14px 16px; border-bottom: 1px solid #f1f5f9; font-size: 14px; color: #1e293b; }
.user-table tr { animation: fadeUp 0.3s ease both; transition: background 0.2s; }
.user-table tr:hover { background: #f8fafc; }
.user-table tr:last-child td { border-bottom: none; }
.text-right { text-align: right !important; }

.username-text { font-weight: 700; display: flex; align-items: center; gap: 8px; }
.admin-badge { font-size: 11px; background: #1e293b; color: #fff; padding: 2px 8px; border-radius: 10px; font-weight: 700; }

/* 操作按钮 (PC) */
.action-cell { display: flex; justify-content: flex-end; gap: 8px; }
.action-btn { 
  padding: 6px 12px; border: none; border-radius: 8px; 
  cursor: pointer; font-size: 12px; font-weight: 700; transition: all 0.15s;
}
.action-btn:active { transform: scale(0.95); }
.admin-txt { color: #94a3b8; font-size: 12px; font-weight: 600; padding: 6px 0; }

/* --- 移动端布局样式 --- */
.mobile-list-view { display: none; }
.user-item-card { 
  background: white; border-radius: 16px; padding: 16px; margin-bottom: 12px; 
  box-shadow: 0 2px 12px rgba(22,93,255,.06); border: 1px solid #e2e8f0;
  animation: fadeUp 0.3s ease both;
}
.card-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 12px; }
.user-name { font-weight: 800; color: #1e293b; font-size: 15px; flex: 1; }

.card-body { margin-bottom: 16px; }
.status-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 13px; }
.status-row .label { color: #64748b; font-weight: 600; }

/* 操作按钮 (移动端) */
.card-footer { display: flex; gap: 10px; }
.mob-btn { 
  flex: 1; padding: 10px; border: none; border-radius: 10px; 
  font-size: 13px; font-weight: 700; cursor: pointer; transition: all 0.15s; 
}
.mob-btn:active { transform: scale(0.96); }

/* --- 状态标签与按钮颜色体系 --- */
.status-group { display: flex; gap: 6px; }
.status-tag { padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; border: 1px solid transparent; }

/* 状态色映射 */
.status-tag.active, .status-tag.approved { background: #ecfdf5; color: #10b981; border-color: #a7f3d0; } /* 正常/已通过 */
.status-tag.banned { background: #fef2f2; color: #ef4444; border-color: #fecaca; } /* 封禁 */
.status-tag.pending { background: #fff7ed; color: #f97316; border-color: #fed7aa; } /* 审核中 */
.status-tag.unapplied { background: #f1f5f9; color: #64748b; border-color: #e2e8f0; } /* 未申请 */

/* 按钮色映射 */
.btn-success { background: #ecfdf5; color: #10b981; }
.btn-success:hover { background: #d1fae5; }
.btn-danger { background: #fef2f2; color: #ef4444; }
.btn-danger:hover { background: #fee2e2; }

/* 响应式媒体查询：切换双端视图 */
@media (max-width: 768px) {
  .pc-table-view { display: none; } 
  .mobile-list-view { display: block; }
}
</style>