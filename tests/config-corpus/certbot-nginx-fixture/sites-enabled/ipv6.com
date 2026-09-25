server {
    listen 18080;
    listen [::]:18080;
    server_name ipv6.com;
}
