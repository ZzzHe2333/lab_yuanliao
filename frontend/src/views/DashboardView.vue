<script setup>
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const data = ref({ total_chemicals: 0, warehouses: 0, expired: 0, low_stock: 0, recent: [] })
const error = ref('')
onMounted(async () => { try { data.value = await api.stats() } catch (e) { error.value = e.message } })
</script>
<template>
  <PageHeader title="实验室原料总览" subtitle="集中查看库存、过期与低库存情况">
    <RouterLink class="btn ghost" to="/movements">库存操作</RouterLink>
    <RouterLink class="btn primary" to="/chemicals/new">+ 新增原料</RouterLink>
  </PageHeader>
  <div v-if="error" class="alert danger-box">{{ error }}</div>
  <section class="stat-grid">
    <div class="stat-card"><span>原料总数</span><b>{{ data.total_chemicals }}</b><small>当前登记原料</small></div>
    <div class="stat-card"><span>仓库数量</span><b>{{ data.warehouses }}</b><small>已配置库区</small></div>
    <div class="stat-card alert-stat"><span>已过期</span><b>{{ data.expired }}</b><small>需要优先处理</small></div>
    <div class="stat-card warn-stat"><span>低库存</span><b>{{ data.low_stock }}</b><small>达到预警阈值</small></div>
  </section>
  <section class="panel">
    <div class="panel-title"><div><h2>最近新增</h2><p>最新登记的 6 条原料</p></div><RouterLink to="/chemicals">查看全部 →</RouterLink></div>
    <div class="table-wrap">
      <table><thead><tr><th>名称</th><th>CAS</th><th>仓库</th><th>库存</th><th>状态</th></tr></thead>
      <tbody>
        <tr v-for="c in data.recent" :key="c.id">
          <td><RouterLink :to="`/chemicals/${c.id}`" class="strong-link">{{ c.name }}</RouterLink><small class="block">#{{ c.id }} · {{ c.batch_no || '无批号' }}</small></td>
          <td>{{ c.cas || '-' }}</td><td>{{ c.warehouse_name || '-' }}</td><td>{{ c.quantity }} {{ c.unit }}</td>
          <td><StatusBadge :status="c.status" :expired="c.is_expired" :low="c.is_low_stock" /></td>
        </tr>
        <tr v-if="!data.recent.length"><td colspan="5" class="empty">还没有原料，先新增一条。</td></tr>
      </tbody></table>
    </div>
  </section>
</template>
