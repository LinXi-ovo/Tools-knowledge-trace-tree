# 知识树管理系统


支持树形节点增删改查、JSON 导入、导出统计、数据库迁移。

## 快速开始

1. 进入项目目录：
   ```bash
   cd knowledge-tree-manager
   ```
2. 运行主程序：
   ```bash
   python knowledge_tree.py
   ```
3. 在菜单中输入 `1` 初始化数据库。
4. 使用其他选项进行增删改查、导入。

## 文件说明

| 文件 | 说明 |
| --- | --- |
| knowledge_tree.py | 主程序，包含菜单、CRUD、JSON导入、统计 |
| migrate_db.py | 数据库扩展脚本（添加新字段） |
| import_tree.json | 示例知识树 JSON，演示导入功能 |
| docs/user_guide.md | 详细使用手册 |

## 扩展字段

如需新增节点属性：
1. 编辑 `migrate_db.py` 中的字段名与类型，执行脚本。
2. 在 JSON 节点的字段中直接添加同名键，导入时自动识别。

## 依赖

- Python 3.6+
- 标准库（无需额外安装）
