/**
 * Created by wsh on 2017/5/9.
 */

const fs = require('fs')
const glob = require('glob')
const path = require('path')
const webpack = require('webpack')
const ExtractTextPlugin = require('extract-text-webpack-plugin')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const FriendlyErrorsPlugin = require('friendly-errors-webpack-plugin')
const OptimizeCSSPlugin = require('optimize-css-assets-webpack-plugin')

/*
 * development and production configurations
 */

function makeBuildConfigs (options) {
  return {
    // build or dev settings take priority over common settings
    // see the "get" method for details
    common: {
      assetsRoot: path.resolve(__dirname, './frontend/dist'),
      assetsSubDirectory: 'static',
      assetsPublicPath: '/'
    },
    build: {
      cssMinimize: true,
      cssSourceMap: true,
      cssExtract: true,
      // source-map is better for debugging tools
      devtool: '#source-map',  // or false to disable source map
      // Gzip off by default as many popular static hosts already gzip
      // all static assets for you. Before setting to true, make sure to:
      // `npm install --save-dev compression-webpack-plugin`
      productionGzip: false,
      productionGzipExtensions: ['js', 'css'],
      // build specific plugins
      extraPlugins: [
        new webpack.optimize.UglifyJsPlugin({
          compress: {warnings: false},
          sourceMap: true
        }),
        new OptimizeCSSPlugin({cssProcessorOptions: {safe: true}})
      ],
      outputFilename: (ext) => ext === 'ext'
        ? `[name].[chunkhash:8].[ext]` : `[name].[chunkhash:8].${ext}`
    },
    dev: {
      cssMinimize: false,
      cssSourceMap: false,
      cssExtract: true,
      // cheap-module-eval-source-map is faster for development
      devtool: '#cheap-module-eval-source-map',
      port: process.env.PORT || 8080,
      // https://webpack.github.io/docs/webpack-dev-server.html#proxy
      proxy: {},
      // dev specific plugins
      extraPlugins: [
        new webpack.HotModuleReplacementPlugin(),
        new webpack.NoEmitOnErrorsPlugin(),
        new FriendlyErrorsPlugin()
      ],
      outputFilename: (ext) => ext === 'ext' ? `[name].[ext]` : `[name].${ext}`
    },
    get: function (_path, options = {}) {
      let config = process.env.NODE_ENV === 'production' ? this.build : this.dev
      let properties = _path.split('.')
      let search = (root) => {
        let value = null
        for (let idx in properties) {
          let parent = value || root
          if (!parent.hasOwnProperty(properties[idx])) {
            break
          } else {
            value = parent[properties[idx]]
          }
        }
        return value
      }
      let value = search(config)
      if (value === null) value = search(this.common)
      return value
    }
  }
}

/*
 * util functions
 */

function cssLoaders (options) {
  options = options || {}

  let cssLoader = {
    loader: 'css-loader',
    options: {
      minimize: options.minimize,
      sourceMap: options.sourceMap
    }
  }

  // generate loader string to be used with extract text plugin
  function generateLoaders (loader, loaderOptions) {
    let loaders = [cssLoader]
    if (loader) {
      loaders.push({
        loader: loader + '-loader',
        options: Object.assign({}, loaderOptions, {
          sourceMap: options.sourceMap
        })
      })
    }

    // Extract CSS when that option is specified
    // (which is the case during production build)
    if (options.extract) {
      return ExtractTextPlugin.extract({
        use: loaders,
        fallback: 'vue-style-loader'
      })
    } else {
      return ['vue-style-loader'].concat(loaders)
    }
  }

  // http://vuejs.github.io/vue-loader/configurations/extract-css.html
  return {
    css: generateLoaders(),
    postcss: generateLoaders(),
    less: generateLoaders('less'),
    sass: generateLoaders('sass', {indentedSyntax: true}),
    scss: generateLoaders('scss'),
    stylus: generateLoaders('stylus'),
    styl: generateLoaders('stylus')
  }
}

