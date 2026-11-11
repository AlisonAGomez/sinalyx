/** Inicia o painel Vue e conecta a navegação e os estilos da aplicação. */

import { createApp } from 'vue'

import App from './App.vue'
import { router } from './router'
import './assets/main.css'

createApp(App).use(router).mount('#app')
