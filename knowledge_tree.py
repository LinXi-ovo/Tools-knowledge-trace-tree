#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二十八届中国机器人及人工智能大赛 知识树管理系统
功能：创建数据库、插入初始知识树、增删改查节点、统计、导入JSON
"""

import sqlite3
import json
import os

from export_to_json_dynamic import export_to_json_dynamic

DB_FILE = 'knowledge_tree.db'

def get_connection():
    return sqlite3.connect(DB_FILE)

def create_database():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level INTEGER NOT NULL,
            type TEXT NOT NULL,
            parent_id INTEGER,
            FOREIGN KEY (parent_id) REFERENCES knowledge_nodes(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()
    print("数据库表已确保存在。")

def insert_initial_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM knowledge_nodes")
    if c.fetchone()[0] > 0:
        conn.close()
        print("数据库中已存在数据，跳过初始化。")
        return

    c.execute("INSERT INTO knowledge_nodes (name, level, type, parent_id) VALUES (?, ?, ?, ?)",
              ("项目总览", 0, "基础", None))
    root_id = c.lastrowid

    nodes_level1 = [
        ("大赛流程与规则", "必须掌握"),
        ("技术报告与答辩", "必须掌握"),
        ("Python编程", "前置知识"),
        ("ROS/ROS2", "必须掌握"),
        ("人工智能创新赛", "加分能力")
    ]
    parent_ids = {}
    for name, typ in nodes_level1:
        c.execute("INSERT INTO knowledge_nodes (name, level, type, parent_id) VALUES (?, ?, ?, ?)",
                  (name, 1, typ, root_id))
        parent_ids[name] = c.lastrowid

    data_level2 = [
        ("大赛流程与规则", "校赛/省赛/国赛", "必须掌握"),
        ("大赛流程与规则", "仲裁办法", "必须掌握"),
        ("技术报告与答辩", "报告撰写", "必须掌握"),
        ("技术报告与答辩", "答辩技巧", "必须掌握"),
        ("Python编程", "基础语法", "前置知识"),
        ("Python编程", "NumPy", "前置知识"),
        ("ROS/ROS2", "话题通信", "必须掌握"),
        ("ROS/ROS2", "TF坐标变换", "必须掌握"),
        ("人工智能创新赛", "大模型应用", "加分能力"),
    ]
    for parent_name, name, typ in data_level2:
        pid = parent_ids.get(parent_name)
        if pid:
            c.execute("INSERT INTO knowledge_nodes (name, level, type, parent_id) VALUES (?, ?, ?, ?)",
                      (name, 2, typ, pid))

    conn.commit()
    conn.close()
    print("初始知识树数据插入成功！")

def add_node(name, level, type, parent_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO knowledge_nodes (name, level, type, parent_id) VALUES (?, ?, ?, ?)",
              (name, level, type, parent_id))
    node_id = c.lastrowid
    conn.commit()
    conn.close()
    print(f"节点 '{name}' 添加成功，ID={node_id}")
    return node_id

def delete_node(node_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        WITH RECURSIVE descendants(id) AS (
            SELECT id FROM knowledge_nodes WHERE id = ?
            UNION ALL
            SELECT k.id FROM knowledge_nodes k
            INNER JOIN descendants d ON k.parent_id = d.id
        )
        SELECT id FROM descendants
    ''', (node_id,))
    ids_to_delete = [row[0] for row in c.fetchall()]
    for nid in ids_to_delete:
        c.execute("DELETE FROM knowledge_nodes WHERE id = ?", (nid,))
    conn.commit()
    conn.close()
    print(f"已删除节点及其子树，共计 {len(ids_to_delete)} 个节点。")
    return len(ids_to_delete)

def update_node(node_id, name=None, type=None):
    conn = get_connection()
    c = conn.cursor()
    if name:
        c.execute("UPDATE knowledge_nodes SET name = ? WHERE id = ?", (name, node_id))
    if type:
        c.execute("UPDATE knowledge_nodes SET type = ? WHERE id = ?", (type, node_id))
    conn.commit()
    conn.close()
    print("节点信息已更新。")

def get_children(parent_id=None):
    conn = get_connection()
    c = conn.cursor()
    if parent_id is None:
        c.execute("SELECT id, name, level, type, parent_id FROM knowledge_nodes WHERE parent_id IS NULL")
    else:
        c.execute("SELECT id, name, level, type, parent_id FROM knowledge_nodes WHERE parent_id = ?", (parent_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_subtree(node_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        WITH RECURSIVE subtree(id) AS (
            SELECT id FROM knowledge_nodes WHERE id = ?
            UNION ALL
            SELECT k.id FROM knowledge_nodes k
            INNER JOIN subtree s ON k.parent_id = s.id
        )
        SELECT k.id, k.name, k.level, k.type, k.parent_id FROM knowledge_nodes k
        INNER JOIN subtree s ON k.id = s.id
    ''', (node_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def search_node(keyword):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, level, type, parent_id FROM knowledge_nodes WHERE name LIKE ?", ('%' + keyword + '%',))
    rows = c.fetchall()
    conn.close()
    return rows

def get_node_by_id(node_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, name, level, type, parent_id FROM knowledge_nodes WHERE id = ?", (node_id,))
    row = c.fetchone()
    conn.close()
    return row

def count_by_type():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT type, COUNT(*) FROM knowledge_nodes GROUP BY type")
    rows = c.fetchall()
    conn.close()
    return rows

def max_depth():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(level) FROM knowledge_nodes")
    max_lvl = c.fetchone()[0]
    conn.close()
    return max_lvl

def import_from_json(filepath, clear_existing=False):
    """从JSON文件导入知识树，自动适配数据库现有列。"""
    with open(filepath, 'r', encoding='utf-8') as f:
        tree_data = json.load(f)

    conn = get_connection()
    c = conn.cursor()

    if clear_existing:
        c.execute("DELETE FROM knowledge_nodes")
        print("⚠️ 已清空原有数据！")

    # 读取数据库当前所有列（id除外）
    c.execute("PRAGMA table_info(knowledge_nodes)")
    db_columns = [info[1] for info in c.fetchall() if info[1] != 'id']

    def insert_node(node, parent_id=None):
        row = {}
        for col in db_columns:
            if col == 'parent_id':
                row[col] = parent_id
            elif col in node:
                row[col] = node[col]
            else:
                row[col] = None
        columns = ', '.join(row.keys())
        placeholders = ', '.join(['?'] * len(row))
        sql = f"INSERT INTO knowledge_nodes ({columns}) VALUES ({placeholders})"
        c.execute(sql, list(row.values()))
        node_id = c.lastrowid
        for child in node.get('children', []):
            insert_node(child, node_id)
        return node_id

    insert_node(tree_data)
    conn.commit()
    conn.close()
    print("✅ JSON 导入完成！")

def print_table(rows, columns=["ID", "名称", "层级", "类型", "父节点ID"]):
    if not rows:
        print("（无数据）")
        return
    header = " | ".join(columns)
    print(header)
    print("-" * len(header))
    for row in rows:
        print(" | ".join(str(item) for item in row))

def print_menu():
    print("\n" + "="*60)
    print("  第二十八届中国机器人及人工智能大赛 知识树管理系统")
    print("="*60)
    print("1. 初始化数据库（建表+示例数据）")
    print("2. 添加新节点")
    print("3. 删除节点（含子树）")
    print("4. 修改节点（名称/类型）")
    print("5. 查询：按ID查看节点")
    print("6. 查询：按关键词模糊搜索")
    print("7. 查询：显示某节点的子树")
    print("8. 统计各类别节点数量")
    print("9. 显示根节点下的直接子节点")
    print("10. 从JSON导入知识树")
    print("11. 导出数据库数据到json")
    print("0. 退出")
    print("-"*60)

def main():
    create_database()  # 确保表存在
    while True:
        print_menu()
        choice = input("请输入选项编号: ").strip()
        if choice == '1':
            insert_initial_data()
        elif choice == '2':
            name = input("节点名称: ").strip()
            if not name: continue
            level = int(input("层级: "))
            typ = input("类别: ").strip()
            parent_id_input = input("父节点ID (根请回车): ").strip()
            parent_id = int(parent_id_input) if parent_id_input else None
            add_node(name, level, typ, parent_id)
        elif choice == '3':
            nid = int(input("节点ID: "))
            node = get_node_by_id(nid)
            if node and input(f"确认删除 '{node[1]}' 及其子树？(y/n): ").strip().lower() == 'y':
                delete_node(nid)
        elif choice == '4':
            nid = int(input("节点ID: "))
            name = input("新名称: ").strip()
            typ = input("新类别: ").strip()
            update_node(nid, name=name if name else None, type=typ if typ else None)
        elif choice == '5':
            nid = int(input("节点ID: "))
            node = get_node_by_id(nid)
            print_table([node] if node else [])
        elif choice == '6':
            kw = input("关键词: ").strip()
            results = search_node(kw)
            print_table(results)
        elif choice == '7':
            nid = int(input("节点ID: "))
            subtree = get_subtree(nid)
            print_table(subtree)
        elif choice == '8':
            stats = count_by_type()
            print("类别统计：")
            for typ, cnt in stats:
                print(f"  {typ}: {cnt}")
            print(f"最大层级: {max_depth()}")
        elif choice == '9':
            roots = get_children(None)
            if roots:
                root = roots[0]
                print(f"根节点: {root[1]} (ID={root[0]})")
                children = get_children(root[0])
                print_table(children)
        elif choice == '10':
            path = input("JSON文件路径: ").strip()
            if not os.path.exists(path):
                print("文件不存在。")
            else:
                clear = input("清空原有数据？(y/n): ").strip().lower() == 'y'
                import_from_json(path, clear_existing=clear)
        elif choice == '11':
            path = input("导出文件路径（默认 my_tree.json）: ").strip()
            if not path:
                path = 'my_tree.json'
            export_to_json_dynamic(path)
        elif choice == '0':
            print("再见！")
            break
        else:
            print("无效选项。")

if __name__ == '__main__':
    main()
