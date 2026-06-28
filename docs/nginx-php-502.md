# 问题：Nginx + PHP-FPM 报502 Bad Gateway

## 场景
项目部署到服务器后，访问页面返回502，
或者运行一段时间后偶发502。

## 报错信息
502 Bad Gateway

## 原因
1. PHP-FPM进程未启动或已崩溃
2. PHP-FPM进程数不够，请求排队超时
3. Nginx配置的PHP-FPM地址端口不匹配

## 解决方案
1. 先确认PHP-FPM是否在运行
   systemctl status php-fpm
   ps aux | grep php-fpm

2. 查看PHP-FPM错误日志
   tail -f /var/log/php-fpm/error.log

3. 进程数不够时调整配置
   pm.max_children = 50
   pm.start_servers = 10

4. 确认Nginx配置
   fastcgi_pass 127.0.0.1:9000;
   确认端口和PHP-FPM监听端口一致
