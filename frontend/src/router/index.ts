import { createRouter, createWebHistory } from 'vue-router'

import AppLayout from '../layouts/AppLayout.vue'

const AuthCallbackPanel = () => import('../components/AuthCallbackPanel.vue')
const AccessPage = () => import('../pages/AccessPage.vue')
const AuditPage = () => import('../pages/AuditPage.vue')
const DatasetPage = () => import('../pages/DatasetPage.vue')
const HomePage = () => import('../pages/HomePage.vue')
const PatientPage = () => import('../pages/PatientPage.vue')
const SettingsPage = () => import('../pages/SettingsPage.vue')
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
      component: AppLayout,
      children: [
        {
          path: '',
          name: 'home',
          component: HomePage,
          meta: {
            title: '工作台',
            subtitle: '牙齿影像智能诊断系统',
          },
        },
        {
          path: 'patients',
          name: 'patients',
          component: PatientPage,
          meta: {
            title: '患者管理',
            subtitle: '患者档案与历史病例',
          },
        },
        {
          path: 'workspace',
          name: 'workspace',
          component: WorkspacePage,
          meta: {
            title: '影像工作站',
            subtitle: '上传、AI 诊断与报告审核',
          },
        },
        {
          path: 'upload',
          name: 'upload',
          redirect: (to) => ({ path: '/workspace', query: to.query }),
        },
        {
          path: 'diagnosis',
          name: 'diagnosis',
          redirect: (to) => ({ path: '/workspace', query: to.query }),
        },
        {
          path: 'reports',
          name: 'reports',
          redirect: (to) => ({ path: '/workspace', query: to.query }),
        },
        {
          path: 'settings',
          name: 'settings',
          component: SettingsPage,
          meta: {
            title: '系统设置',
            subtitle: '系统能力与更多工具',
          },
        },
        {
          path: 'datasets',
          name: 'datasets',
          component: DatasetPage,
          meta: {
            title: '数据集中心',
            subtitle: '公开数据与模型评估',
          },
        },
        {
          path: 'access',
          name: 'access',
          component: AccessPage,
          meta: {
            title: '权限中心',
            subtitle: '角色与能力说明',
          },
        },
        {
          path: 'audit',
          name: 'audit',
          component: AuditPage,
          meta: {
            title: '审计中心',
            subtitle: '关键操作留痕追踪',
          },
        },
      ],
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
