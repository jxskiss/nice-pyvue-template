/**
 * Created by wsh on 2017/5/9.
 */

const path = require('path');
const webpack = require('webpack');
const glob = require('glob');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const FriendlyErrorsPlugin = require('friendly-errors-webpack-plugin')
const OptimizeCSSPlugin = require('optimize-css-assets-webpack-plugin')

/*
 * development and production configurations
 */

const buildConfigs = {
  dev: {
    assetsRoot: path.resolve(__dirname, './frontend/dist'),
    assetsSubDirectory: 'static',
    assetsPublicPath: '/',
    cssMinimize: false,
    cssSourceMap: false,
    cssExtract: true,
    // cheap-module-eval-source-map is faster for development
    devtool: '#cheap-module-eval-source-map',
    extraPlugins: [
      new webpack.HotModuleReplacementPlugin(),
      new webpack.NoEmitOnErrorsPlugin(),
      new FriendlyErrorsPlugin()
    ],
    outputFilename: (ext) => ext === 'ext' ? `[name].[ext]` : `[name].${ext}`
  },
  build: {
    assetsRoot: path.resolve(__dirname, './frontend/public'),
    assetsSubDirectory: 'static',
    assetsPublicPath: '/',
    cssMinimize: true,
    cssSourceMap: true,
    cssExtract: true,
    // source-map is better for debugging tools
    devtool: '#source-map',  // or false to disable source map
    extraPlugins: [
      new webpack.optimize.UglifyJsPlugin({
        compress: {warnings: false},
        sourceMap: true
      }),
      new OptimizeCSSPlugin({cssProcessorOptions: {safe: true}})
    ],
    // outputFilename: (ext) => ext === 'ext' ?
    //   `[name].[chunkhash:8].[ext]` : `[name].[chunkhash:8].${ext}`
    outputFilename: (ext) => ext === 'ext' ? `[name].[ext]` : `[name].${ext}`
  },
  get: function (_path, options = {}) {
    let config = options.dev ? this.dev : this.build;
    let properties = _path.split('.')
    let value;
    for (let idx in properties) {
      let parent = value || config;
      if (!parent.hasOwnProperty(properties[idx])) {
        return null
      } else {
        value = parent[properties[idx]]
      }
    }
    return value
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
  let output = [];
  let loaders = cssLoaders(options);
  for (let extension in loaders) {
    let loader = loaders[extension];
    output.push({
      test: new RegExp('\\.' + extension + '$'),
      use: loader
    })
  }
  return output
}

function getPageEntries (globPath) {
  let entries = {}, paths, basename, pathname;
  glob.sync(globPath).forEach(entry => {
    basename = path.basename(entry, path.extname(entry));
    paths = entry.split(path.sep)
    pathname = paths.slice(paths.indexOf('pages') + 1, -1).concat([basename]).join(path.sep)
    entries[pathname] = entry;
  });
  return entries
}

function resolveFrontend (dir) {
  return path.join(__dirname, 'frontend', dir || '')
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
  const getConfig = (_path) => buildConfigs.get(_path, options)
  const assetsPath = (_path) => path.posix.join(getConfig('assetsSubDirectory'), _path)
  const outputFilename = (ext) => getConfig('outputFilename')(ext)

  let exports = {
    context: path.resolve(__dirname),
    entry: getPageEntries(resolveFrontend('src/pages/**/*.js')),
    output: {
      path: getConfig('assetsRoot'),
      filename: assetsPath(`js/${outputFilename('js')}`),
      publicPath: getConfig('assetsPublicPath')
    },

    resolve: {
      modules: [resolveFrontend('src'), 'node_modules'],
      extensions: ['.js', '.vue', '.json', '.css', '.scss', '.less'],
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
              minimize: getConfig('cssMinimize'),
              sourceMap: getConfig('cssSourceMap'),
              extract: getConfig('cssExtract')
            })
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
        minimize: getConfig('cssMinimize'),
        sourceMap: getConfig('cssSourceMap'),
        extract: getConfig('cssExtract')
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

    devtool: getConfig('devtool'),

    // development server
    devServer: {
      contentBase: resolveFrontend('dist'),
      port: process.env.PORT || 8080,
      compress: true,
      historyApiFallback: true,
      hot: true
    }
  };

  /*
   * build html pages, config HtmlWebpackPlugin for each page
   */
  let pages = getPageEntries(resolveFrontend('src/pages/**/*.html'));
  for (let pathname in pages) {
    let conf = {
      filename: pathname + '.html',
      template: pages[pathname],
      chunks: [pathname, 'vendor', 'manifest'],
      inject: true,   // inject js file
      minify: {       // minify the html file
        removeComments: true,
        collapseWhitespace: false,
        removeAttributeQuotes: true
        // more options:
        // https://github.com/kangax/html-minifier#options-quick-reference
      }
    };
    exports.plugins.push(new HtmlWebpackPlugin(conf));
  }

  return exports
}
