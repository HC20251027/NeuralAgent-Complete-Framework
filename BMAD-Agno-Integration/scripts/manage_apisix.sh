#!/bin/bash

# APISIX网关管理工具脚本
# 提供网关的启动、停止、配置管理等操作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
APISIX_HOME=${APISIX_HOME:-"/usr/local/apisix"}
APISIX_CONF=${APISIX_CONF:-"configs/apisix.yaml"}
LOG_DIR=${LOG_DIR:-"/tmp/apisix"}
PID_FILE=${PID_FILE:-"/tmp/apisix.pid"}

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 检查APISIX安装
check_apisix() {
    if [ ! -d "$APISIX_HOME" ]; then
        log_error "APISIX未安装或安装目录不存在: $APISIX_HOME"
        log_info "请先安装APISIX: https://apisix.apache.org/docs/apisix/getting-started/"
        exit 1
    fi
    
    if ! command -v apisix &> /dev/null; then
        log_error "APISIX命令未找到，请检查PATH设置"
        exit 1
    fi
    
    log_info "APISIX环境检查通过"
}

# 创建必要目录
create_directories() {
    mkdir -p "$LOG_DIR"
    log_info "创建日志目录: $LOG_DIR"
}

# 启动APISIX
start_apisix() {
    log_info "启动APISIX网关..."
    
    check_apisix
    create_directories
    
    # 检查是否已经运行
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warn "APISIX已经在运行 (PID: $PID)"
            return 0
        else
            log_warn "删除过期的PID文件"
            rm -f "$PID_FILE"
        fi
    fi
    
    # 启动APISIX
    cd "$APISIX_HOME"
    apisix start --config-file="$APISIX_CONF" &
    APISIX_PID=$!
    
    # 保存PID
    echo "$APISIX_PID" > "$PID_FILE"
    
    # 等待启动
    sleep 3
    
    # 检查启动状态
    if ps -p "$APISIX_PID" > /dev/null 2>&1; then
        log_info "APISIX启动成功 (PID: $APISIX_PID)"
        
        # 检查健康状态
        if curl -s http://127.0.0.1:9080/apisix/status > /dev/null; then
            log_info "APISIX健康检查通过"
        else
            log_warn "APISIX启动完成，但健康检查失败"
        fi
    else
        log_error "APISIX启动失败"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# 停止APISIX
stop_apisix() {
    log_info "停止APISIX网关..."
    
    if [ ! -f "$PID_FILE" ]; then
        log_warn "未找到PID文件，APISIX可能未运行"
        return 0
    fi
    
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID"
        
        # 等待停止
        for i in {1..30}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        if ps -p "$PID" > /dev/null 2>&1; then
            log_warn "优雅停止失败，强制终止"
            kill -9 "$PID"
        fi
        
        log_info "APISIX已停止"
    else
        log_warn "APISIX未运行"
    fi
    
    rm -f "$PID_FILE"
}

# 重启APISIX
restart_apisix() {
    log_info "重启APISIX网关..."
    stop_apisix
    sleep 2
    start_apisix
}

# 查看状态
status_apisix() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            log_info "APISIX正在运行 (PID: $PID)"
            
            # 检查健康状态
            if curl -s http://127.0.0.1:9080/apisix/status > /dev/null; then
                log_info "APISIX健康状态: 正常"
            else
                log_warn "APISIX健康状态: 异常"
            fi
        else
            log_info "APISIX未运行"
        fi
    else
        log_info "APISIX未运行"
    fi
}

# 查看日志
logs_apisix() {
    if [ "$1" == "follow" ]; then
        tail -f "$LOG_DIR/error.log" "$LOG_DIR/access.log" 2>/dev/null || log_error "日志文件不存在"
    else
        if [ -f "$LOG_DIR/error.log" ]; then
            log_info "=== 错误日志 ==="
            tail -n 50 "$LOG_DIR/error.log"
        fi
        
        if [ -f "$LOG_DIR/access.log" ]; then
            log_info "=== 访问日志 ==="
            tail -n 50 "$LOG_DIR/access.log"
        fi
    fi
}

