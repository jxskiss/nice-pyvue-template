/**
 * 关于 Vue.js 项目 API、Router 模块化配置，推荐一篇很好的文章：
 * https://segmentfault.com/a/1190000009858990
 */

import axios from 'axios'
import env from './env.config'


export function apiBase() {
  // maybe use env to distinct API base url is better?
  let hostname = window.location.hostname,
    API_BASE_URL = '/api'  // 默认开发环境, PROXY 反向代理

  if (hostname === 'www.example.com') {  // 正式生产环境
    API_BASE_URL = 'http://api.example.com'
  } else if (hostname === 'test.example.com') {  // 测试环境
    API_BASE_URL = 'http://test-api.example.com'
  }
  return API_BASE_URL
}

export function COMMON_API () {
  return {
    Users: {
      Profile: apiBase() + '/v1/common/users/profile',
      Login: apiBase() + '/v1/common/users/login',
      Logout: apiBase() + '/v1/common/users/logout'
    }
  }
}

export function MOCK_API () {
  return {
    Mock1: apiBase() + '/v1/mockapi/mock1',
    Mock2: apiBase() + '/v1/mockapi/mock2/'
  }
}

export const Api = {
  Users: {
    Profile: () => axios.get(COMMON_API().Users.Profile),
    Login: (data) => axios.post(COMMON_API().Users.Login, data),
    Logout: () => axios.get(COMMON_API().Users.Logout)
  },
  Mockapi: {
    Mock1: () => axios.get(MOCK_API().Mock1),
    Mock2List: () => axios.get(MOCK_API().Mock2),
    Mock2Detail: (someId) => axios.get(`${MOCK_API().Mock2}${someId}`),
    Mock2Submit: (data) => axios.post(MOCK_API().Mock2, data)
  }
}


// CSRF token settings for Django
axios.defaults.xsrfCookieName = 'csrftoken';
axios.defaults.xsrfHeaderName = 'X-CSRFToken';

// Add a request interceptor
axios.interceptors.request.use(function (config) {
  // Do something before request is sent
  return config
}, function (error) {
  // Do something with request error
  return Promise.reject(error)
})

// Add a response interceptor
axios.interceptors.response.use(function (response) {
  if (env === 'development') {
    console.log('Success response from:', response.config.url)
    console.log(response.data)
  }
  return response
}, function (error) {
  if (env === 'development') {
    console.log('Error response from:', error.config.url)
    if (error.response && error.response.data) {
      let data = error.response.data
      if (data.code === 'error_with_traceback') {
        console.log(data.traceback)
      } else {
        console.log(data.code, data.message)
      }
    } else {
      console.log(error)
    }
  }
  return Promise.reject(error)
})
