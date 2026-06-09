<template>
  <div class="chat-page">
    <van-loading v-if="loadingOrder" class="page-loading" type="spinner" color="#165DFF" />

    <template v-else-if="order">
      <section class="chat-card">
        <header class="chat-header">
          <div class="chat-header-main">
            <div class="chat-title">订单聊天</div>
            <div class="chat-subtitle">#{{ orderId }}</div>
            <div class="chat-meta">
              <span>{{ order.start_loc }}</span>
              <span class="chat-meta-arrow">→</span>
              <span>{{ order.end_loc }}</span>
            </div>
          </div>
          <span class="chat-status" :class="`is-${orderStatus.tone}`">{{ orderStatus.label }}</span>
        </header>

        <div class="target-panel">
          <div class="target-label">聊天对象</div>

          <div v-if="availableTargets.length" class="target-list">
            <button
              v-for="target in availableTargets"
              :key="target.id"
              type="button"
              class="target-pill"
              :class="{ active: selectedTargetId === target.id }"
              @click="selectedTargetId = target.id"
            >
              <span class="target-role">{{ target.roleLabel }}</span>
              <span class="target-name">{{ target.name }}</span>
            </button>
          </div>

          <van-empty v-else image-size="56" description="当前订单暂无可聊天对象" />
        </div>

        <template v-if="activeTarget">
          <div class="chat-panel">
            <div class="chat-panel-head">
              正在和{{ activeTarget.roleLabel }} {{ activeTarget.name }}聊天
            </div>

            <div class="chat-messages" ref="msgContainer">
              <van-loading
                v-if="loadingMessages"
                class="message-loading"
                type="spinner"
                color="#165DFF"
              />

              <template v-else>
                <div
                  v-for="msg in messages"
                  :key="msg.msgId"
                  :class="['msg-row', msg.senderId === myId ? 'msg-self' : 'msg-other']"
                >
                  <div class="msg-bubble">
                    <div class="msg-content">{{ msg.content }}</div>
                    <div class="msg-time">{{ formatMessageTime(msg.sendTime) }}</div>
                  </div>
                </div>

                <div v-if="messages.length === 0" class="empty-chat">
                  <div class="empty-chat-title">还没有聊天记录</div>
                  <div class="empty-chat-text">发一条消息开始聊天吧。</div>
                </div>
              </template>
            </div>

            <div class="chat-input-shell">
              <van-field
                v-model="inputText"
                class="chat-field"
                rows="1"
                autosize
                type="textarea"
                maxlength="500"
                placeholder="输入消息..."
                @keydown.enter.exact.prevent="sendMsg"
              />
              <van-button class="send-btn" round type="primary" :loading="sending" @click="sendMsg">
                发送
              </van-button>
            </div>
          </div>
        </template>
      </section>
    </template>

    <van-empty v-else description="订单不存在" />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { fetchUserProfiles, getCachedUsername } from '@/api/account.js'
import { getMessages, getUserId as getOpsUserId, markMessagesRead, sendMessage } from '../../api/ops.js'
import { getUserId as getRideUserId, rideApi } from '../../api/ride.js'

const route = useRoute()
const orderId = String(route.params.orderId || '')
const myId = Number(getOpsUserId())
const myOrderUserId = String(getRideUserId() || '').trim()

const loadingOrder = ref(true)
const loadingMessages = ref(false)
const order = ref(null)
const selectedTargetId = ref('')
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const msgContainer = ref(null)
const userNames = ref({})

function formatMessageTime(value) {
  if (!value) return ''
  const time = new Date(value)
  if (Number.isNaN(time.getTime())) return String(value).slice(11, 16)
  const hh = String(time.getHours()).padStart(2, '0')
  const mm = String(time.getMinutes()).padStart(2, '0')
  return `${hh}:${mm}`
}

function toNumericId(value) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function toStableChatUserId(value) {
  const direct = toNumericId(value)
  if (direct !== null) return direct

  const text = String(value || '').trim()
  if (!text) return null

  let hash = 0
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 131 + text.charCodeAt(index)) % 1000000007
  }
  return 100000 + hash
}

function displayName(id) {
  const key = String(id || '').trim()
  return userNames.value[key] || getCachedUsername(key)
}

