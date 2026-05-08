FROM node:22-alpine AS build

WORKDIR /app
ARG VITE_API_BASE_URL=
ARG VITE_LOGTO_ENDPOINT=http://127.0.0.1:3001
ARG VITE_LOGTO_APP_ID=
ARG VITE_LOGTO_API_RESOURCE=https://api.wisdom-tooth-ai.local
ARG NPM_REGISTRY=https://registry.npmjs.org/

ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_LOGTO_ENDPOINT=${VITE_LOGTO_ENDPOINT}
ENV VITE_LOGTO_APP_ID=${VITE_LOGTO_APP_ID}
ENV VITE_LOGTO_API_RESOURCE=${VITE_LOGTO_API_RESOURCE}

COPY package.json ./package.json
COPY package-lock.json ./package-lock.json
RUN npm config set registry ${NPM_REGISTRY} && npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
