/**
 * Created by wsh on 2017/5/9.
 * Usage:
 *    import AxiosPlugin from '@/plugins/axios.js'
 *    Vue.use(AxiosPlugin)
 *    // or
 *    Vue.use(AxiosPlugin, '$axios')
 */

import axios from 'axios'

export default {
  install: function (Vue, name = '$http') {
    Object.defineProperty(Vue.prototype, name, {value: axios});
  }
}
