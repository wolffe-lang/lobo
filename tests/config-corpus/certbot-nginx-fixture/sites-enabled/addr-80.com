server {
    listen 1.2.3.4:18080;
    listen [1:20::300]:18080;
    server_name addr-80.com;
}
