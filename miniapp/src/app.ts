import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './app.scss'

const app = createApp(App)
app.use(createPinia())

export default app
