#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识树管理系统 - 导出为 JSON 功能
支持将整个知识树从 SQLite 数据库导出为一个 JSON 文件。
自动检测表结构，未来新增字段无需修改本脚本。
"""

import sqlite3
import json

DB_FILE = 'knowledge_tree.db'          # 数据库文件名
OUTPUT_FILE = 'my_knowledge_tree.json' # 默认导出文件名


def export_to_json_dynamic(filepath=None):
    """
    导出知识树到 JSON 文件，自动包含表中除 id、parent_id 之外的所有列。
    
    :param filepath: JSON 文件路径。若为 None，则使用默认文件名 OUTPUT_FILE
    """
    if filepath is None:
        filepath = OUTPUT_FILE

    # 1. 连接数据库
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 2. 获取表的结构信息
    c.execute("PRAGMA table_info(knowledge_nodes)")
    table_info = c.fetchall()
    # table_info 中每一行是：(cid, name, type, notnull, dflt_value, pk)
    # 我们只需要列名（name），排除 id 和 parent_id
    export_cols = [info[1] for info in table_info 
                   if info[1] not in ('id', 'parent_id')]

    # 3. 构造查询，同时保留 id 和 parent_id 用于构建树结构
    query_cols = 'id, ' + ', '.join(export_cols) + ', parent_id'
    c.execute(f"SELECT {query_cols} FROM knowledge_nodes")
    rows = c.fetchall()
    conn.close()

    # 4. 构建节点字典，键为节点 id，值为节点数据
    nodes = {}
    for row in rows:
        node_id = row[0]
        # 提取用户字段的值（去掉 row 的第一个 id 和最后一个 parent_id）
        user_values = row[1:-1]
        node_data = dict(zip(export_cols, user_values))
        node_data['children'] = []                     # 为每个节点预留 children 列表
        nodes[node_id] = node_data
        # 暂时把 parent_id 挂在字典里，稍后构建树时会用到并移除
        nodes[node_id]['_parent_id'] = row[-1]

    # 5. 组装树结构
    roots = []
    for node_id, node in nodes.items():
        parent_id = node.pop('_parent_id')            # 移除临时字段
        if parent_id is None:
            roots.append(node)                        # 没有父节点的就是根
        else:
            if parent_id in nodes:
                # 将当前节点挂到其父节点的 children 列表中
                nodes[parent_id]['children'].append(node)

    # 6. 如果只有一棵树（只有一个根），直接输出根对象而不是数组
    if len(roots) == 1:
        roots = roots[0]

    # 7. 写入 JSON 文件
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(roots, f, ensure_ascii=False, indent=2)

    print(f"✅ 知识树已导出至 {filepath}")


# -------------------------- 演示部分 --------------------------
if __name__ == '__main__':
    # 初次运行前，请确保已经运行过主程序并插入了示例数据。
    # 导出到默认文件 my_knowledge_tree.json
    export_to_json_dynamic()
    
    # 也可以指定路径：
    # export_to_json_dynamic('backup/custom_tree.json')