const orderStatus = computed(() => {
  const status = order.value?.status
  return ({
    published: { label: '招募中', tone: 'success' },
    full: { label: '已满员', tone: 'warning' },
    locked: { label: '已锁单', tone: 'primary' },
    completed: { label: '已完成', tone: 'success' },
  })[status] || { label: status || '未知状态', tone: 'default' }
})

const hasAcceptedDriver = computed(() => {
  if (!order.value) return false
  const ownerId = String(order.value.owner_id || '')
  if (!ownerId) return false
  return order.value.status === 'locked' || Boolean(order.value.locked_time) || Boolean(order.value.vehicle_id)
})

const availableTargets = computed(() => {
  if (!order.value) return []

  const targets = []
  const seen = new Set()

  const addTarget = (rawId, role) => {
    const id = String(rawId || '').trim()
    if (!id || id === myOrderUserId || seen.has(id)) return

    const backendUserId = toStableChatUserId(id)
    if (backendUserId === null) return

    seen.add(id)

    const roleMeta = role === 'driver'
      ? { roleLabel: '车主' }
      : role === 'publisher'
        ? { roleLabel: '发起人' }
        : { roleLabel: '乘客' }

    targets.push({
      id,
      name: displayName(id),
      backendUserId,
      ...roleMeta,
    })
  }

  if (hasAcceptedDriver.value) {
    addTarget(order.value.owner_id, 'driver')
  }

  for (const passenger of order.value.passengers || []) {
    const passengerId = String(passenger.passenger_id || '').trim()
    if (!passengerId) continue
    addTarget(
      passengerId,
      passengerId === String(order.value.passenger_id || '') ? 'publisher' : 'passenger',
    )
  }

  return targets
})

const activeTarget = computed(() =>
  availableTargets.value.find((target) => target.id === selectedTargetId.value) || null,
)

function pickDefaultTarget() {
  const preferred = String(route.query.targetUserId || '').trim()
  if (preferred && availableTargets.value.some((target) => target.id === preferred)) {
    return preferred
  }

  const driverTarget = availableTargets.value.find((target) => target.roleLabel === '车主')
  return driverTarget?.id || availableTargets.value[0]?.id || ''
}

async function scrollToBottom() {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

async function loadMessages() {
  if (!activeTarget.value) {
    messages.value = []
    return
  }

  loadingMessages.value = true
  try {
    const data = await getMessages(orderId, myId, activeTarget.value.backendUserId)
    messages.value = data.items || []
    await markMessagesRead(orderId, myId, activeTarget.value.backendUserId)
    await scrollToBottom()
  } catch (error) {
    showToast(error.message || '加载消息失败')
  } finally {
    loadingMessages.value = false
  }
}

async function loadOrder() {
  loadingOrder.value = true
  try {
    order.value = await rideApi.getOrderDetail(orderId)
    await syncUserNames()
  } catch (error) {
    order.value = null
    showToast(error.message || '加载订单失败')
  } finally {
    loadingOrder.value = false
  }
}

async function syncUserNames() {
  if (!order.value) return

  const ids = new Set()
  const addId = (value) => {
    const id = String(value || '').trim()
    if (id) ids.add(id)
  }

  addId(order.value.passenger_id)
  addId(order.value.owner_id)
  for (const passenger of order.value.passengers || []) {
    addId(passenger.passenger_id)
  }

  const profiles = await fetchUserProfiles(Array.from(ids))
  userNames.value = Object.entries(profiles).reduce((map, [id, profile]) => {
    map[id] = profile.username
    return map
  }, { ...userNames.value })
}

async function sendMsg() {
  const text = inputText.value.trim()
  if (!text || !activeTarget.value) return

  if (activeTarget.value.id === myOrderUserId || activeTarget.value.backendUserId === myId) {
    showToast('不能和自己聊天')
    return
  }

  sending.value = true
  try {
    await sendMessage({
      orderId,
      senderId: myId,
      receiverId: activeTarget.value.backendUserId,
      content: text,
    })
    inputText.value = ''
    await loadMessages()
  } catch (error) {
    showToast(error.message || '发送失败')
  } finally {
    sending.value = false
  }
}

watch(
  availableTargets,
  (targets) => {
    if (!targets.length) {
      selectedTargetId.value = ''
      messages.value = []
      return
    }

    if (!targets.some((target) => target.id === selectedTargetId.value)) {
      selectedTargetId.value = pickDefaultTarget()
    }
  },
  { immediate: true },
)

watch(selectedTargetId, async () => {
  inputText.value = ''
  await loadMessages()
})

watch(
  () => messages.value.length,
  async () => {
    await scrollToBottom()
  },
)

onMounted(async () => {
  await loadOrder()
})
</script>

<style scoped>
.chat-page {
  padding-bottom: 18px;
}

.page-loading {
  display: flex;
  justify-content: center;
  padding: 72px 0;
}

.chat-card {
  display: grid;
  gap: 12px;
}

.chat-header {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #dce8ff;
  padding: 14px 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  box-shadow: 0 4px 18px rgba(22, 93, 255, 0.06);
}

.chat-header-main {
  min-width: 0;
  flex: 1;
}

.chat-title {
  font-size: 17px;
  font-weight: 800;
  color: #172033;
}

.chat-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
  word-break: break-all;
}

