# Plugins

## Import Plugins

Put plugins used by many components or js files here.

Plugin usage example:

    import MomentPlugin from '@/plugins/awesome.js'
    Vue.use(MomentPlugin)

    new Vue({
      created() {
        console.log(this.$moment.now());
      }
    })

Look the plugin for particular usages.

## Write Plugins

There are several methods to use javascript libraries with Vue.js,
see this post: [Use Any Javascript Library With Vue.js](http://vuejsdevelopers.com/2017/04/22/vue-js-libraries-plugins/)
for instructions of other methods.
