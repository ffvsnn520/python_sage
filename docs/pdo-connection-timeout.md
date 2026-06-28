# 问题：PDO连接MySQL超时

## 场景
PHP使用PDO连接MySQL数据库时，本地开发正常，
生产环境偶发连接失败，或高并发下频繁报连接超时。

## 报错信息
PDOException: SQLSTATE[HY000] [2002] Connection timed out
PDOException: SQLSTATE[HY000] [1045] Access denied for user

## 原因
1. 网络问题：服务器之间网络不通或不稳定
2. 权限问题：MySQL账号没有授权该IP访问
3. 连接数耗尽：MySQL max_connections被打满，新连接被拒绝
4. 防火墙：3306端口被防火墙拦截

## 解决方案
1. 排查网络
   - ping 数据库地址确认网络通
   - telnet db_host 3306 确认端口可访问

2. 排查权限
   - 登录MySQL执行：SHOW GRANTS FOR 'user'@'%';
   - 确认host是否包含当前服务器IP

3. 排查连接数
   - 执行：SHOW STATUS LIKE 'Threads_connected';
   - 对比：SHOW VARIABLES LIKE 'max_connections';
   - 如果接近上限，考虑加连接池或调大max_connections

4. 代码层加重试
   - 捕获异常后等待500ms重试，最多重试3次