# 测试配置
test_config() {
    log_info "测试APISIX配置..."
    
    check_apisix
    
    cd "$APISIX_HOME"
    if apisix test --config-file="$APISIX_CONF"; then
        log_info "配置测试通过"
    else
        log_error "配置测试失败"
        exit 1
    fi
}

# 初始化配置
init_config() {
    log_info "初始化APISIX配置..."
    
    # 创建配置目录
    mkdir -p configs/apisix
    
    # 复制默认配置
    if [ ! -f "configs/apisix.yaml" ]; then
        cp configs/apisix.yaml configs/apisix/apisix.yaml
        log_info "已创建默认配置文件: configs/apisix/apisix.yaml"
    fi
    
    # 创建Python配置管理脚本
    cat > scripts/apisix_manager.py << 'EOF'
#!/usr/bin/env python3
"""
APISIX网关配置管理脚本
"""

import asyncio
import sys
import os
sys.path.append('.')

from apisix.gateway.communication_interface import GatewayCommunicationInterface
from apisix.gateway.route_manager import RouteManager, ServiceInfo, RouteInfo
from apisix.gateway.plugin_manager import PluginManager

async def main():
    # 初始化通信接口
    gateway = GatewayCommunicationInterface()
    await gateway.initialize()
    
    # 同步配置到APISIX
    result = await gateway.sync_configuration_to_apisix()
    print(f"配置同步结果: {result}")
    
    # 获取网关状态
    status = await gateway.get_gateway_status()
    print(f"网关状态: {status}")

if __name__ == "__main__":
    asyncio.run(main())
EOF
    
    chmod +x scripts/apisix_manager.py
    log_info "配置管理脚本已创建: scripts/apisix_manager.py"
}

# 同步配置
sync_config() {
    log_info "同步配置到APISIX..."
    
    if command -v python3 &> /dev/null; then
        python3 scripts/apisix_manager.py
    else
        log_error "Python3未安装，无法执行配置同步"
        exit 1
    fi
}

# 健康检查
health_check() {
    log_info "执行APISIX健康检查..."
    
    # 检查进程状态
    status_apisix
    
    # 检查端口监听
    if netstat -ln | grep -q ":9080 "; then
        log_info "APISIX端口监听正常"
    else
        log_warn "APISIX端口监听异常"
    fi
    
    # 检查API响应
    if curl -s http://127.0.0.1:9180/apisix/admin/server_info > /dev/null; then
        log_info "Admin API响应正常"
    else
        log_warn "Admin API响应异常"
    fi
    
    if curl -s http://127.0.0.1:9080/apisix/status > /dev/null; then
        log_info "代理端口响应正常"
    else
        log_warn "代理端口响应异常"
    fi
}

# 显示帮助
show_help() {
    echo "APISIX网关管理工具"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start           启动APISIX网关"
    echo "  stop            停止APISIX网关"
    echo "  restart         重启APISIX网关"
    echo "  status          查看APISIX状态"
    echo "  logs [follow]   查看APISIX日志"
    echo "  test            测试配置文件"
    echo "  init            初始化配置"
    echo "  sync            同步配置到APISIX"
    echo "  health          执行健康检查"
    echo "  help            显示此帮助信息"
    echo ""
    echo "环境变量:"
    echo "  APISIX_HOME     APISIX安装目录 (默认: /usr/local/apisix)"
    echo "  APISIX_CONF     配置文件路径 (默认: configs/apisix.yaml)"
    echo "  LOG_DIR         日志目录 (默认: /tmp/apisix)"
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        "start")
            start_apisix
            ;;
        "stop")
            stop_apisix
            ;;
        "restart")
            restart_apisix
            ;;
        "status")
            status_apisix
            ;;
        "logs")
            logs_apisix "$2"
            ;;
        "test")
            test_config
            ;;
        "init")
            init_config
            ;;
        "sync")
            sync_config
            ;;
        "health")
            health_check
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"