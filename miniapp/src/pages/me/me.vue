<script setup lang="ts">
import Taro, { useDidShow } from '@tarojs/taro'
import { useAuthStore } from '../../stores/auth'
import CustomTabBar from '../../components/CustomTabBar.vue'

const auth = useAuthStore()

useDidShow(async () => { await auth.init() })

function handleLogout() {
  Taro.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    success: (res) => { if (res.confirm) auth.logout() },
  })
}

function goPage(path: string) { Taro.navigateTo({ url: path }) }
function showComingSoon() { Taro.showToast({ title: '功能开发中', icon: 'none' }) }
</script>

<template>
  <view class="me-page">
    <!-- Profile Card -->
    <view class="me-profile-wrap">
      <view class="me-profile-bg" />
      <view class="me-profile-card">
        <view class="me-avatar" :class="{ 'me-avatar-placeholder': !auth.isLoggedIn }">
          <text class="me-avatar-text">{{ auth.isLoggedIn ? auth.displayName.slice(0, 1) : '?' }}</text>
        </view>

        <template v-if="auth.isLoggedIn">
          <text class="me-name">{{ auth.displayName }}</text>
          <view class="me-role">{{ auth.user?.role_label || auth.role }}</view>
          <text class="me-id">ID: {{ auth.user?.user_id?.slice(0, 8) || '' }}...</text>
        </template>
        <template v-else>
          <text class="me-name">未登录</text>
          <text class="me-sub">登录后享受完整功能</text>
          <view class="me-login-btn" @tap="Taro.switchTab({ url: '/pages/index/index' })">
            <text>前往登录</text>
          </view>
        </template>
      </view>
    </view>

    <!-- Permission Tags -->
    <view class="me-perm" v-if="auth.isLoggedIn">
      <text class="me-perm-title">账号权限</text>
      <view class="me-perm-tags">
        <view v-for="p in auth.user?.permissions || []" :key="p" class="me-perm-tag">
          <text>{{ {
            'read:images': '查看影像', 'upload:images': '上传影像',
            'review:reports': '审核报告', 'finalize:reports': '正式确认',
          }[p] || p }}</text>
        </view>
      </view>
    </view>

    <!-- Menu -->
    <view class="me-menu-group">
      <text class="me-menu-title">功能</text>
      <view class="me-menu-list">
        <view class="me-menu-item" @tap="goPage('/pages/patients/patients')">
          <view class="me-menu-left">
            <text class="me-menu-icon">👥</text>
            <text class="me-menu-text">患者档案</text>
          </view>
          <text class="me-menu-arrow">›</text>
        </view>
        <view class="me-menu-item" @tap="goPage('/pages/stats/stats')">
          <view class="me-menu-left">
            <text class="me-menu-icon">📊</text>
            <text class="me-menu-text">诊断统计</text>
          </view>
          <text class="me-menu-arrow">›</text>
        </view>
        <view class="me-menu-item" @tap="goPage('/pages/history/history')">
          <view class="me-menu-left">
            <text class="me-menu-icon">📋</text>
            <text class="me-menu-text">我的报告</text>
          </view>
          <text class="me-menu-arrow">›</text>
        </view>
        <view class="me-menu-item" @tap="goPage('/pages/quiz/quiz')">
          <view class="me-menu-left">
            <text class="me-menu-icon">🦷</text>
            <text class="me-menu-text">症状自测</text>
          </view>
          <text class="me-menu-arrow">›</text>
        </view>
      </view>
    </view>

    <view class="me-menu-group">
      <text class="me-menu-title">设置</text>
      <view class="me-menu-list">
        <view class="me-menu-item" @tap="goPage('/pages/notifications/notifications')">
          <view class="me-menu-left">
            <text class="me-menu-icon">🔔</text>
            <text class="me-menu-text">消息通知</text>
          </view>
          <text class="me-menu-arrow">›</text>
        </view>
        <view class="me-menu-item" @tap="goPage('/pages/help/help')">
          <view class="me-menu-left">
            <text class="me-menu-icon">📖</text>
            <text class="me-menu-text">使用帮助</text>
          </view>
          <text class="me-menu-arrow">›</text>
        </view>
        <view class="me-menu-item" @tap="goPage('/pages/about/about')">
          <view class="me-menu-left">
            <text class="me-menu-icon">ℹ️</text>
            <text class="me-menu-text">关于智齿 AI</text>
          </view>
          <text class="me-menu-arrow">›</text>
        </view>
      </view>
    </view>

    <!-- Logout -->
    <view class="me-logout-wrap" v-if="auth.isLoggedIn">
      <button class="me-logout-btn" @tap="handleLogout">退出登录</button>
    </view>

    <!-- Version -->
    <view class="me-version">
      <text>智齿 AI v0.1.0</text>
      <text class="me-version-sub">Wisdom Tooth AI · Taro 4.x</text>
    </view>

    <CustomTabBar :current="2" />
  </view>
