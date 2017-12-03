import Vue from 'vue'

Vue.config.productionTip = false

const template = `
<div id="app" style="max-width: 720px; margin: auto;">
<h1>Demonstration of single page development.</h1>
<div>
<p>You can do <code>npm run dev</code> and <code>npm run build</code> for only one entry.</p>
<p>This avoids loading any unnecessary stuff into development environment, so it's blazing fast.</p> 
</div>
<div>
<p>Usage Example:</p>
<code><pre style="background-color: ghostwhite">
# linux / mac
PAGE=dev-single npm run dev
PAGE=dev-single npm run build

# windows
npm run dev -- --env.page=dev-single
npm run build -- --env.page=dev-single
</pre></code>
</div>
</div>
`

/* eslint-disable no-new */
new Vue({
  el: '#app',
  template: template,
  data () {
    return {}
  },
  created () {
    document.title = 'Single page development demo'
  }
})
