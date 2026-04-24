import json
import re
from pathlib import Path


def safe_filename(name: str) -> str:
    """替换文件名中的非法字符"""
    return re.sub(r'[\\/*?:"<>|]', '-', name)


def gen_md(data, path='output-ob-map', parent_name=''):
    """
    递归生成 Obsidian 笔记
    data: {"children": [...]}
    path: 当前目录
    parent_name: 父节点的原始名称（用于子笔记的 parent 字段）
    返回：本层所有子节点的名称列表（供父笔记生成双链）
    """
    base_dir = Path(path)
    base_dir.mkdir(parents=True, exist_ok=True)

    child_names = []   # 记录本层子节点的原始名称

    for child in data['children']:
        orig_name = child['name']
        safe_name = safe_filename(orig_name)
        note_path = base_dir / f"{safe_name}.md"

        # 先递归处理子节点，获取它们的名称列表
        sub_names = []
        if child['children']:
            sub_dir = base_dir / safe_name
            sub_names = gen_md(
                {'children': child['children']},
                sub_dir,
                parent_name=orig_name
            )

        # --- 构建 Frontmatter ---
        frontmatter = (
            "---\n"
            f"type: {child['type']}\n"
            f"level: {child['level']}\n"
            f"status: not-started\n"
            f"priority: normal\n"
            f"tags: [knowledge]\n"
        )
        if parent_name:
            frontmatter += f"parent: \"{parent_name}\"\n"
        frontmatter += "---\n\n"

        # --- 构建正文 ---
        content = f"# {orig_name}\n\n"
        content += f"**难度等级**：{child['type']}\n\n"

        # 子节点列表（双链）
        if sub_names:
            content += "## 子节点\n\n"
            for sub in sub_names:
                content += f"- [[{sub}]]\n"
            content += "\n"

        content += "## 学习笔记\n\n（在此记录……）\n\n"
        content += "## 相关链接\n\n（其他笔记链接）\n"

        # 写入文件
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter + content)

        child_names.append(orig_name)

    return child_names


if __name__ == '__main__':
    with open('data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 如果 JSON 是列表，依次处理所有根
    roots = data if isinstance(data, list) else [data]
    for root_node in roots:
        # 输出根目录名用根节点的 name
        root_dir = safe_filename(root_node.get('name', '知识图谱'))
        gen_md(root_node, path=f'output-ob-map/{root_dir}')