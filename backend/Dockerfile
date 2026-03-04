FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴：libpq (psycopg binary) + postgresql-client (dbshell 需要 psql)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 先複製 requirements 以利用 Docker layer 快取
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案原始碼 (由於 Build Context 改為根目錄，指定複製 backend 資料夾內容到 /app)
COPY backend/ /app/

# 賦予 entrypoint.sh 執行權限
RUN chmod +x /app/entrypoint.sh

# 對外暴露 Django 開發伺服器 port
EXPOSE 8000

# 使用 sh 直譯器執行，避免 Mac 主機上的檔案權限問題導致 "permission denied"
ENTRYPOINT ["sh", "/app/entrypoint.sh"]
