TABLE level, type, status
FROM "知识图谱"
WHERE status != "completed"
SORT level asc