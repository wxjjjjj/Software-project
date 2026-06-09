<template>
  <div class="search-page">

    <!-- ── 路线 ── -->
    <div class="form-section">
      <div class="fs-header">
        <span class="fs-dot"></span>行程路线
      </div>
      <div class="route-inputs">
        <div class="ri-row">
          <span class="ri-icon start">●</span>
          <div class="loc-wrap">
            <van-field
              v-model="query.start_loc"
              placeholder="出发地（不填则不限）"
              clearable
              @input="filterSug('start')"
              @blur="() => hideDropdown('start')"
              class="ri-field"
            />
            <div v-show="showStart && sugStart.length" class="loc-suggestions">
              <div
                v-for="s in sugStart" :key="s.name"
                class="loc-suggestion-item"
                @mousedown.prevent="pickSug('start', s)"
              >{{ s.name }}</div>
            </div>
          </div>
        </div>
        <div class="ri-connector">
          <span class="ri-vline"></span>
        </div>
        <div class="ri-row">
          <span class="ri-icon end">●</span>
          <div class="loc-wrap">
            <van-field
              v-model="query.end_loc"
              placeholder="目的地（不填则不限）"
              clearable
              @input="filterSug('end')"
              @blur="() => hideDropdown('end')"
              class="ri-field"
            />
            <div v-show="showEnd && sugEnd.length" class="loc-suggestions">
              <div
                v-for="s in sugEnd" :key="s.name"
                class="loc-suggestion-item"
                @mousedown.prevent="pickSug('end', s)"
              >{{ s.name }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 时间 ── -->
    <div class="form-section">
      <div class="fs-header">
        <span class="fs-dot"></span>出发时间范围
      </div>
      <van-cell-group inset>
        <van-field v-model="query.time_from" label="最早" type="datetime-local" />
        <van-field v-model="query.time_to"   label="最晚" type="datetime-local" />
      </van-cell-group>
    </div>

    <!-- ── 标签筛选 ── -->
    <div class="form-section">
      <div class="fs-header">
        <span class="fs-dot"></span>标签筛选
      </div>
      <div class="tag-panel">
        <div class="tag-cloud">
          <span
            v-for="t in AVAILABLE_TAGS" :key="t"
            class="tag-chip"
            :class="{ active: selectedTags.includes(t) }"
            @click="toggleTag(t)"
          >{{ t }}</span>
          <span
            v-for="t in customTags" :key="'c-'+t"
            class="tag-chip custom active"
          >{{ t }}<span class="tag-chip-close" @click.stop="removeCustomTag(t)">×</span></span>
        </div>
        <div class="custom-tag-row">
          <input
            v-model="customTagInput"
            placeholder="自定义标签，回车添加"
            class="custom-input"
            @keyup.enter="addCustomTag"
          />
          <button type="button" class="custom-add-btn" @click="addCustomTag">＋</button>
        </div>
      </div>
    </div>

    <!-- ── 搜索按钮 ── -->
    <div class="submit-wrap">
      <van-button
        round block type="primary" size="large"
        :loading="loading" loading-text="搜索中…"
        class="submit-btn"
        @click="doSearch"
      >搜索订单</van-button>
    </div>

    <!-- ── 结果 ── -->
    <template v-if="searched">
      <div class="result-bar">
        <span class="rh-count">找到 <b>{{ orders.length }}</b> 条订单</span>
        <span v-if="selectedTags.length + customTags.length" class="rh-tags">
          · {{ [...selectedTags, ...customTags].join(' / ') }}
        </span>
      </div>
      <van-loading v-if="loading" class="page-loading" type="spinner" color="#165DFF" />
      <van-empty v-else-if="!orders.length" description="没有符合条件的订单" />
      <template v-else>
        <div
          v-for="(o, i) in orders"
          :key="o.order_id"
          class="order-card"
          :class="`s-${o.status}`"
          :style="{ animationDelay: `${i * 0.05}s` }"
          @click="$router.push(`/passenger/orders/${o.order_id}`)"
        >
          <div class="card-head">
            <van-tag :type="statusType(o.status)">{{ statusLabel(o.status) }}</van-tag>
            <span class="card-price">¥{{ o.expected_price }}</span>
          </div>
          <div class="card-route">
            <div class="route-node">
              <span class="nd s"></span>
              <span class="nd-name">{{ o.start_loc }}</span>
            </div>
            <div class="route-dash"><span></span></div>
            <div class="route-node">
              <span class="nd e"></span>
              <span class="nd-name">{{ o.end_loc }}</span>
            </div>
          </div>
          <div class="card-meta">
            <span>🕐 {{ fmtTime(o.depart_time_from) }}</span>
            <span class="seats-info">
              <span class="mini-bar">
                <span class="mini-fill" :style="{ width: `${Math.min((o.seats_joined||0)/(o.seats_needed||1)*100,100)}%` }"></span>
              </span>
              剩 {{ o.remaining_seats }} 座
            </span>
          </div>
          <div class="card-tags" v-if="o.tags?.length">
            <span v-for="t in o.tags" :key="t" class="mini-tag">{{ t }}</span>
          </div>
        </div>
      </template>
    </template>

  </div>
</template>

<script setup>
import { ref } from 'vue'
import { rideApi, STATUS_MAP, formatTime, AVAILABLE_TAGS, searchPlaces } from '@/api/ride.js'

const query          = ref({ start_loc: '', end_loc: '', time_from: '', time_to: '' })
const selectedTags   = ref([])
const customTags     = ref([])
const customTagInput = ref('')
const orders   = ref([])
const loading  = ref(false)
const searched = ref(false)
const showStart = ref(false)
const showEnd   = ref(false)
const sugStart  = ref([])
const sugEnd    = ref([])

const statusLabel = (s) => STATUS_MAP[s]?.label || s
const statusType  = (s) => STATUS_MAP[s]?.type  || 'default'
const fmtTime     = (s) => formatTime(s)

function toggleTag(t) {
  const idx = selectedTags.value.indexOf(t)
  if (idx >= 0) selectedTags.value.splice(idx, 1)
  else selectedTags.value.push(t)
}

function addCustomTag() {
  const t = customTagInput.value.trim()
  if (!t || customTags.value.includes(t) || selectedTags.value.includes(t)) {
    customTagInput.value = ''; return
  }
  customTags.value.push(t)
  customTagInput.value = ''
}

function removeCustomTag(t) {
  customTags.value = customTags.value.filter(x => x !== t)
}

function hideDropdown(field) {
  setTimeout(() => {
    if (field === 'start') showStart.value = false
    else showEnd.value = false
  }, 150)
}

let sugTimer = null
async function filterSug(field) {
  const kw = field === 'start' ? query.value.start_loc : query.value.end_loc
  if (!kw?.trim()) {
    if (field === 'start') { sugStart.value = []; showStart.value = false }
    else { sugEnd.value = []; showEnd.value = false }
    return
  }
  clearTimeout(sugTimer)
  sugTimer = setTimeout(async () => {
    const results = await searchPlaces(kw)
    if (field === 'start') { sugStart.value = results; showStart.value = results.length > 0 }
    else { sugEnd.value = results; showEnd.value = results.length > 0 }
  }, 300)
}

function pickSug(field, s) {
  if (field === 'start') { query.value.start_loc = s.name; showStart.value = false }
  else { query.value.end_loc = s.name; showEnd.value = false }
}

async function doSearch() {
  loading.value = true; searched.value = false
  try {
    const res = await rideApi.searchOrders({
      ...query.value,
      tags: [...selectedTags.value, ...customTags.value]
    })
    orders.value = res.items || []
    searched.value = true
  } catch {
    orders.value = []; searched.value = true
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.search-page { padding-bottom: 32px; }

/* ── 区块 ── */
.form-section { margin-bottom: 10px; }
.fs-header {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: #1e293b;
  padding: 12px 4px 8px; letter-spacing: .3px;
}
.fs-dot { width: 8px; height: 8px; border-radius: 50%; background: #165DFF; flex-shrink: 0; }

/* ── 路线输入 ── */
.route-inputs {
  background: #fff; border-radius: 16px;
  padding: 6px 16px 10px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
}
.ri-row { display: flex; align-items: center; gap: 10px; }
.ri-icon { font-size: 11px; flex-shrink: 0; line-height: 1; }
.ri-icon.start { color: #165DFF; }
.ri-icon.end   { color: #f97316; }
.loc-wrap { flex: 1; position: relative; }
.ri-field { padding: 10px 0; --van-cell-horizontal-padding: 0; }
.ri-connector { padding: 2px 0 2px 5px; }
.ri-vline {
  display: block; width: 1.5px; height: 18px;
  background: repeating-linear-gradient(180deg,#cbd5e1 0,#cbd5e1 4px,transparent 4px,transparent 8px);
  margin-left: 2px;
}
.loc-suggestions {
  position: absolute; top: 100%; left: 0; right: 0; z-index: 100;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0,0,0,.1); overflow: hidden; margin-top: 2px;
}
.loc-suggestion-item {
  padding: 10px 14px; font-size: 13px; color: #1e293b; cursor: pointer;
  border-bottom: 1px solid #f1f5f9;
}
.loc-suggestion-item:last-child { border-bottom: none; }
.loc-suggestion-item:active { background: #f0f5ff; }

/* ── 标签 ── */
.tag-panel {
  background: #fff; border-radius: 16px;
  padding: 14px 16px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
}
.tag-cloud { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.custom-tag-row { display: flex; align-items: center; gap: 8px; }
.custom-input {
  flex: 1; border: 1.5px solid #e2e8f0; border-radius: 20px;
  padding: 6px 14px; font-size: 13px; outline: none; color: #1e293b;
  transition: border-color .15s;
}
.custom-input:focus { border-color: #165DFF; }
.custom-add-btn {
  width: 30px; height: 30px; border-radius: 50%;
  border: 1.5px solid #165DFF; background: transparent;
  color: #165DFF; font-size: 18px; line-height: 28px;
  text-align: center; cursor: pointer; flex-shrink: 0;
  transition: all .15s;
}
.custom-add-btn:hover { background: #165DFF; color: #fff; }
.tag-chip {
  padding: 5px 12px; border-radius: 20px; font-size: 12px;
  border: 1.5px solid #e2e8f0; background: #fff; color: #64748b;
  cursor: pointer; transition: all .15s; user-select: none;
}
.tag-chip.active {
  background: #165DFF; border-color: #165DFF;
  color: #fff; box-shadow: 0 3px 10px rgba(22,93,255,.3);
}
.tag-chip-close { margin-left: 4px; opacity: .8; cursor: pointer; }

/* ── 搜索按钮 ── */
.submit-wrap { padding: 12px 0 8px; }
.submit-btn  { box-shadow: 0 6px 20px rgba(22,93,255,.35) !important; }

/* ── 结果 ── */
.result-bar {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: #64748b; padding: 8px 2px 10px;
}
.rh-count b { color: #165DFF; font-weight: 700; }
.rh-tags { color: #165DFF; font-size: 12px; font-weight: 500; }

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.order-card {
  background: #fff; border-radius: 16px;
  padding: 13px 16px; margin-bottom: 10px;
  box-shadow: 0 2px 14px rgba(22,93,255,.07);
  cursor: pointer; position: relative;
  border-left: 3px solid #e2e8f0;
  animation: fadeUp .28s ease both;
  transition: transform .14s;
}
.order-card:active { transform: scale(.985); }
.order-card.s-published { border-left-color: #165DFF; }
.order-card.s-locked    { border-left-color: #f97316; }
.order-card.s-completed { border-left-color: #10b981; }
.order-card.s-full      { border-left-color: #f59e0b; }

.card-head {
  display: flex; align-items: center; gap: 7px;
  margin-bottom: 10px;
}
.card-price { margin-left: auto; font-size: 16px; font-weight: 800; color: #f97316; }

.card-route {
  display: flex; align-items: center;
  gap: 0; margin-bottom: 9px;
}
.route-node { display: flex; align-items: center; gap: 6px; }
.nd { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.nd.s { background: #165DFF; }
.nd.e { background: #f97316; }
.nd-name { font-size: 15px; font-weight: 700; color: #1e293b; }
.route-dash { flex: 1; padding: 0 8px; }
.route-dash span {
  display: block; height: 1.5px;
  background: repeating-linear-gradient(90deg,#cbd5e1 0,#cbd5e1 4px,transparent 4px,transparent 8px);
}

.card-meta {
  display: flex; justify-content: space-between; align-items: center;
  font-size: 12px; color: #64748b; margin-bottom: 6px;
}
.seats-info { display: flex; align-items: center; gap: 6px; }
.mini-bar { width: 36px; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
.mini-fill { height: 100%; background: #165DFF; border-radius: 2px; }

.card-tags { display: flex; gap: 5px; flex-wrap: wrap; }
.mini-tag {
  padding: 2px 8px; border-radius: 20px; font-size: 11px;
  background: #f0f5ff; color: #165DFF; border: 1px solid #dce8ff;
}

.page-loading { display: flex; justify-content: center; padding: 40px 0; }
</style>
