import axios from 'axios';
import qs from 'query-string';
import defaultOptions from './api.config';

function isEmptyObject (obj) {
  return !obj || !Object.keys(obj).length;
}

function isObject (obj) {
  return Object.prototype.toString.call(obj) === '[object Object]';
}

function isArray (obj) {
  return Object.prototype.toString.call(obj) === '[object Array]';
}

function cleanupHeaders (headers) {
  ['common', 'get', 'post', 'put', 'delete', 'patch', 'options', 'head']
    .forEach(prop => headers[prop] && delete headers[prop]);
  return headers;
}

function resolveHeaders (method, defaults = {}, extras = {}) {
  method = method && method.toLowerCase();
  if (!/^(get|post|put|delete|patch|options|head)$/.test(method)) {
    throw new Error(`resolveHeaders: illegal method:"${method}"`);
  }

  const commonHeaders = defaults.common || {};
  const headersForMethod = defaults[method] || {};
  return cleanupHeaders({
    ...defaults,
    ...commonHeaders,
    ...headersForMethod,
    ...extras
  });
}

function resolveConfig (method, defaults = {}, extras = {}) {
  if (isEmptyObject(defaults) && isEmptyObject(extras)) {
    return {};
  }

  return {
    ...defaults,
    ...extras,
    headers: resolveHeaders(method, defaults.headers, extras.headers)
  };
}

class BaseApiModule {
  constructor (options = {}) {
    this.defaultConfig = {
      headers: { ...defaultOptions.headers, ...options.headers }
    }

    // this.$http = axios.create({
    //   ...defaultOptions,
    //   ...options,
    //   ...this.defaultConfig
    // })
    this.$http = axios
  }

  get (url, config = {}) {
    return this.$http.get(url, resolveConfig('get', this.defaultConfig, config));
  }

  post (url, data = undefined, config = {}) {
    return this.$http.post(url, data, resolveConfig('post', this.defaultConfig, config));
  }

  put (url, data = undefined, config = {}) {
    return this.$http.put(url, data, resolveConfig('put', this.defaultConfig, config));
  }

  delete (url, config = {}) {
    return this.$http.delete(url, resolveConfig('delete', this.defaultConfig, config));
  }
}

function bindModuleMethod (method, moduleInstance) {
  return function (url, args, config = {}) {
    method = method.toLowerCase();
    const shouldSendData = method === 'post' || method === 'put';
    return new Promise(function (resolve, reject) {
      config = {
        url,
        method,
        ...resolveConfig(method, moduleInstance.defaultConfig, config)
      };
      if (args) {
        shouldSendData
          ? config.data = args
          : config.url = `${config.url}?${qs.stringify(args)}`;
      }
      moduleInstance.$http.request(config)
        .then(response => resolve(response))
        .catch(error => reject(error));
    });
  };
}

function mapParamsToPathVariables (url, params) {
  if (!url || typeof url !== 'string') {
    throw new Error(`url ${url} should be a string`);
  }
  return url.replace(/:(\w+)/ig, (_, key) => params[key]);
}

function bindApis (defs = {}) {
  return module => {
    const instance = module.prototype || module;
    for (const [name, def] of Object.entries(defs)) {
      if (!def || Object.keys(def).length === 0) {
        throw new Error(`invalid definition for API "${name}()"`)
      }
      Object.defineProperty(instance, name, {
        configurable: true,
        writable: true,
        enumerable: true,
        value: ((url, func, thisArg) => {
          return function () {
            let args = Array.prototype.slice.call(arguments);
            if (args.length > 0 && url.indexOf('/:') >= 0) {
              if (isObject(args[0])) {
                const params = args[0];
                args = args.slice(1);
                url = mapParamsToPathVariables(url, params);
              }
            }
            return func && func.apply(thisArg, [url].concat(args));
          }
        })(def.url, bindModuleMethod(def.method, instance), instance)
      });
    }
  };
}

export default function makeApiModule (apiDefs) {
  for (let [name, def] of Object.entries(apiDefs)) {
    if (typeof def === 'string') {
      apiDefs[name] = {method: 'GET', url: def};
    } else if (isArray(def)) {
      apiDefs[name] = {method: def[0], url: def[1]};
    }
  }
  return class extends BaseApiModule {
    constructor (options) {
      super(options);
      bindApis(apiDefs)(this);
    }
  };
}

// // TagManager api module
// const tagApiDefs = {
//   // can be string, "GET" method will be used by default
//   getTag: '/tags/:id',
//   // can be array, [method, url]
//   getTagPageableList: ['GET', '/tags'],
//   // or object style, { method, url }
//   getTagFullList: {method: 'GET', url: '/tags'},
//
//   // method can be either uppercase or lowercase
//   createTag: ['post', '/tags'],
//   updateTag: ['post', '/tags/:id'],
//   deleteTag: ['delete', '/tags/:id']
// };
//
// const tagApi = new (makeApiModule(tagApiDefs))({/* custom options */});
// or
// const TagApiModule = makeApiModule(tagApiDefs);
// const tagApi = new TagApiModule( /* custom options */ );
