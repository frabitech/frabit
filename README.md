![logo](images/Frabit.png)

Frabit
=========================
![PyPI - License](https://img.shields.io/github/license/blylei/frabit)
![size](https://img.shields.io/github/repo-size/blylei/frabit)
![lanwage](https://img.shields.io/github/languages/top/blylei/frabit)
[![status](https://img.shields.io/github/checks-status/blylei/frabit/master)](https://github.com/blylei/frabit/releases)
[![downloads](https://img.shields.io/github/downloads/blylei/frabit/total.svg)](https://github.com/blylei/frabit/releases)
[![release](https://img.shields.io/github/v/release/blylei/frabit.svg)](https://github.com/blylei/frabit/releases)


# Frabit 一个专用于MySQL的备份管理工具
## 用途
只需要根据备份场景，在策略配置文件中配置策略；添加需要备份的实例，即可自动完成备份、恢复、归档等需要DBA手动完成的任务。Frabit主要是调用第三方的工具来自动完成备份、巡检、恢复等任务。将策略与备份逻辑解耦，全程不需要额外编写脚本。目前计划实现的功能如下：
 -  执行备份操作
     
     1 . 逻辑备份:根据备份策略，调用[mysqldump](https://dev.mysql.com/doc/refman/5.7/en/mysqldump.html) 进行备份     
     
     2 . 物理备份:根据备份策略，调用[XtraBackup](https://www.percona.com/doc/percona-xtrabackup/LATEST/index.html) 进行备份
     
     3 . binlog备份:根据备份策略，调用[mysqlbinlog](https://dev.mysql.com/doc/refman/5.7/en/mysqlbinlog.html) 从对应的主库实时转储binlog

  
 -  备份恢复演练
## 文档
[简体中文](docs/zh/README.md)

[English](docs/en/README.md)

## LICENSE 

Copyright (C) 2020-2021 Blylei Limited

Frabit is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with Frabit. If not, see http://www.gnu.org/licenses/.