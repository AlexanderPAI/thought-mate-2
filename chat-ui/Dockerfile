FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html styles.css chat.js /usr/share/nginx/html/
COPY vendor/ /usr/share/nginx/html/vendor/
