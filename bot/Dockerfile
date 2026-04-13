FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DISPLAY=:99

WORKDIR /app

# =============================
# 1. Dependencias sistema + Xvfb
# =============================
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    apt-transport-https \
    xvfb \
    # Dependencias de Chromium/Edge
    libnss3 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libxshmfence1 \
    libglu1-mesa \
    # Dependencias adicionales necesarias
    fonts-liberation \
    libappindicator3-1 \
    libatk1.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxi6 \
    libxtst6 \
    libdrm2 \
    libxkbcommon0 \
    libxfixes3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =============================
# 2. Microsoft Edge
# =============================
RUN wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/edge stable main" \
    > /etc/apt/sources.list.d/microsoft-edge.list

RUN apt-get update && apt-get install -y microsoft-edge-stable \
    && rm -rf /var/lib/apt/lists/*

# =============================
# 3. Python dependencies
# =============================
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . /app

# =============================
# 4. Script de arranque mejorado
# =============================
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🚀 Iniciando Xvfb..."\n\
# Iniciar Xvfb en segundo plano\n\
Xvfb :99 -screen 0 1280x1024x24 -ac &\n\
XVFB_PID=$!\n\
\n\
# Esperar a que Xvfb esté listo\n\
sleep 3\n\
\n\
# Verificar que Xvfb está corriendo\n\
if ! kill -0 $XVFB_PID 2>/dev/null; then\n\
    echo "❌ Error: Xvfb no pudo iniciarse"\n\
    exit 1\n\
fi\n\
\n\
export DISPLAY=:99\n\
echo "🌐 DISPLAY=$DISPLAY"\n\
\n\
# Opcional: Verificar que el display está disponible\n\
xdpyinfo > /dev/null 2>&1 || echo "⚠️  Advertencia: No se pudo verificar display"\n\
\n\
echo "🚀 Ejecutando scraper..."\n\
exec python main.py\n\
\n\
# Limpiar al salir\n\
trap "kill $XVFB_PID" EXIT' > /start.sh \
    && chmod +x /start.sh

CMD ["/start.sh"]