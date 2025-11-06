"""
数据库初始化脚本
一键初始化完整的数据库环境
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.database.connection import db_connection
from code.database.vector_store import VectorDatabase
from code.database.migration import DatabaseMigration
from code.database.backup import DatabaseBackup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def initialize_database():
    """初始化完整数据库环境"""
    try:
        logger.info("开始初始化数据库环境...")
        
        # 1. 初始化数据库连接
        logger.info("1. 初始化数据库连接...")
        await db_connection.initialize()
        
        # 测试连接
        if await db_connection.test_connection():
            logger.info("✓ 数据库连接成功")
        else:
            raise Exception("数据库连接失败")
        
        # 2. 初始化向量数据库
        logger.info("2. 初始化向量数据库...")
        vector_db = VectorDatabase()
        await vector_db.initialize_vector_extensions()
        await vector_db.create_tables()
        logger.info("✓ 向量数据库初始化成功")
        
        # 3. 运行数据库迁移
        logger.info("3. 执行数据库迁移...")
        migration = DatabaseMigration()
        migration_count = await migration.migrate()
        logger.info(f"✓ 执行了 {migration_count} 个迁移")
        
        # 4. 初始化备份系统
        logger.info("4. 初始化备份系统...")
        backup = DatabaseBackup()
        await backup.initialize_backup_system()
        logger.info("✓ 备份系统初始化成功")
        
        # 5. 创建初始备份
        logger.info("5. 创建初始备份...")
        backup_file = await backup.create_full_backup("初始化备份")
        logger.info(f"✓ 初始备份创建成功: {backup_file}")
        
        # 6. 验证初始化结果
        logger.info("6. 验证初始化结果...")
        await verify_initialization()
        
        logger.info("🎉 数据库环境初始化完成！")
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def verify_initialization():
    """验证初始化结果"""
    try:
        # 检查表是否存在
        tables = [
            'text_embeddings',
            'image_embeddings',
            'audio_embeddings',
            'multimodal_embeddings',
            'agent_memories',
            'schema_migrations',
            'backup_records'
        ]
        
        for table in tables:
            result = await db_connection.execute_query(
                "SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = $1;",
                table
            )
            
            if result[0]['count'] == 0:
                raise Exception(f"表 {table} 不存在")
        
        # 检查向量扩展
        result = await db_connection.execute_query(
            "SELECT COUNT(*) as count FROM pg_extension WHERE extname = 'vector';"
        )
        
        if result[0]['count'] == 0:
            raise Exception("pgvector扩展未安装")
        
        logger.info("✓ 数据库初始化验证通过")
        
    except Exception as e:
        logger.error(f"初始化验证失败: {e}")
        raise


async def create_sample_data():
    """创建示例数据"""
    try:
        logger.info("创建示例数据...")
        
        vector_db = VectorDatabase()
        
        # 创建示例文本嵌入
        sample_texts = [
            "人工智能是计算机科学的一个分支",
            "机器学习是AI的重要子领域", 
            "深度学习使用神经网络进行学习",
            "自然语言处理让计算机理解人类语言",
            "计算机视觉让机器看懂图像"
        ]
        
        import numpy as np
        
        for i, text in enumerate(sample_texts):
            # 生成随机向量作为示例
            embedding = np.random.rand(1536).tolist()
            
            await vector_db.store_text_embedding(
                content=text,
                embedding=embedding,
                metadata={"category": "sample", "index": i},
                source_type="sample",
                source_id=f"sample_{i}"
            )
        
        # 创建示例智能体记忆
        sample_memories = [
            {
                "type": "preference",
                "content": {"language": "中文", "style": "专业"},
                "importance": 0.8
            },
            {
                "type": "knowledge", 
                "content": {"domain": "AI", "expertise": ["ML", "NLP", "CV"]},
                "importance": 0.9
            },
            {
                "type": "context",
                "content": {"project": "BMAD-Agno Integration", "role": "developer"},
                "importance": 0.7
            }
        ]
        
        for i, memory in enumerate(sample_memories):
            embedding = np.random.rand(1536).tolist() if i % 2 == 0 else None
            
            await vector_db.store_agent_memory(
                agent_id="sample_agent",
                memory_type=memory["type"],
                content=memory["content"],
                embedding=embedding,
                importance_score=memory["importance"]
            )
        
        logger.info("✓ 示例数据创建完成")
        
    except Exception as e:
        logger.error(f"创建示例数据失败: {e}")
        raise


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库初始化工具')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--sample', action='store_true', help='创建示例数据')
    parser.add_argument('--verify', action='store_true', help='验证数据库状态')
    
    args = parser.parse_args()
    
    try:
        if args.init:
            await initialize_database()
        elif args.sample:
            await create_sample_data()
        elif args.verify:
            await verify_initialization()
        else:
            # 默认执行完整初始化
            await initialize_database()
            await create_sample_data()
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
    except Exception as e:
        logger.error(f"操作失败: {e}")
        sys.exit(1)
    finally:
        await db_connection.close()


if __name__ == "__main__":
    asyncio.run(main())