// Generate loaders for standalone style files (outside of .vue)
function styleLoaders (options) {
  let output = []
  let loaders = cssLoaders(options)
  for (let extension in loaders) {
    let loader = loaders[extension]
    output.push({
      test: new RegExp('\\.' + extension + '$'),
      use: loader
    })
  }
  return output
}

function getPageEntries (globPath) {
  let targetPage = process.env.PAGE
  let entries = {}, paths, basename, pathname, pageIndex
  glob.sync(globPath).forEach(entry => {
    basename = path.basename(entry, path.extname(entry))
    // node-glob uses forward-slashes only in glob expressions, even on windows
    paths = entry.split('/')
    pageIndex = paths.indexOf('pages') + 1
    if (targetPage) {  // partially build
      if (paths.length === pageIndex + 1) {  // root pages
        if (basename !== targetPage) {
          return
        }
      } else if (paths[pageIndex] !== targetPage) {
        return
      }
    }
    pathname = paths.slice(pageIndex, -1).concat([basename]).join('/')
    entries[pathname] = entry
  })
  return entries
}

function resolveFrontend (target) {
  return path.join(__dirname, 'frontend', target || '')
}

// check whether a module is from node_modules
function isNodeModule (module) {
  return (
    module.resource &&
    /\.js$/.test(module.resource) &&
    module.resource.indexOf(
      path.join(__dirname, 'node_modules')
    ) === 0
  )
}

/*
 * webpack configurations
 */

