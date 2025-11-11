# Use stable Alpine Nginx image
FROM nginx:stable-alpine

# Remove default configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom configuration into container
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose ports for HTTP and HTTPS
EXPOSE 80 443

