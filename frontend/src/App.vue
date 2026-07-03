<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { api, type Candle, type FilterTemplate, type IndicatorCondition, type Market, type ScreenResult, type Stock, type StockDetail, type WatchlistItem, type Watchlists } from './api'

const market = ref<Market>('cn')
const stocks = ref<Stock[]>([])
const results = ref<ScreenResult[]>([])
const watchlists = ref<Watchlists>({ groups: {} })
const templates = ref<FilterTemplate[]>([])
const detail = ref<StockDetail | null>(null)
const intraday = ref<Candle[]>([])
const activeTab = ref<'screen' | 'watchlist'>('screen')
const status = ref('准备就绪')
const search = ref('')
const templateName = ref('我的技术筛选')
const watchGroup = ref('默认')

const conditions = reactive<IndicatorCondition[]>([
  { indicator: 'ma', period: 5, operator: '>', value: 1, enabled: true },
  { indicator: 'macd', period: 12, operator: '>', value: 0, enabled: true },
  { indicator: 'rsi', period: 14, operator: '>', value: 10, enabled: true }
])

const filteredResults = computed(() => {
  const keyword = search.value.trim().toLowerCase()
  if (!keyword) return results.value
  return results.value.filter(item => item.symbol.toLowerCase().includes(keyword) || item.name.toLowerCase().includes(keyword))
})

async function loadBaseData() {
  status.value = '正在加载基础数据'
  stocks.value = await api.universe(market.value)
  watchlists.value = await api.watchlists()
  templates.value = await api.templates()
  status.value = '基础数据已加载'
}

async function runScreen() {
  status.value = '正在执行技术指标筛选'
  detail.value = null
  const preferredSymbols = market.value === 'cn' ? ['000001', '600519', '300750'] : ['AAPL', 'MSFT', 'NVDA']
  const availableSymbols = new Set(stocks.value.map(stock => stock.symbol))
  const symbols = preferredSymbols.filter(symbol => availableSymbols.has(symbol))
  const fallbackSymbols = stocks.value.slice(0, 5).map(stock => stock.symbol)
  const screenSymbols = symbols.length ? symbols : fallbackSymbols.length ? fallbackSymbols : preferredSymbols
  const response = await api.screen(market.value, conditions, screenSymbols)
  results.value = response.results.sort((left, right) => right.change_percent - left.change_percent)
  status.value = response.results.length ? `筛选完成，扫描 ${screenSymbols.length} 只，命中 ${response.results.length} 只，失败 ${response.failed_count} 只` : `扫描 ${screenSymbols.length} 只后无匹配股票，请放宽条件`
}

async function addToWatchlist(item: ScreenResult) {
  await api.addWatchlist({ group: watchGroup.value || '默认', market: item.market, symbol: item.symbol, name: item.name })
  watchlists.value = await api.watchlists()
  item.is_watchlisted = true
  status.value = `${item.name} 已加入自选股`
}

async function removeWatchlistItem(id: string) {
  await api.deleteWatchlist(id)
  watchlists.value = await api.watchlists()
  status.value = '自选股已删除'
}

async function saveTemplate() {
  const template = await api.createTemplate({ name: templateName.value || '未命名模板', market: market.value, conditions })
  templates.value = await api.templates()
  status.value = `模板已保存：${template.name}`
}

async function loadTemplate(template: FilterTemplate) {
  market.value = template.market
  conditions.splice(0, conditions.length, ...template.conditions.map(item => ({ ...item })))
  await loadBaseData()
  status.value = `模板已加载：${template.name}`
}

async function updateTemplate(template: FilterTemplate) {
  await api.updateTemplate(template.id, { name: template.name, market: market.value, conditions })
  templates.value = await api.templates()
  status.value = `模板已更新：${template.name}`
}

async function deleteTemplate(id: string) {
  await api.deleteTemplate(id)
  templates.value = await api.templates()
  status.value = '模板已删除'
}

async function openDetail(item: ScreenResult | Stock | WatchlistItem) {
  detail.value = await api.detail(item.market, item.symbol)
  try {
    intraday.value = await api.intraday(item.market, item.symbol)
  } catch {
    intraday.value = []
  }
  status.value = `已打开 ${item.name} 详情`
}

onMounted(loadBaseData)
</script>