module.exports = (options = {}) => {
  // --env.production
  if (typeof options.production === 'boolean' && options.production) {
    process.env.NODE_ENV = 'production'
  } else {
    process.env.NODE_ENV = 'development'
  }
  if (options.port) process.env.PORT = options.port  // --env.port=PORT
  if (options.page) process.env.PAGE = options.page  // --env.page=PAGE

  const buildConfigs = makeBuildConfigs(options)
  const getConfig = (_path) => buildConfigs.get(_path, options)
  const assetsPath = (_path) => path.posix.join(getConfig('assetsSubDirectory'), _path)
  const outputFilename = (ext) => getConfig('outputFilename')(ext)

  let exports = {
    context: path.resolve(__dirname),
    entry: getPageEntries(resolveFrontend('src/pages/**/*.[jt]s')),
    output: {
      path: getConfig('assetsRoot'),
      filename: assetsPath(`js/${outputFilename('js')}`),
      publicPath: getConfig('assetsPublicPath')
    },

    resolve: {
      modules: [resolveFrontend('src'), 'node_modules'],
      extensions: ['.js', '.ts', '.vue', '.json', '.css', '.scss', '.less'],
      alias: {
        'vue$': 'vue/dist/vue.esm.js',
        '@': resolveFrontend('src'),
        'assets': resolveFrontend('src/assets'),
        'components': resolveFrontend('src/components'),
        'plugins': resolveFrontend('src/plugins'),
        'utils': resolveFrontend('src/utils')
      }
    },

    module: {
      rules: [
        {
          test: /\.(js|vue)$/,
          loader: 'eslint-loader',
          enforce: 'pre',
          include: [resolveFrontend('src'), resolveFrontend('test')],
          exclude: /node_modules/,
          options: {
            formatter: require('eslint-friendly-formatter')
          }
        },
        {
          test: /\.vue$/,
          loader: 'vue-loader',
          options: {
            loaders: cssLoaders({
              minimize: getConfig('cssMinimize') || false,
              sourceMap: getConfig('cssSourceMap') || false,
              extract: getConfig('cssExtract') || false
            }),
            transformToRequire: {
              video: 'src',
              source: 'src',
              img: 'src',
              image: 'xlink:href'
            }
          }
        },
        {
          test: /\.tsx?$/,
          loader: 'ts-loader',
          include: [resolveFrontend('src'), resolveFrontend('test')],
          options: {
            appendTsSuffixTo: [/\.vue$/],
            // set to false to get benefits from static type checking
            // https://www.npmjs.com/package/ts-loader#transpileonly-boolean-defaultfalse
            transpileOnly: true
          }
        },
        {
          test: /\.js$/,
          loader: 'babel-loader',
          include: [resolveFrontend('src'), resolveFrontend('test')],
          exclude: /node_modules/
        },
        {
          test: /\.json$/,
          loader: 'json-loader'
        },
        {
          test: /\.(png|jpe?g|gif|svg)(\?.*)?$/,
          loader: 'url-loader',
          options: {
            limit: 10000,
            name: assetsPath(`img/${outputFilename('ext')}`)
            // a lot of other options
          }
        },
        {
          test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/,
          loader: 'url-loader',
          options: {
            limit: 10000,
            name: assetsPath(`fonts/${outputFilename('ext')}`)
          }
        }
      ].concat(styleLoaders({
        minimize: getConfig('cssMinimize') || false,
        sourceMap: getConfig('cssSourceMap') || false,
        extract: getConfig('cssExtract') || false
      }))
    },

    // don't bundle external libraries, which are loaded from CDN
    externals: {},

    plugins: [
      // extract css into its own file
      new ExtractTextPlugin({
        filename: assetsPath(`css/${outputFilename('css')}`)
      }),
      // split vendor js into its own file
      new webpack.optimize.CommonsChunkPlugin({
        name: 'vendor',
        minChunks: function (module, count) {
          // any required modules inside node_modules are extracted to vendor
          return isNodeModule(module)
        }
      }),
      // extract webpack runtime and module manifest to its own file in order to
      // prevent vendor hash from being updated whenever app bundle is updated
      new webpack.optimize.CommonsChunkPlugin({
        name: 'manifest',
        chunks: ['vendor']
      }),
      // copy custom static assets
      new CopyWebpackPlugin([
        {
          from: resolveFrontend('static'),
          to: getConfig('assetsSubDirectory'),
          ignore: ['.*', 'README.*']
        }
      ])
    ].concat(getConfig('extraPlugins') || []),

    devtool: getConfig('devtool') || '#cheap-module-eval-source-map',

    // development server
    devServer: {
      contentBase: resolveFrontend('dist'),
      compress: true,
      historyApiFallback: true,
      hot: true,
      port: buildConfigs.dev.port,
      proxy: buildConfigs.dev.proxy
    }
  }

  /*
   * build html pages, config HtmlWebpackPlugin for each page
   */
  for (let pathname in getPageEntries(resolveFrontend('src/pages/**/@(index|main).[jt]s'))) {
    let conf = {
      filename: ((pn) => {
        // always use index.html as output filename for main or index entry
        if (pn === 'main') return 'index.html'
        if (pn.endsWith('/main')) return `${pn.slice(0, -5)}/index.html`
        return pn + '.html'
      })(pathname),
      template: ((pn) => {
        // use root index.html as template if page html not exists
        let htmlPath = resolveFrontend(`src/pages/${pn}.html`)
        if (fs.existsSync(htmlPath)) {
          return htmlPath
        }
        return resolveFrontend('src/pages/index.html')
      })(pathname),
      chunks: [pathname, 'vendor', 'manifest'],
      inject: true,   // inject js file
      minify: {       // minify the html file
        removeComments: true,
        collapseWhitespace: true,
        removeAttributeQuotes: true
        // more options:
        // https://github.com/kangax/html-minifier#options-quick-reference
      }
    }
    exports.plugins.push(new HtmlWebpackPlugin(conf))
  }

  if (getConfig('productionGzip')) {
    let extensions = getConfig('productionGzipExtensions')
    if (extensions && extensions.length > 0) {
      const CompressionWebpackPlugin = require('compression-webpack-plugin')
      let conf = {
        asset: '[path].gz[query]',
        algorithm: 'gzip',
        test: new RegExp(`\\.(${extensions.join('|')})$`),
        threshold: 10240,
        minRatio: 0.8
      }
      exports.plugins.push(new CompressionWebpackPlugin(conf))
    }
  }

  /*
   * Run the build command with an extra argument to view the bundle analyzer
   * report after build finishes:
   * `webpack --env.report`, or
   * `npm run build -- --env.report`
   */
  if (options.report) {
    const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin
    exports.plugins.push(new BundleAnalyzerPlugin())
  }

  return exports
}
