server {
    listen 18443 ssl;
    listen [::]:18443 ssl ipv6only=on;
    listen 5001 ssl;
    listen [::]:5001 ssl ipv6only=on;
    server_name ipv6ssl.com;
}
