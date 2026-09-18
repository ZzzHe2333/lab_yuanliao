<script setup>
import { onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'
import StatusBadge from '../components/StatusBadge.vue'

const rows = ref([]), warehouses = ref([]), loading = ref(false), error = ref('')
const filters = ref({ search: '', warehouse_id: '', status: '', alert: '', sort: 'id', order: 'desc' })
let timer
async function load() { loading.value = true; error.value=''; try { rows.value = await api.chemicals(filters.value) } catch(e){ error.value=e.message } finally { loading.value=false } }
onMounted(async () => { warehouses.value = await api.warehouses(); load() })
watch(filters, () => { clearTimeout(timer); timer=setTimeout(load, 200) }, { deep:true })
async function remove(c) { if (!confirm(`确定删除“${c.name}”吗？`)) return; try { await api.deleteChemical(c.id); await load() } catch(e){ alert(e.message) } }
</script>
<template>
  <PageHeader title="原料库存" subtitle="搜索、筛选和管理实验室全部原料">
    <RouterLink class="btn primary" to="/chemicals/new">+ 新增原料</RouterLink>
  </PageHeader>
  <section class="panel filter-panel">
    <input v-model="filters.search" class="input search" placeholder="搜索名称 / CAS / 批号 / 供应商" />
    <select v-model="filters.warehouse_id" class="input"><option value="">全部仓库</option><option v-for="w in warehouses" :value="w.id" :key="w.id">{{ w.name }}</option></select>
    <select v-model="filters.status" class="input"><option value="">全部状态</option><option>良好</option><option>一般</option><option>低库存</option><option>停用</option></select>
    <select v-model="filters.alert" class="input"><option value="">全部预警</option><option value="expired">仅已过期</option><option value="low">仅低库存</option></select>
    <select v-model="filters.sort" class="input"><option value="id">最新登记</option><option value="name">名称</option><option value="purchase_date">采购日期</option><option value="expiration_date">到期日期</option><option value="quantity">库存量</option></select>
    <button class="btn ghost" @click="filters.order = filters.order === 'asc' ? 'desc' : 'asc'">{{ filters.order === 'asc' ? '↑ 升序' : '↓ 降序' }}</button>
  </section>
  <div v-if="error" class="alert danger-box">{{ error }}</div>
  <section class="panel">
    <div class="panel-title"><div><h2>库存列表</h2><p>{{ loading ? '加载中...' : `共 ${rows.length} 条` }}</p></div></div>
    <div class="table-wrap"><table><thead><tr><th>原料</th><th>位置</th><th>采购 / 到期</th><th>库存</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="c in rows" :key="c.id">
          <td><RouterLink :to="`/chemicals/${c.id}`" class="strong-link">{{ c.name }}</RouterLink><span v-if="c.is_new_material" class="new-material-tag inline-tag">新原料</span><small class="block">CAS {{ c.cas || '-' }} · 批号 {{ c.batch_no || '-' }}</small></td>
          <td>{{ c.warehouse_name || '-' }}<small class="block">{{ [c.room, c.cabinet && `柜 ${c.cabinet}`, c.shelf && `层 ${c.shelf}`].filter(Boolean).join(' / ') || '未指定库位' }}</small></td>
          <td>{{ c.purchase_date || '-' }}<small class="block" :class="{ red: c.is_expired }">到期 {{ c.expiration_date || '-' }}</small></td>
          <td><b :class="{ red: c.is_negative_stock }">{{ c.quantity }}</b> {{ c.unit }}<small class="block" v-if="c.is_negative_stock">配方/实验已超前领用，待补入库</small><small class="block" v-else-if="c.low_stock_threshold">预警 ≤ {{ c.low_stock_threshold }} {{ c.unit }}</small></td>
          <td><StatusBadge :status="c.status" :expired="c.is_expired" :low="c.is_low_stock" :negative="c.is_negative_stock" /></td>
          <td class="actions"><RouterLink class="link-btn" :to="`/chemicals/${c.id}/edit`">编辑</RouterLink><button class="link-btn danger-link" @click="remove(c)">删除</button></td>
        </tr>
        <tr v-if="!loading && !rows.length"><td colspan="6" class="empty">没有符合条件的原料。</td></tr>
      </tbody></table></div>
  </section>
</template>
