"""数据库迁移脚本：添加新字段"""
import sqlite3

DB_FILE = 'knowledge_tree.db'

def add_column_if_not_exists(conn, table, column, col_type):
    c = conn.cursor()
    c.execute(f"PRAGMA table_info({table})")
    existing = [info[1] for info in c.fetchall()]
    if column not in existing:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"已添加列 {column}")
    else:
        print(f"列 {column} 已存在，跳过。")

if __name__ == '__main__':
    conn = sqlite3.connect(DB_FILE)
    # 在这里添加你需要的字段，例如：
    add_column_if_not_exists(conn, "knowledge_nodes", "estimated_hours", "INTEGER")
    add_column_if_not_exists(conn, "knowledge_nodes", "notes", "TEXT")
    # 更多字段继续添加...
    conn.close()
    print("迁移完成。")
