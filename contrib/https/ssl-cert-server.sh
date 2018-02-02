# Instruction for running ssl certificate server
# https://github.com/jxskiss/ssl-cert-server

wget https://github.com/jxskiss/ssl-cert-server/files/1648572/ssl-cert-server_0.1.1_linux_amd64.tar.gz
tar zxvf ssl-cert-server_0.1.1_linux_amd64.tar.gz

chmod +x ssl-cert-server_0.1.1_linux_amd64

./ssl-cert-server_0.1.1_linux_amd64 \
    --listen=127.0.0.1:8999 \
    --email=admin@example.com \
    --pattern=".*\\.example\\.com$" \
    --cache-dir=./ssl-certs \
    --force-rsa=true \
    --logtostderr
