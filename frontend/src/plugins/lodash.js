/**
 * Created by wsh on 2017/5/20.
 * Usage:
 *    import LodashPlugin from '@/plugins/lodash.js'
 *    Vue.use(LodashPlugin)
 *    // or
 *    Vue.use(LodashPlugin, '$lodash')
 */

import lodash from 'lodash'

export default {
  install: function (Vue, name = '$lodash') {
    Object.defineProperty(Vue.prototype, name, {value: lodash})
  }
}
