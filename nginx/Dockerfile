# Use stable Alpine Nginx image
FROM nginx:stable-alpine

# Replace the main nginx.conf
COPY nginx.conf /etc/nginx/nginx.conf

# nginx user inside the container is uid/gid 101 → tmpfs already uses that
EXPOSE 80 443