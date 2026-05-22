<template>
  <div class="page-card chat-room">
    <div class="chat-header">
      订单 #{{ orderId }} 聊天
    </div>

    <div class="chat-messages" ref="msgContainer">
      <div
        v-for="msg in messages"
        :key="msg.msgId"
        :class="['msg-row', msg.senderId === myId ? 'msg-self' : 'msg-other']"
      >
        <div class="msg-content">{{ msg.content }}</div>
        <div class="msg-time">{{ formatTime(msg.sendTime) }}</div>
      </div>
      <van-empty v-if="messages.length === 0" description="暂无消息" />
    </div>

    <div class="chat-input">
      <van-field
        v-model="inputText"
        placeholder="输入消息..."
        @keypress.enter="sendMsg"
      />
      <van-button type="primary" @click="sendMsg" :loading="sending" size="small">
        发送
      </van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { showToast } from 'vant'
import { sendMessage, getMessages, getUserId } from '../../api/ops.js'

const route = useRoute()
const orderId = route.params.orderId
const myId = getUserId()
const messages = ref([])
const inputText = ref('')
const sending = ref(false)
const msgContainer = ref(null)

function formatTime(t) {
  if (!t) return ''
  return t.slice(11, 19)
}

async function loadMessages() {
  try {
    const data = await getMessages(orderId, myId)
    messages.value = data.items
    await scrollToBottom()
  } catch {
    showToast('加载消息失败')
  }
}

async function scrollToBottom() {
  await nextTick()
  if (msgContainer.value) {
    msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  }
}

async function sendMsg() {
  const text = inputText.value.trim()
  if (!text) return
  sending.value = true
  const mid = Number(myId)
  const receiverId = mid === 1 ? 2 : 1
  try {
    await sendMessage({
      orderId: orderId,
      senderId: mid,
      receiverId,
      content: text
    })
    inputText.value = ''
    await loadMessages()
  } catch (e) {
    showToast(e.message || '发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  await loadMessages()
})

watch(() => messages.value.length, async () => {
  await scrollToBottom()
})
</script>

<style scoped>
.chat-room { display: flex; flex-direction: column; height: calc(100vh - 100px); padding: 0; }
.chat-header {
  position: sticky; top: 0; background: #1989fa; color: #fff;
  text-align: center; padding: 12px; font-size: 16px; z-index: 1;
}
.chat-messages { flex: 1; overflow-y: auto; padding: 12px; background: #f7f8fa; }
.msg-row { margin-bottom: 12px; max-width: 80%; }
.msg-self { margin-left: auto; text-align: right; }
.msg-other { margin-right: auto; text-align: left; }
.msg-content {
  display: inline-block; padding: 8px 12px; border-radius: 8px;
  font-size: 14px; line-height: 1.4; word-break: break-word;
}
.msg-self .msg-content { background: #1989fa; color: #fff; border-radius: 8px 0 8px 8px; }
.msg-other .msg-content { background: #fff; color: #333; border-radius: 0 8px 8px 8px; }
.msg-time { font-size: 11px; color: #999; margin-top: 4px; }
.chat-input {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: #fff; border-top: 1px solid #eee;
}
.chat-input .van-field { flex: 1; }
</style>
