import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Companies from '../views/Companies.vue'
import Automation from '../views/Automation.vue'
import Welcome from '../views/Welcome.vue'
import Invoices from '../views/Invoices.vue'

const routes = [
    {
        path: '/',
        redirect: '/dashboard' // Could be welcome depending on auth state
    },
    {
        path: '/welcome',
        name: 'Welcome',
        component: Welcome
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard
    },
    {
        path: '/empresas',
        name: 'Companies',
        component: Companies
    },
    {
        path: '/automatizacion',
        name: 'Automation',
        component: Automation
    },
    {
        path: '/comprobantes/propuesta',
        name: 'Propuesta',
        component: Invoices
    },
    {
        path: '/comprobantes/descarga',
        name: 'DescargaCPE',
        component: Invoices
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