.chat-meta {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #334155;
  flex-wrap: wrap;
}

.chat-meta-arrow {
  color: #165dff;
  font-weight: 700;
}

.chat-status {
  flex: 0 0 auto;
  padding: 5px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  background: #f3f4f6;
  color: #64748b;
}

.chat-status.is-success {
  background: #ecfdf5;
  color: #16a34a;
}

.chat-status.is-warning {
  background: #fff7ed;
  color: #ea580c;
}

.chat-status.is-primary {
  background: #eff6ff;
  color: #165dff;
}

.target-panel,
.chat-panel {
  background: #fff;
  border-radius: 16px;
  border: 1px solid #dce8ff;
  padding: 14px;
  box-shadow: 0 4px 18px rgba(22, 93, 255, 0.06);
}

.target-label,
.chat-panel-head {
  font-size: 13px;
  font-weight: 700;
  color: #475569;
}

.target-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.target-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  border: 1px solid #dbe7ff;
  background: #f8fbff;
  color: #334155;
  font-size: 13px;
}

.target-pill.active {
  background: #eaf2ff;
  border-color: #8bb6ff;
  color: #165dff;
}

.target-role {
  font-size: 11px;
  font-weight: 700;
  color: #64748b;
}

.target-name {
  font-weight: 700;
}

.chat-messages {
  margin-top: 12px;
  min-height: 320px;
  max-height: 420px;
  overflow-y: auto;
  padding: 12px;
  border-radius: 14px;
  background: #f8fbff;
  border: 1px solid #edf3ff;
}

.message-loading {
  padding: 44px 0;
  text-align: center;
}

.msg-row {
  display: flex;
  margin-bottom: 12px;
}

.msg-self {
  justify-content: flex-end;
}

.msg-other {
  justify-content: flex-start;
}

.msg-bubble {
  max-width: 82%;
}

.msg-content {
  display: inline-block;
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.45;
  word-break: break-word;
}

.msg-self .msg-content {
  background: #165dff;
  color: #fff;
  border-radius: 14px 4px 14px 14px;
}

.msg-other .msg-content {
  background: #fff;
  color: #253041;
  border: 1px solid #e5edf9;
  border-radius: 4px 14px 14px 14px;
}

.msg-time {
  margin-top: 4px;
  font-size: 11px;
  color: #94a3b8;
}

.msg-self .msg-time {
  text-align: right;
}

.empty-chat {
  min-height: 180px;
  display: grid;
  place-content: center;
  text-align: center;
  color: #64748b;
}

.empty-chat-title {
  font-size: 15px;
  font-weight: 700;
  color: #172033;
}

.empty-chat-text {
  margin-top: 6px;
  font-size: 12px;
}

.chat-input-shell {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid #e6eefb;
  background: #fff;
}

.chat-field {
  flex: 1;
  padding: 0;
  background: transparent;
}

.send-btn {
  flex: 0 0 auto;
  min-width: 72px;
  font-weight: 700;
}
</style>
