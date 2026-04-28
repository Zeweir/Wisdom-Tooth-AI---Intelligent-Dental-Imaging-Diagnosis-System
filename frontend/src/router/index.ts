import { createRouter, createWebHistory } from 'vue-router'

import AppShell from '../layouts/AppShell.vue'

const AuthCallbackPanel = () => import('../components/AuthCallbackPanel.vue')
const AccessPage = () => import('../pages/AccessPage.vue')
const AuditPage = () => import('../pages/AuditPage.vue')
const HomePage = () => import('../pages/HomePage.vue')
const WorkspacePage = () => import('../pages/WorkspacePage.vue')

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/callback',
      name: 'callback',
      component: AuthCallbackPanel
    },
    {
      path: '/',
      component: AppShell,
      children: [
        {
          path: '',
          name: 'home',
          component: HomePage
        },
        {
          path: 'workspace',
          name: 'workspace',
          component: WorkspacePage
        },
        {
          path: 'access',
          name: 'access',
          component: AccessPage
        },
        {
          path: 'audit',
          name: 'audit',
          component: AuditPage
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/'
    }
  ],
  scrollBehavior() {
    return { top: 0 }
  }
})

export default router
