FROM node:20-alpine AS web-build

WORKDIR /web

ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY focus/web/package.json focus/web/package-lock.json ./
RUN npm ci

COPY focus/web ./
RUN npm run build


FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
COPY --from=web-build /web/dist /app/focus/web/dist

EXPOSE 8000

CMD ["uvicorn", "focus.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
