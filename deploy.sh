#!/bin/bash
# ============================================================
# 图书馆管理系统 - 阿里云一键部署脚本
# 使用方法: bash deploy.sh [选项]
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════╗"
echo "║     图书馆管理系统 - 部署脚本 v2.0          ║"
echo "╚══════════════════════════════════════════════╝"
echo -e "${NC}"

# ---- 检查依赖 ----
check_deps() {
    echo -e "${YELLOW}[1/4] 检查依赖...${NC}"

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        echo "请先安装 Docker: curl -fsSL https://get.docker.com | bash"
        exit 1
    fi
    echo -e "  ${GREEN}✓ Docker $(docker --version | cut -d' ' -f3 | cut -d',' -f1)${NC}"

    if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        echo -e "${RED}错误: Docker Compose 未安装${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}✓ Docker Compose${NC}"
}

# ---- 配置环境 ----
setup_env() {
    echo -e "\n${YELLOW}[2/4] 配置环境变量...${NC}"

    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            # 生成随机密钥
            SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "s/SECRET_KEY=.*/SECRET_KEY=$SECRET/" .env
            else
                sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET/" .env
            fi
            echo -e "  ${GREEN}✓ 已创建 .env 文件（含随机 SECRET_KEY）${NC}"
        else
            echo -e "  ${YELLOW}⚠ .env.example 不存在，跳过${NC}"
        fi
    else
        echo -e "  ${GREEN}✓ .env 已存在${NC}"
    fi
}

# ---- 构建并启动 ----
deploy() {
    echo -e "\n${YELLOW}[3/4] 构建镜像并启动服务...${NC}"

    # 拉取基础镜像
    docker pull python:3.12-slim 2>/dev/null || true

    # 构建并启动
    docker compose up -d --build

    echo -e "  ${GREEN}✓ 服务已启动${NC}"
}

# ---- 验证部署 ----
verify() {
    echo -e "\n${YELLOW}[4/4] 验证部署...${NC}"

    # 等待服务就绪
    echo "  等待服务就绪..."
    for i in $(seq 1 30); do
        if curl -s http://localhost/healthz > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ 服务就绪${NC}"
            break
        fi
        sleep 2
    done

    # 显示状态
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  部署完成！${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "  首页:       ${GREEN}http://localhost${NC}"
    echo -e "  管理后台:   ${GREEN}http://localhost/login${NC}  (root / 1234)"
    echo -e "  读者入口:   ${GREEN}http://localhost/reader${NC}"
    echo -e "  健康检查:   ${GREEN}http://localhost/healthz${NC}"
    echo ""
    echo -e "  查看日志:   ${YELLOW}docker compose logs -f app${NC}"
    echo -e "  停止服务:   ${YELLOW}docker compose down${NC}"
    echo -e "  重启服务:   ${YELLOW}docker compose restart${NC}"
    echo ""
}

# ---- 显示帮助 ----
show_help() {
    echo "用法: bash deploy.sh [选项]"
    echo ""
    echo "选项:"
    echo "  deploy    构建并部署（默认）"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  logs      查看日志"
    echo "  status    查看状态"
    echo "  down      停止并删除容器"
    echo "  help      显示帮助"
}

# ---- 主逻辑 ----
case "${1:-deploy}" in
    deploy)
        check_deps
        setup_env
        deploy
        verify
        ;;
    start)
        echo "启动服务..."
        docker compose up -d
        verify
        ;;
    stop)
        echo "停止服务..."
        docker compose stop
        ;;
    restart)
        echo "重启服务..."
        docker compose restart
        verify
        ;;
    logs)
        docker compose logs -f --tail=100
        ;;
    status)
        docker compose ps
        echo ""
        curl -s http://localhost/healthz | python3 -m json.tool 2>/dev/null || echo "服务未就绪"
        ;;
    down)
        echo -e "${RED}将删除所有容器和数据卷！${NC}"
        read -p "确认? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v
            echo "已清理"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac
