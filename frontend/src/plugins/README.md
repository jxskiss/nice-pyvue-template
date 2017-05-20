# Plugins

## Import Plugins

Put plugins used by many components or js files here.

The plugins can be imported by three ways:

1. use relative path:

   `import AwesomePlugin from '../../plugins/awesome.js`

2. use plugins/foo.js directly:

   `import AwesomePlugin from 'plugins/awesome.js`

3. use @ to indicate local files:

   `import AwesomePlugin from '@/plugins/awesome.js`,

   this is the default way used by vue-cli webpack template.

See webpack.config.js for more details about path resolving.

## Write Plugins

There are several methods to use javascript libraries with Vue.js,
see this post: [Use Any Javascript Library With Vue.js](http://vuejsdevelopers.com/2017/04/22/vue-js-libraries-plugins/)
for instructions of other methods.
