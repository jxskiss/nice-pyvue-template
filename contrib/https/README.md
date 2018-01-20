# Deploy HTTPS Service

Instructions about deploy HTTPS website.

## Method 1: Bare Nginx

Apply and renew SSL certificate manually, and reload Nginx service
when SSL certificate being changed, the reloading action may be
accomplished by crontab.

If you are using free certificate from [Let's Encrypt], the cert issuing,
cert renewal and Nginx reloading actions can be accomplished fully
automatic using the [Certbot] or other ACME clients.
See [Let's Encrypt] website for more details and documentation.

## Method 2: Reverse Proxy with automatic HTTPS capability

There are many reverse proxy software provide ability to issue and renew
SSL certificate from [Let's Encrypt].

1. [Caddy](https://caddyserver.com/)
2. [Traefik](https://traefik.io/)
3. [golang/autocert](https://godoc.org/golang.org/x/crypto/acme/autocert)

Please see the corresponding link for more details.

## Method 3: OpenResty/lua-resty-auto-ssl

https://github.com/GUI/lua-resty-auto-ssl

On the fly (and free) SSL registration and renewal inside OpenResty/nginx
with Let's Encrypt.

This [OpenResty] plugin automatically and transparently issues SSL certificates
from Let's Encrypt (a free certificate authority) as requests are received.
It works like:

- A SSL request for a SNI hostname is received.
- If the system already has a SSL certificate for that domain,
  it is immediately returned (with OCSP stapling).
- If the system does not yet have an SSL certificate for this domain,
  it issues a new SSL certificate from Let's Encrypt. Domain validation
  is handled for you. After receiving the new certificate (usually within
  a few seconds), the new certificate is saved, cached, and returned
  to the client (without dropping the original request).

This uses the ssl_certificate_by_lua functionality in OpenResty 1.9.7.2+.

This project has been used in production by many users and is well maintained.

## Method 4: OpenResty with Central Certificate Server

I have written a small project [ssl-cert-server] to serve as a central
certificate server, which cache, issue and renew certificates for any
domain which can proxy the HTTP-01 challenge to the cert server.

The reverse proxy [OpenResty] behaves as client of the cert server.


[Let's Encrypt]: https://letsencrypt.org/
[Certbot]: https://certbot.eff.org/
[OpenResty]: https://openresty.org/
[ssl-cert-server]: https://github.com/jxskiss/ssl-cert-server
