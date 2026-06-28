# 问题：MySQL查询速度慢，接口响应超时

## 场景
数据量增大后，原本正常的接口开始变慢，
用户反馈页面加载超过5秒，甚至超时报错。

## 报错信息
504 Gateway Timeout
PDOException: SQLSTATE[HY000]: max_execution_time exceeded

## 原因
1. 查询没有走索引，全表扫描
2. SELECT * 返回过多不需要的字段
3. 关联查询过多，JOIN层级深
4. 数据量级到达瓶颈，缺少分页

## 解决方案
1. 先用EXPLAIN定位问题
   EXPLAIN SELECT * FROM orders WHERE user_id = 123;
   - 看type字段，ALL表示全表扫描，需要加索引

2. 根据情况加索引
   - ALTER TABLE orders ADD INDEX idx_user_id (user_id);

3. 只查需要的字段
   SELECT id, status, created_at FROM orders

4. 大数据量强制分页
   LIMIT 20 OFFSET 0
