# Stage 1 — build wheels (throwaway build deps stay in this stage)
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2 — runtime
FROM python:3.11-slim

# Install Chrome (runtime dep for Selenium)
# NOTE: não usar `apt-get purge`/`autoremove` aqui — o Chrome é instalado com
# --no-install-recommends, então suas dependências ficam marcadas como "auto" e
# o autoremove as remove junto; purgar gnupg também derruba o Chrome por dependência.
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget gnupg curl \
    && mkdir -p /etc/apt/keyrings \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps from prebuilt wheels, then drop the wheels
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy the backend files (including the data folder); build context is ./backend,
# so "src" lands at /app/src and imports resolve as "src.*"
COPY . .

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
