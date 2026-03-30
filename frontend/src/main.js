//#整个系统启动入口
import { createApp } from 'vue' //#'vue'和‘vant’是从项目环境中（node_modules文件夹）拉取的外部依赖包
import Vant from 'vant'

import App from './App.vue'//#页面整体布局
import router from './router'//#路由配置--实现多页面切换
import 'vant/lib/index.css'
import './style.css'//#自己写的全局样式，对vant样式做补充，如果vant（移动端UI）够了可以不要

createApp(App).use(router).use(Vant).mount('#app')
