# 问题：PHP Session失效或不生效111

## 场景
用户登录后session正常，但过一段时间自动退出，
或者在多台服务器部署后session频繁丢失。

## 报错信息
session数据为空，用户被强制退出登录

## 原因
1. 单机：session文件存储路径权限不足或磁盘满
2. 多机：负载均衡下请求打到不同服务器，session不共享
3. session过期时间配置过短

## 解决方案
1. 单机排查
   - 检查session.save_path目录是否可写
   - df -h 确认磁盘空间

2. 多机环境（根本解法）
   - 改用Redis存储session
   - php.ini配置：
     session.handler = redis
     session.save_path = "tcp://127.0.0.1:6379"

3. 调整过期时间
   - session.gc_maxlifetime = 7200
