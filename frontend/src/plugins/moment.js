/**
 * Created by wsh on 2017/5/9.
 * Usage:
 *    import MomentPlugin from '@/plugins/moment.js'
 *    Vue.use(MomentPlugin)
 */

import moment from 'moment'

export default {
  install: function (Vue) {
    Object.defineProperty(Vue.prototype, '$moment', {value: moment});
  }
}
