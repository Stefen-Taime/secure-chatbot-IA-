FROM node:20-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
RUN npm install babel-eslint@10.1.0 --save-dev
COPY . .
RUN npm run build

FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]