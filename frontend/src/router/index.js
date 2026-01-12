import { createRouter, createWebHistory } from 'vue-router'

// Lazy load views
const Dashboard = () => import('../views/Dashboard.vue')
const Companies = () => import('../views/Companies.vue')
const Automation = () => import('../views/Automation.vue')

const routes = [
    { path: '/', redirect: '/dashboard' },
    { path: '/dashboard', component: Dashboard, name: 'Dashboard' },
    { path: '/empresas', component: Companies, name: 'Empresas' },
    { path: '/automatizacion', component: Automation, name: 'Automatizacion' },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

export default router
