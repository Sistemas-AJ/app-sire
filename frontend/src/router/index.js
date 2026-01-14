import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Companies from '../views/Companies.vue'
import Automation from '../views/Automation.vue'
import Welcome from '../views/Welcome.vue'
import Proposal from '../views/Proposal.vue'
import InvoicesDownload from '../views/InvoicesDownload.vue'
import InvoicesRepository from '../views/InvoicesRepository.vue'

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
        component: Proposal
    },
    {
        path: '/comprobantes/descarga',
        name: 'DescargaCPE',
        component: InvoicesDownload
    },
    {
        path: '/comprobantes/repositorio',
        name: 'RepositorioCPE',
        component: InvoicesRepository
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
