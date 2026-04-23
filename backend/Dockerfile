# Multi-stage: build the Next.js static bundle, then serve it from Python.

# -------- stage 1: build the React frontend --------
FROM node:20-alpine AS web-build

WORKDIR /web
COPY web/package.json web/pnpm-lock.yaml* ./
RUN corepack enable && pnpm install --frozen-lockfile=false
COPY web/ .
RUN pnpm build
# `pnpm build` with `output: 'export'` writes the static site to /web/out


# -------- stage 2: Python runtime + bundled UI --------
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY src ./src
COPY backend ./backend
COPY --from=web-build /web/out ./web/out

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
