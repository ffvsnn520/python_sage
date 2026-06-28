# 问题：PHP导出文件内存溢出

## 场景
使用PHPExcel或类似库导出大量数据到xlsx文件时，
需要先将数据库查询结果全部写入数组，再统一写入文件，
当数据量较大（通常万条以上）时触发PHP内存限制报错。

## 报错信息
Fatal error: Allowed memory size of 134217728 bytes exhausted

## 原因
PHP默认内存限制较低（通常128M），大数据量全部载入内存
会导致内存耗尽。

## 解决方案
1. 分批查询 + 流式写入（推荐）
   - 每次查询1000条，边查边写入文件，写完释放内存
   - 使用支持流式写入的库，如PhpSpreadsheet的StreamWriter

2. 临时调大内存限制（不推荐，治标不治本）
   ini_set('memory_limit', '512M');

3. 改用CSV格式导出
   - CSV不需要构建复杂对象，内存占用极低
   - 适合纯数据导出场景
