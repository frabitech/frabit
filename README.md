![logo](images/Frabit.png)

Frabit version v2.0.1-dev
=========================
![PyPI - License](https://img.shields.io/github/license/blylei/frabit)
[![downloads](https://img.shields.io/github/downloads/blylei/frabit/total.svg)](https://github.com/blylei/frabit/releases) 
[![release](https://img.shields.io/github/v/release/blylei/frabit.svg)](https://github.com/blylei/frabit/releases)

[size](https://img.shields.io/github/repo-size/blylei/frabit)
# Frabit 集成了mysqldump、mysqlbinlog、xtrabackup等开源工具来完成MySQL的日常备份、恢复任务
# 工具简介
只需要根据备份场景，在策略配置文件中配置策略；添加需要备份的实例，即可自动完成备份、恢复、归档等需要DBA手动完成的任务。Frabit主要是调用第三方的工具来自动完成备份、巡检、恢复等任务。将策略与备份逻辑解耦，全程不需要额外编写脚本。目前计划实现的功能如下：
 -  执行备份操作
     
     1 . 逻辑备份:根据备份策略，调用[mysqldump](https://dev.mysql.com/doc/refman/5.7/en/mysqldump.html) 进行备份     
     
     2 . 物理备份:根据备份策略，调用[XtraBackup](https://www.percona.com/doc/percona-xtrabackup/LATEST/index.html) 进行备份
     
     3 . binlog备份:根据备份策略，调用[mysqlbinlog](https://dev.mysql.com/doc/refman/5.7/en/mysqlbinlog.html) 从对应的主库实时转储binlog

  
 -  备份恢复演练

# 安装

 - build from source code
 ```shell
 shell> git https://github.com/blylei/frabit.git
 shell> cd frabit
 shell> python setup.py install
```      

Frabit 将备份策略，备份任务、备份实例以及巡检记录存储到MySQL数据库中。因此，在安装好Frabit之后，需要执行下列语句来初始化mydbs
```bash
mysql -u root -p < ${frabit_src_dir}/script/init_frabit.sql
```
 
# LICENSE 

Copyright (C) 2020-2021 Blylei Limited

Frabit is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

Frabit is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with Barman. If not, see http://www.gnu.org/licenses/.