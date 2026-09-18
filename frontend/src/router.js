import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from './views/DashboardView.vue'
import ChemicalsView from './views/ChemicalsView.vue'
import ChemicalFormView from './views/ChemicalFormView.vue'
import ChemicalDetailView from './views/ChemicalDetailView.vue'
import WarehousesView from './views/WarehousesView.vue'
import ScanView from './views/ScanView.vue'
import MovementsView from './views/MovementsView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: DashboardView },
    { path: '/chemicals', component: ChemicalsView },
    { path: '/chemicals/new', component: ChemicalFormView },
    { path: '/chemicals/:id', component: ChemicalDetailView },
    { path: '/chemicals/:id/edit', component: ChemicalFormView },
    { path: '/warehouses', component: WarehousesView },
    { path: '/scan', component: ScanView },
    { path: '/movements', component: MovementsView }
  ]
})
