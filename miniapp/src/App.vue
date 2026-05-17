<template>
  <view class="app-root">
    <slot />
  </view>
</template>

<style lang="scss">
page {
  --primary: #5b5fe3;
  --primary-dark: #3d3fa8;
  --primary-light: #eef2ff;
  --success: #10b981;
  --success-light: #ecfdf5;
  --warning: #f59e0b;
  --warning-light: #fffbeb;
  --danger: #ef4444;
  --danger-light: #fef2f2;
  --text: #1e293b;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --text-placeholder: #cbd5e1;
  --bg: #f8fafc;
  --bg-white: #ffffff;
  --border: #e2e8f0;
  --border-light: #f1f5f9;
  --radius-sm: 8px;
  --radius: 12px;
  --radius-md: 16px;
  --radius-lg: 20px;
  --radius-xl: 24px;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
  --shadow: 0 2px 12px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 24px rgba(0,0,0,0.06);

  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', sans-serif;
  font-size: 14px;
  color: var(--text);
  background: var(--bg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

view, text, image, button, input, scroll-view, swiper, swiper-item {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

button {
  padding: 0;
  margin: 0;
  background: none;
  border: none;
  border-radius: 0;
  font-size: inherit;
  color: inherit;
  line-height: inherit;
}

button::after {
  border: none;
}

.app-root {
  min-height: 100vh;
}

.safe-area-bottom {
  padding-bottom: constant(safe-area-inset-bottom);
  padding-bottom: env(safe-area-inset-bottom);
}

.safe-area-top {
  padding-top: constant(safe-area-inset-top);
  padding-top: env(safe-area-inset-top);
}
</style>