</template>

<style>
/* === Me Page === */
.me-page { min-height: 100vh; padding-bottom: 48px; }

/* Profile */
.me-profile-wrap { position: relative; padding: 32px 28px 0; }
.me-profile-bg {
  position: absolute; top: 0; left: 0; right: 0; height: 200px;
  background: linear-gradient(135deg, #5b5fe3 0%, #818cf8 100%);
}
.me-profile-card {
  position: relative; background: #fff; border-radius: 24px;
  padding: 40px 28px 28px; margin-top: 20px;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 4px 24px rgba(0,0,0,0.06);
}
.me-avatar {
  width: 96px; height: 96px; border-radius: 48px;
  background: linear-gradient(135deg, #5b5fe3, #818cf8);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
}
.me-avatar-placeholder { background: linear-gradient(135deg, #cbd5e1, #94a3b8); }
.me-avatar-text { font-size: 44px; font-weight: 700; color: #fff; }
.me-name { font-size: 36px; font-weight: 700; color: #1e293b; display: block; }
.me-sub { font-size: 26px; color: #94a3b8; margin-top: 6px; display: block; }
.me-role {
  display: inline-block; font-size: 22px; color: #5b5fe3;
  background: #f0f0ff; padding: 4px 16px; border-radius: 20px; margin-top: 8px;
}
.me-id { font-size: 22px; color: #cbd5e1; margin-top: 8px; display: block; }
.me-login-btn { margin-top: 16px; padding: 14px 48px; background: #5b5fe3; border-radius: 24px; color: #fff; font-size: 28px; font-weight: 500; }

/* Permission */
.me-perm { margin: 24px 28px; background: #fff; border-radius: 20px; padding: 24px; }
.me-perm-title { font-size: 28px; font-weight: 600; color: #1e293b; display: block; margin-bottom: 14px; }
.me-perm-tags { display: flex; flex-direction: row; flex-wrap: wrap; }
.me-perm-tag { font-size: 22px; color: #475569; background: #f8fafc; padding: 8px 16px; border-radius: 10px; border: 1px solid #e2e8f0; margin-right: 10px; margin-bottom: 10px; }

/* Menu */
.me-menu-group { margin: 0 28px 8px; }
.me-menu-title { display: block; font-size: 24px; color: #94a3b8; padding: 16px 4px 12px; }
.me-menu-list { background: #fff; border-radius: 20px; overflow: hidden; }
.me-menu-item {
  display: flex; flex-direction: row; align-items: center;
  justify-content: space-between; padding: 28px 24px;
  border-bottom: 1px solid #f8fafc;
}
.me-menu-item:last-child { border-bottom: 0; }
.me-menu-left { display: flex; flex-direction: row; align-items: center; }
.me-menu-icon { font-size: 28px; width: 44px; text-align: center; margin-right: 16px; }
.me-menu-text { font-size: 28px; color: #1e293b; }
.me-menu-arrow { font-size: 32px; color: #cbd5e1; }

/* Logout */
.me-logout-wrap { margin: 40px 28px 0; }
.me-logout-btn {
  width: 100%; height: 92px; line-height: 92px; text-align: center;
  background: #fff; color: #ef4444; border: 1px solid #fee2e2;
  border-radius: 16px; font-size: 30px; font-weight: 500;
}

/* Version */
.me-version { display: flex; flex-direction: column; align-items: center; margin-top: 40px; }
.me-version text { font-size: 24px; color: #cbd5e1; }
.me-version-sub { font-size: 20px; margin-top: 4px; }
</style>
