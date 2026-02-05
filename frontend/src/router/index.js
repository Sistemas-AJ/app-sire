import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import Companies from '../views/Companies.vue'
import Automation from '../views/Automation.vue'
import Welcome from '../views/Welcome.vue'
import Proposal from '../views/Proposal.vue'
import InvoicesDownload from '../views/InvoicesDownload.vue'
import InvoicesRepository from '../views/InvoicesRepository.vue'
import Login from '../views/Login.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { guest: true }
    },
    {
        path: '/',
        redirect: '/dashboard'
    },
    {
        path: '/welcome',
        name: 'Welcome',
        component: Welcome,
        meta: { requiresAuth: true }
    },
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true }
    },
    {
        path: '/empresas',
        name: 'Companies',
        component: Companies,
        meta: { requiresAuth: true }
    },
    {
        path: '/automatizacion',
        name: 'Automation',
        component: Automation,
        meta: { requiresAuth: true }
    },
    {
        path: '/comprobantes/propuesta',
        name: 'Propuesta',
        component: Proposal,
        meta: { requiresAuth: true }
    },
    {
        path: '/comprobantes/descarga',
        name: 'DescargaCPE',
        component: InvoicesDownload,
        meta: { requiresAuth: true }
    },
    {
        path: '/comprobantes/repositorio',
        name: 'RepositorioCPE',
        component: InvoicesRepository,
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token');

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!token) {
            next({ name: 'Login' });
        } else {
            next();
        }
    } else if (to.matched.some(record => record.meta.guest)) {
        if (token) {
            next({ name: 'Dashboard' });
        } else {
            next();
        }
    } else {
        next();
    }
});

export default router
