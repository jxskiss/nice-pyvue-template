/**
 * 关于 Vue.js 项目 API、Router 模块化配置，推荐两篇文章：
 * https://segmentfault.com/a/1190000009858990
 * https://juejin.im/post/5a52c9a4f265da3e2a0d6b74
 */

import axios from 'axios'
import qs from 'query-string'
import env from './env.config'

function baseUrl () {
  // maybe use env to distinct API base url is better?
  let hostname = window.location.hostname,
    API_BASE_URL = `http://${window.location.host}`  // 默认开发环境, PROXY 反向代理

  if (hostname === 'www.example.com') {  // 正式生产环境
    API_BASE_URL = 'http://api.example.com'
  } else if (hostname === 'test.example.com') {  // 测试环境
    API_BASE_URL = 'http://test-api.example.com'
  }
  return API_BASE_URL
}

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
  // Do something with the response
  return response
}, function (error) {
  if (env === 'development') {
    let detail = error
    if (error.response && error.response.data) {
      const data = error.response.data
      if (data.code === 'error_with_traceback') {
        detail = data.traceback
      } else {
        detail = `${data.code}: ${data.message}`
      }
    }
    console.log('Error response from:', error.config.url, detail)
  }
  return Promise.reject(error)
})

const defaultOptions = {
  baseUrl: baseUrl(),
  // CSRF token settings for Django
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  headers: {
    // 'Content-Type': 'application/x-www-form-urlencoded'
    'Content-Type': 'application/json'
  },
  transformRequest: [function (data, headers) {
    if (headers['Content-Type'] === 'application/x-www-form-urlencoded') {
      return qs.stringify(data)
    }
  }]
}

export default defaultOptions;
