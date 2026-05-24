#!/bin/bash
# QMS 一键部署脚本
# 使用方法: chmod +x deploy.sh && ./deploy.sh

set -e

SERVER="ubuntu@18.143.190.101"
REMOTE_DIR="/opt/qms"
LOCAL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== QMS 部署脚本 ==="
echo "本地目录: $LOCAL_DIR"
echo "服务器: $SERVER"
echo "远程目录: $REMOTE_DIR"
echo ""

# 1. 上传代码到服务器
echo "[1/5] 上传代码到服务器..."
ssh "$SERVER" "sudo mkdir -p $REMOTE_DIR && sudo chown ubuntu:ubuntu $REMOTE_DIR"
rsync -avz --exclude '__pycache__' --exclude '*.db' --exclude '.DS_Store' \
    "$LOCAL_DIR/" "$SERVER:$REMOTE_DIR/"
echo "代码上传完成"

# 2. 安装 Python 依赖
echo "[2/5] 安装 Python 依赖..."
ssh "$SERVER" "cd $REMOTE_DIR && sudo pip3 install -r requirements.txt"
echo "依赖安装完成"

# 3. 初始化数据库并设置 WAL 模式
echo "[3/5] 初始化数据库 (WAL 模式)..."
ssh "$SERVER" "cd $REMOTE_DIR && python3 -c \"
from app import create_app
app = create_app()
import sqlite3
conn = sqlite3.connect('$REMOTE_DIR/qms.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.close()
print('Database initialized with WAL mode')
\""
echo "数据库初始化完成"

# 4. 配置 Nginx
echo "[4/5] 配置 Nginx..."
ssh "$SERVER" "sudo cp $REMOTE_DIR/deploy/nginx_qms.conf /etc/nginx/sites-available/qms.conf && \
    sudo ln -sf /etc/nginx/sites-available/qms.conf /etc/nginx/sites-enabled/qms.conf && \
    sudo nginx -t && sudo systemctl reload nginx"
echo "Nginx 配置完成"

# 5. 配置 systemd 服务
echo "[5/5] 配置 systemd 服务..."
ssh "$SERVER" "sudo cp $REMOTE_DIR/deploy/qms.service /etc/systemd/system/qms.service && \
    sudo systemctl daemon-reload && \
    sudo systemctl enable qms && \
    sudo systemctl restart qms"
echo "systemd 服务配置完成"

# 6. 配置定时备份
echo "[额外] 配置数据库定时备份..."
ssh "$SERVER" "(crontab -l 2>/dev/null; echo '0 * * * * cp $REMOTE_DIR/qms.db $REMOTE_DIR/backups/qms_\$(date +\%Y\%m\%d_\%H\%M).db && find $REMOTE_DIR/backups -name \"*.db\" -mtime +30 -delete') | crontab -"
ssh "$SERVER" "mkdir -p $REMOTE_DIR/backups"

echo ""
echo "=== 部署完成 ==="
echo "访问地址: http://18.143.190.101:3200"
echo "默认管理员: admin / admin123 (请立即修改密码!)"