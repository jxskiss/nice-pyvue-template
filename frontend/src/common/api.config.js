/**
 * 关于 Vue.js 项目 API、Router 模块化配置，推荐一篇很好的文章：
 * https://segmentfault.com/a/1190000009858990
 */

import axios from 'axios'
import qs from 'query-string'
import env from './env.config'


function baseUrl () {
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
  // Do something with the response
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
  } else {
    console.log(error)
  }
  return Promise.reject(error)
})


export default defaultOptions = {
  baseUrl: baseUrl(),
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  headers: {
    // 'Content-Type': 'application/x-www-form-urlencoded',
  },
  transformRequest: [function (data, headers) {
    if (headers['Content-Type'] === 'application/x-www-form-urlencoded') {
      return qs.stringify(data)
    }
  }]
}
