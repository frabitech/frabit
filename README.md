![logo](images/Frabit.png)

Frabit
=========================
![PyPI - License](https://img.shields.io/github/license/frabitech/frabit)
![size](https://img.shields.io/github/repo-size/frabitech/frabit)
![lang](https://img.shields.io/pypi/pyversions/frabit)
[![status](https://img.shields.io/pypi/status/frabit)](https://github.com/frabitech/frabit/releases)
[![downloads](https://img.shields.io/github/downloads/frabitech/frabit/total.svg)](https://github.com/frabitech/frabit/releases)
[![pypi](https://img.shields.io/pypi/v/frabit)](https://github.com/frabitech/frabit/releases)
[![Upload Python Package](https://github.com/frabitech/frabit/actions/workflows/python-publish.yml/badge.svg)](https://github.com/frabitech/frabit/actions/workflows/python-publish.yml)

# Frabit 一个专用于MySQL的备份管理工具

安装
-----------
- pip 安装
```bash
pip install frabit
或者
pip3 install frabit
```
- 源码编译安装
```bash
shell> git clone https://github.com/frabitech/frabit.git
shell> cd frabit
shell> python3 setup.py install

```

用途
-----------
根据备份场景，在策略配置文件中配置策略；添加需要备份的实例，即可自动完成备份、恢复、归档等需要DBA手动完成的任务。Frabit主要是调用第三方的工具来自动完成备份、巡检、恢复等任务。将策略与备份逻辑解耦，全程不需要额外编写脚本。目前计划实现的功能如下：
 
-   执行备份操作

     1 .  逻辑备份:根据备份策略，调用[mysqldump](https://dev.mysql.com/doc/refman/5.7/en/mysqldump.html) 进行备份    
     ```bash
       shell> frabit backup -c config.cnf 
     ```
     2 . 物理备份:根据备份策略，调用[XtraBackup](https://www.percona.com/doc/percona-xtrabackup/LATEST/index.html) 进行备份
    ```bash
    shell> frabit backup -c config.cnf 
    ```
     3 . binlog备份:根据备份策略，调用[mysqlbinlog](https://dev.mysql.com/doc/refman/5.7/en/mysqlbinlog.html) 从对应的主库实时转储binlog
    ```bash
    shell> frabit binlog -c config.cnf 
    ```
  
-   备份恢复演练
    
    1 不管是物理备份，还是逻辑备份，只需要运行下面的命令，就能将数据恢复到专用于恢复的机器上
    ```bash
    shell> frabit restore backup_id -c config.cnf
    ```
    不管是物理备份，还是逻辑备份，只需要运行下面的命令，就能将数据恢复到专用于恢复的机器上
    ```bash
    shell> frabit restore backup_id -c config.cnf
    ```

-  备份检查
    
    1 . 列出备份集
    
     在备份实例上，执行以下命令，列出当前实例的备份集
     ```bash
    shell> frabit list-backups 
    ```
    2 . 检查备份状态

     在备份实例上，执行以下命令，检查指定备份是否成功
     ```bash
    shell> frabit check-backup backup_id 
    ```
   
文档
--------
[简体中文](docs/zh/README.md)

[English manual](docs/en/README.md)

## LICENSE 

Copyright (C) 2020-2021 Blylei Limited

Frabit is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with Frabit. If not, see http://www.gnu.org/licenses/.