<template>
  <main class="shell">
    <header class="hero">
      <div>
        <p class="eyebrow">Local Quant Research</p>
        <h1>StockSelection 量化选股工具</h1>
        <p>基于日线技术指标筛选 A 股和美股主流股票，管理自选股和筛选模板。</p>
      </div>
      <div class="status">{{ status }}</div>
    </header>

    <nav class="tabs">
      <button :class="{ active: activeTab === 'screen' }" @click="activeTab = 'screen'">技术筛选</button>
      <button :class="{ active: activeTab === 'watchlist' }" @click="activeTab = 'watchlist'">自选股</button>
    </nav>

    <section v-if="activeTab === 'screen'" class="grid">
      <aside class="panel controls">
        <h2>筛选条件</h2>
        <label>市场</label>
        <select v-model="market" @change="loadBaseData">
          <option value="cn">A 股</option>
          <option value="us">美股</option>
        </select>

        <label>自选分组</label>
        <input v-model="watchGroup" placeholder="默认" />

        <div class="condition" v-for="condition in conditions" :key="condition.indicator">
          <label><input type="checkbox" v-model="condition.enabled" /> {{ condition.indicator.toUpperCase() }}</label>
          <input type="number" v-model.number="condition.period" min="1" />
          <select v-model="condition.operator">
            <option>&gt;</option>
            <option>&gt;=</option>
            <option>&lt;</option>
            <option>&lt;=</option>
          </select>
          <input type="number" v-model.number="condition.value" />
        </div>

        <button class="primary" @click="runScreen">执行筛选</button>

        <h3>模板</h3>
        <input v-model="templateName" placeholder="模板名称" />
        <button @click="saveTemplate">保存当前模板</button>
        <div class="template" v-for="template in templates" :key="template.id">
          <span>{{ template.name }}</span>
          <button @click="loadTemplate(template)">加载</button>
          <button @click="updateTemplate(template)">更新</button>
          <button @click="deleteTemplate(template.id)">删除</button>
        </div>
      </aside>

      <section class="panel results">
        <div class="section-head">
          <h2>筛选结果</h2>
          <input v-model="search" placeholder="搜索代码或名称" />
        </div>
        <table>
          <thead>
            <tr>
              <th>代码</th>
              <th>名称</th>
              <th>最新价</th>
              <th>涨跌幅</th>
              <th>成交量</th>
              <th>命中原因</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filteredResults" :key="`${item.market}-${item.symbol}`">
              <td>{{ item.symbol }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.latest_price }}</td>
              <td :class="item.change_percent >= 0 ? 'up' : 'down'">{{ item.change_percent }}%</td>
              <td>{{ item.volume.toLocaleString() }}</td>
              <td>{{ item.matched_reasons.join('；') }}</td>
              <td>
                <button @click="openDetail(item)">详情</button>
                <button :disabled="item.is_watchlisted" @click="addToWatchlist(item)">{{ item.is_watchlisted ? '已自选' : '加自选' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="!filteredResults.length" class="empty">暂无结果</p>
      </section>
    </section>

    <section v-if="activeTab === 'watchlist'" class="panel">
      <h2>自选股分组</h2>
      <div class="watch-group" v-for="(items, group) in watchlists.groups" :key="group">
        <h3>{{ group }}</h3>
        <div class="watch-item" v-for="item in items" :key="item.id">
          <span>{{ item.symbol }} · {{ item.name }} · {{ item.market }}</span>
          <button @click="openDetail(item)">详情</button>
          <button @click="removeWatchlistItem(item.id)">删除</button>
        </div>
      </div>
      <p v-if="!Object.keys(watchlists.groups).length" class="empty">暂无自选股</p>
    </section>

    <section v-if="detail" class="panel detail">
      <div class="section-head">
        <h2>{{ detail.stock.name }} {{ detail.stock.symbol }}</h2>
        <span>{{ detail.is_watchlisted ? '已加入自选' : '未加入自选' }}</span>
      </div>
      <div class="cards">
        <div>最新价 <strong>{{ detail.latest.close }}</strong></div>
        <div>MA5 <strong>{{ detail.indicators.ma5 ?? '-' }}</strong></div>
        <div>MA20 <strong>{{ detail.indicators.ma20 ?? '-' }}</strong></div>
        <div>MACD <strong>{{ detail.indicators.macd ?? '-' }}</strong></div>
        <div>RSI14 <strong>{{ detail.indicators.rsi14 ?? '-' }}</strong></div>
      </div>
      <h3>分钟走势</h3>
      <div class="intraday">
        <span v-for="candle in intraday" :key="candle.date">{{ candle.date }} {{ candle.close }}</span>
      </div>
    </section>
  </main>
</template>
