#!/bin/bash

# 数据库管理工具脚本
# 提供数据库的初始化、备份、恢复等操作

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装"
        exit 1
    fi
    
    log_info "Python环境检查通过"
}

# 检查PostgreSQL工具
check_postgres_tools() {
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump 未安装，请安装PostgreSQL客户端工具"
        exit 1
    fi
    
    if ! command -v psql &> /dev/null; then
        log_error "psql 未安装，请安装PostgreSQL客户端工具"
        exit 1
    fi
    
    log_info "PostgreSQL工具检查通过"
}

# 检查环境变量
check_env() {
    if [ -f .env ]; then
        log_info "加载环境变量文件 .env"
        export $(cat .env | grep -v '^#' | xargs)
    fi
    
    # 检查必需的数据库配置
    if [ -z "$DB_HOST" ]; then
        DB_HOST="localhost"
        log_warn "使用默认DB_HOST: localhost"
    fi
    
    if [ -z "$DB_PORT" ]; then
        DB_PORT="5432"
        log_warn "使用默认DB_PORT: 5432"
    fi
    
    if [ -z "$DB_NAME" ]; then
        DB_NAME="ai_agents"
        log_warn "使用默认DB_NAME: ai_agents"
    fi
    
    if [ -z "$DB_USER" ]; then
        DB_USER="postgres"
        log_warn "使用默认DB_USER: postgres"
    fi
}

# 初始化数据库
init_database() {
    log_info "开始初始化数据库..."
    
    check_python
    check_postgres_tools
    check_env
    
    # 运行初始化脚本
    python3 scripts/init_database.py --init
    
    log_info "数据库初始化完成"
}

# 创建示例数据
create_sample_data() {
    log_info "创建示例数据..."
    
    check_python
    
    python3 scripts/init_database.py --sample
    
    log_info "示例数据创建完成"
}

# 备份数据库
backup_database() {
    local backup_type=${1:-"full"}
    local description=${2:-"手动备份"}
    
    log_info "开始备份数据库 (类型: $backup_type)..."
    
    check_postgres_tools
    check_env
    
    # 创建备份目录
    mkdir -p backups
    
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="backups/backup_${backup_type}_${timestamp}.sql"
    
    # 执行备份
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -f "$backup_file" \
        --verbose
    
    if [ $? -eq 0 ]; then
        local file_size=$(du -h "$backup_file" | cut -f1)
        log_info "备份完成: $backup_file (大小: $file_size)"
        
        # 记录到数据库
        python3 -c "
import asyncio
import sys
sys.path.append('.')
from code.database.backup import DatabaseBackup

async def record_backup():
    backup = DatabaseBackup()
    await backup.initialize_backup_system()
    await backup.db.execute_command(
        'INSERT INTO backup_records (backup_type, file_path, description) VALUES (\\'$backup_type\\', \\'$backup_file\\', \\'$description\\');'
    )
    print('备份记录已保存')

asyncio.run(record_backup())
"
    else
        log_error "备份失败"
        exit 1
    fi
}

# 恢复数据库
restore_database() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        log_error "请指定备份文件路径"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi
    
    log_warn "即将恢复数据库到备份文件: $backup_file"
    read -p "确认继续? (y/N): " confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        log_info "操作已取消"
        exit 0
    fi
    
    log_info "开始恢复数据库..."
    
    check_postgres_tools
    check_env
    
    # 执行恢复
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -f "$backup_file" \
        --quiet
    
    if [ $? -eq 0 ]; then
        log_info "数据库恢复完成"
    else
        log_error "数据库恢复失败"
        exit 1
    fi
}

# 列出备份
list_backups() {
    log_info "数据库备份列表:"
    
    check_python
    
    python3 -c "
import asyncio
import sys
sys.path.append('.')
from code.database.backup import DatabaseBackup

async def list_backups():
    backup = DatabaseBackup()
    await backup.initialize_backup_system()
    backups = await backup.list_backups()
    
    if not backups:
        print('没有找到备份记录')
        return
    
    print(f'{'ID':<5} {'类型':<10} {'文件路径':<50} {'大小':<10} {'创建时间':<20}')
    print('-' * 100)
    
    for b in backups:
        size_str = f\"{b['file_size']/1024/1024:.1f}MB\" if b['file_size'] else 'N/A'
        print(f\"{b['id']:<5} {b['backup_type']:<10} {b['file_path'][:50]:<50} {size_str:<10} {str(b['created_at'])[:19]:<20}\")

asyncio.run(list_backups())
"
}

# 清理过期备份
cleanup_backups() {
    log_info "清理过期备份..."
    
    check_python
    
    python3 -c "
import asyncio
import sys
sys.path.append('.')
from code.database.backup import DatabaseBackup

async def cleanup():
    backup = DatabaseBackup()
    await backup.initialize_backup_system()
    count = await backup.cleanup_old_backups()
    print(f'清理了 {count} 个过期备份')

asyncio.run(cleanup())
"
}

# 验证数据库状态
verify_database() {
    log_info "验证数据库状态..."
    
    check_python
    
    python3 scripts/init_database.py --verify
}

# 运行迁移
run_migrations() {
    log_info "运行数据库迁移..."
    
    check_python
    
    python3 -c "
import asyncio
import sys
sys.path.append('.')
from code.database.migration import DatabaseMigration

async def run_migrations():
    migration = DatabaseMigration()
    count = await migration.migrate()
    print(f'执行了 {count} 个迁移')

asyncio.run(run_migrations())
"
}

# 显示帮助信息
show_help() {
    echo "数据库管理工具"
    echo ""
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "命令:"
    echo "  init              初始化数据库"
    echo "  sample            创建示例数据"
    echo "  backup [类型] [描述]  备份数据库 (类型: full|vector)"
    echo "  restore <文件>    恢复数据库"
    echo "  list              列出所有备份"
    echo "  cleanup           清理过期备份"
    echo "  verify            验证数据库状态"
    echo "  migrate           运行数据库迁移"
    echo "  help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 init                    # 初始化数据库"
    echo "  $0 backup full             # 创建完整备份"
    echo "  $0 restore backups/backup.sql  # 恢复数据库"
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        "init")
            init_database
            ;;
        "sample")
            create_sample_data
            ;;
        "backup")
            backup_database "$2" "$3"
            ;;
        "restore")
            restore_database "$2"
            ;;
        "list")
            list_backups
            ;;
        "cleanup")
            cleanup_backups
            ;;
        "verify")
            verify_database
            ;;
        "migrate")
            run_migrations
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