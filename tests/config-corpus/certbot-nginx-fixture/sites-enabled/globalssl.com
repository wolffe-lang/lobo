server {
    server_name globalssl.com;
    listen 4.8.2.6:18057;
}
   
server {
    server_name globalsslsetssl.com;
    listen 4.8.2.6:18057 ssl;
}
