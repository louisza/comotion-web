FROM node:22-slim AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
COPY package*.json ./
# Ensure devDependencies (typescript, @types/*) are installed for build
ENV NODE_ENV=development
RUN npm ci
ENV NODE_ENV=production
COPY . .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
ENV HOSTNAME="0.0.0.0"
CMD ["node", "server.js"]
