import { defineConfig } from '@tarojs/cli'
import path from 'path'

export default defineConfig({
  projectName: 'wisdom-tooth-miniapp',
  date: '2026-5-16',
  designWidth: 750,
  deviceRatio: {
    640: 2.34 / 2,
    750: 1,
    375: 2,
    828: 1.81 / 2,
  },
  sourceRoot: 'src',
  outputRoot: 'dist',
  plugins: ['@tarojs/plugin-framework-vue3'],
  defineConstants: {},
  copy: {
    patterns: [{ from: 'src/static', to: 'dist/static' }],
  },
  framework: 'vue3',
  compiler: 'webpack5',
  alias: {
    '@': path.resolve(__dirname, '..', 'src'),
  },
  mini: {
    webpackChain(chain) {
      chain.resolve.alias.set('@', path.resolve(__dirname, '..', 'src'))
    },
    postcss: {
      pxtransform: { enable: true },
      url: { enable: true },
    },
  },
})
