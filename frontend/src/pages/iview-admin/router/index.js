import Vue from 'vue';
import iView from 'iview';
import VueRouter from 'vue-router';
import Cookies from 'js-cookie';
import Util from '../libs/util';
import {routers, otherRouter, appRouter} from './router';
import {commonApi} from '@common/api';

Vue.use(VueRouter);

// 路由配置
const RouterConfig = {
    // mode: 'history',
    routes: routers
};

export const router = new VueRouter(RouterConfig);

function checkLogin () {
    const isLogin = Cookies.get('user') !== null;
    const lastCheck = localStorage.get('lastCheck');
    const now = (new Date()).getTime();
    return isLogin && lastCheck && now - lastCheck < 10 * 60 * 1000;
}

router.beforeEach((to, from, next) => {
    iView.LoadingBar.start();
    Util.title(to.meta.title);

    if (checkLogin() || /error-.*/.test(to.name) || to.name === 'login') {
        // 错误页面和登陆页面不需要认证
        // 已经登陆的用户一段时间内不需要再次认证
        next();
    } else {
        // 访问其他资源需要先认证用户身份
        commonApi.getUserProfile()
            .then(function (resp) {
                if (resp.data.code === 'ok') {
                    Cookies.set('user', resp.data.data.username);
                    localStorage.set('lastCheck', (new Date()).getTime());
                    Util.toDefaultPage([otherRouter, ...appRouter], to.name, router, next);
                } else {
                    localStorage.clear();
                    next({ name: 'login', query: { redirect: to.fullPath } });
                }
            })
            .catch(function (error) {
                next({ name: 'login', query: { redirect: to.fullPath } });
            })
    }
});

router.afterEach((to) => {
    iView.LoadingBar.finish();
    window.scrollTo(0, 0);
});
