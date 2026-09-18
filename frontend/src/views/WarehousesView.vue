<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'
import PageHeader from '../components/PageHeader.vue'
const rows=ref([]), error=ref(''), form=reactive({name:'',code:'',location:'',description:''})
async function load(){ rows.value=await api.warehouses() }
onMounted(load)
async function add(){ try{ await api.createWarehouse(form); Object.assign(form,{name:'',code:'',location:'',description:''}); error.value=''; await load() }catch(e){error.value=e.message} }
async function remove(w){ if(!confirm(`删除仓库“${w.name}”？`)) return; try{await api.deleteWarehouse(w.id); await load()}catch(e){alert(e.message)} }
</script>
<template>
  <PageHeader title="仓库管理" subtitle="单账户统一管理多个实验室仓库和库区" />
  <div v-if="error" class="alert danger-box">{{ error }}</div>
  <div class="split-layout">
    <section class="panel"><div class="panel-title"><div><h2>仓库列表</h2><p>原料可分配到不同仓库</p></div></div>
      <div class="warehouse-list"><div v-for="w in rows" :key="w.id" class="warehouse-card"><div><h3>{{ w.name }}</h3><p>{{ w.code || '无代码' }} · {{ w.location || '未填写位置' }}</p><small>{{ w.description || '无备注' }}</small></div><div class="warehouse-meta"><b>{{ w.chemical_count }}</b><span>种原料</span><button class="link-btn danger-link" :disabled="w.chemical_count>0" @click="remove(w)">删除</button></div></div></div>
    </section>
    <form class="panel mini-form" @submit.prevent="add"><h2>新增仓库</h2><label>仓库名称 *<input v-model="form.name" class="input" required /></label><label>仓库代码<input v-model="form.code" class="input" placeholder="例如 MAIN" /></label><label>位置<input v-model="form.location" class="input" /></label><label>说明<textarea v-model="form.description" class="input textarea" rows="3"></textarea></label><button class="btn primary">保存仓库</button></form>
  </div>
</template>
