# Use stable Alpine Nginx image
FROM nginx:stable-alpine

# Remove only the default site, but keep the main nginx.conf
RUN rm /etc/nginx/conf.d/default.conf

# Replace the entire main config
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 443