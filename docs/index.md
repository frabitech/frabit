# Frabit 集成mysqldump、mysqlpump、mysqlbinlog、xtrabackup等开源工具来完成MySQL的备份、恢复任务
# 工具简介
只需要根据备份场景，在策略配置文件中配置策略；添加需要备份的实例，即可自动完成备份、恢复、归档等需要DBA手动完成的任务。Frabit主要是调用第三方的工具来自动完成备份、巡检、恢复等任务。将策略与备份逻辑解耦，全程不需要额外编写脚本。目前计划实现的功能如下：
 -  执行备份操作
     
     1 . 逻辑备份:根据备份策略，调用[mysqldump](https://dev.mysql.com/doc/refman/5.7/en/mysqldump.html)进行备份     
     
     2 . 物理备份:根据备份策略，调用[XtraBackup](https://www.percona.com/doc/percona-xtrabackup/LATEST/index.html)进行备份
     
     3 . binlog备份:根据备份策略，调用[mysqlbinlog](https://dev.mysql.com/doc/refman/5.7/en/mysqlbinlog.html)进行备份

  
 -  备份恢复演练
   
     1 . 本地备份文件恢复-online
     
     2 . 远程备份文件恢复-online
# 安装

 - pip安装
 ```shell
 pip install frabit
```      
 - whl文件安装
```shell
# 从pypi官网下载安装文件到当前路径下
 wget https://files.pythonhosted.org/packages/2c/57/af502e0e113f139b3f3add4f1efba899a730a365d2264d476e85b9591da5/mydbs-1.0.0-.py3-none-any.whl
# 使用pip进行安装
 pip install frabit-2.0.1-.py3-none-any.whl
``` 
Frabit 将备份策略，备份任务、备份实例以及巡检记录存储到MySQL数据库中。因此，在安装好Frabit之后，需要执行下列语句来初始化mydbs

```bash
mysql -u root -p < ${frabit_src_dir}/script/init_frabit.sql
```
 
