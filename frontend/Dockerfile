# Build: install dependencies and create the standalone production build
FROM node:22.21-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
RUN npm run build

# Run: only the standalone server and static assets, as a non-root user
FROM node:22.21-alpine
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

RUN addgroup -S factoryshield && adduser -S -G factoryshield factoryshield

COPY --from=builder --chown=factoryshield:factoryshield /app/.next/standalone ./
COPY --from=builder --chown=factoryshield:factoryshield /app/.next/static ./.next/static

USER factoryshield
EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -qO /dev/null http://127.0.0.1:3000/login || exit 1

CMD ["node", "server.js"]
