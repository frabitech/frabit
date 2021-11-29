Frabit version v2.0.1-dev
=========================
![PyPI - License](https://img.shields.io/pypi/l/Barman)
[![downloads](https://img.shields.io/github/downloads/blylei/frabit/total.svg)](https://github.com/blylei/frabit/releases) 
[![release](https://img.shields.io/github/v/release/blylei/frabit.svg)](https://github.com/blylei/frabit/releases)


# Frabit 集成了mysqldump、mysqlbinlog、xtrabackup等开源工具来完成MySQL的日常备份、恢复任务
# 工具简介
只需要根据备份场景，在策略配置文件中配置策略；添加需要备份的实例，即可自动完成备份、恢复、归档等需要DBA手动完成的任务。Frabit主要是调用第三方的工具来自动完成备份、巡检、恢复等任务。将策略与备份逻辑解耦，全程不需要额外编写脚本。目前计划实现的功能如下：
 -  执行备份操作
     
     1 . 逻辑备份:根据备份策略，调用[mysqldump](https://dev.mysql.com/doc/refman/5.7/en/mysqldump.html)进行备份     
     
     2 . 物理备份:根据备份策略，调用[XtraBackup](https://www.percona.com/doc/percona-xtrabackup/LATEST/index.html)进行备份
     
     3 . binlog备份:根据备份策略，调用[mysqlbinlog](https://dev.mysql.com/doc/refman/5.7/en/mysqlbinlog.html)从对应的主库实时转储binlog

  
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


[Sqitch] is a database change management application. It currently supports
PostgreSQL 8.4+, SQLite 3.7.11+, MySQL 5.0+, Oracle 10g+, Firebird 2.0+, Vertica
6.0+, Exasol 6.0+ and Snowflake.

What makes it different from your typical migration approaches? A few things:

*   No opinions

    Sqitch is not tied to any framework, ORM, or platform. Rather, it is a
    standalone change management system with no opinions about your database
    engine, application framework, or development environment.

*   Native scripting

    Changes are implemented as scripts native to your selected database engine.
    Writing a [PostgreSQL] application? Write SQL scripts for [`psql`]. Writing
    an [Oracle]-backed app? Write SQL scripts for [SQL\*Plus].

*   Dependency resolution

    Database changes may declare dependencies on other changes -- even on
    changes from other Sqitch projects. This ensures proper order of
    execution, even when you've committed changes to your VCS out-of-order.

*   Deployment integrity

    Sqitch manages changes and dependencies via a plan file, and employs a
    [Merkle tree] pattern similar to [Git][gitmerkle] and [Blockchain] to ensure
    deployment integrity. As such, there is no need to number your changes,
    although you can if you want. Sqitch doesn't much care how you name your
    changes.

*   Iterative Development

    Up until you [tag] and [release] your project, you can modify your change
    deployment scripts as often as you like. They're not locked in just because
    they've been committed to your VCS. This allows you to take an iterative
    approach to developing your database schema. Or, better, you can do
    test-driven database development.

Want to learn more? The best place to start is in the tutorials:


*   [Introduction to Frabit on MySQL](lib/sqitchtutorial-mysql.pod)


To install Sqitch on a specific platform, including Debian- and RedHat-derived
Linux distributions and Windows, see the [Installation documentation].

  [CPAN]:      https://img.shields.io/cpan/v/App-Sqitch?label=%F0%9F%93%9A%20CPAN
  [📚]:        https://metacpan.org/dist/App-Sqitch "Latest version on CPAN"
  [OSes]:      https://github.com/sqitchers/sqitch/actions/workflows/os.yml/badge.svg
  [💿]:        https://github.com/sqitchers/sqitch/actions/workflows/os.yml "Tested on Linux, macOS, and Windows"
  [Exasol]:    https://github.com/sqitchers/sqitch/actions/workflows/exasol.yml/badge.svg
  [☀️]:         https://github.com/sqitchers/sqitch/actions/workflows/exasol.yml "Tested with Exasol 7.0–7.1"
  [Oracle]:    https://github.com/sqitchers/sqitch/actions/workflows/oracle.yml/badge.svg
  [🔮]:        https://github.com/sqitchers/sqitch/actions/workflows/oracle.yml "Tested with Oracle 11, 18, and 21"
  [Docker]:    https://img.shields.io/docker/v/sqitch/sqitch?label=%F0%9F%90%B3%20Docker&sort=semver
  [🐳]:        https://hub.docker.com/r/sqitch/sqitch "Latest version on Docker Hub"
  [Perl]:      https://github.com/sqitchers/sqitch/actions/workflows/perl.yml/badge.svg
  [🧅]:        https://github.com/sqitchers/sqitch/actions/workflows/perl.yml "Tested with Perl 5.12–5.34"
  [Firebird]:  https://github.com/sqitchers/sqitch/actions/workflows/firebird.yml/badge.svg
  [🔥]:        https://github.com/sqitchers/sqitch/actions/workflows/firebird.yml "Tested with Firebird 2.5, 3, and 4"
  [Snowflake]: https://github.com/sqitchers/sqitch/actions/workflows/snowflake.yml/badge.svg
  [❄️]:         https://github.com/sqitchers/sqitch/actions/workflows/snowflake.yml "Tested with Snowflake"
  [Homebrew]:  https://img.shields.io/github/v/tag/sqitchers/homebrew-sqitch?label=%F0%9F%8D%BA%20Homebrew&sort=semver
  [🍺]:        https://github.com/sqitchers/homebrew-sqitch#readme "Latest Homebrew Tap version"
  [Coverage]:  https://img.shields.io/coveralls/github/sqitchers/sqitch?label=%F0%9F%93%88%20Coverage
  [📈]:        https://coveralls.io/r/sqitchers/sqitch "Test Coverage"
  [MySQL]:     https://github.com/sqitchers/sqitch/actions/workflows/mysql.yml/badge.svg
  [🐬]:        https://github.com/sqitchers/sqitch/actions/workflows/mysql.yml "Tested with MySQL 5.5–8 and MariaDB 10.0–10.6"
  [SQLite]:    https://github.com/sqitchers/sqitch/actions/workflows/sqlite.yml/badge.svg
  [💡]:        https://github.com/sqitchers/sqitch/actions/workflows/sqlite.yml "Tested with SQLite 3.7–3.36"
  [Debian]:    https://img.shields.io/debian/v/sqitch?label=%F0%9F%8D%A5%20Debian
  [🍥]:        https://packages.debian.org/stable/sqitch "Latest version on Debian"
  [Postgres]:  https://github.com/sqitchers/sqitch/actions/workflows/pg.yml/badge.svg
  [🐘]:        https://github.com/sqitchers/sqitch/actions/workflows/pg.yml "Tested with PostgreSQL 9.3–14"
  [Vertica]:   https://github.com/sqitchers/sqitch/actions/workflows/vertica.yml/badge.svg
  [🔺]:        https://github.com/sqitchers/sqitch/actions/workflows/vertica.yml "Tested with Vertica 7.1–11.0"

  [Sqitch]: https://sqitch.org/
  [PostgreSQL]: https://postgresql.org/
  [`psql`]: https://www.postgresql.org/docs/current/static/app-psql.html
  [Oracle]: https://www.oracle.com/database/
  [SQL\*Plus]: https://www.orafaq.com/wiki/SQL*Plus
  [Merkle tree]: https://en.wikipedia.org/wiki/Merkle_tree "Wikipedia: “Merkle tree”"
  [gitmerkle]: https://stackoverflow.com/a/18589734/
    "Stack Overflow: “What is the mathematical structure that represents a Git repo”"
  [Blockchain]: https://medium.com/byzantine-studio/blockchain-fundamentals-what-is-a-merkle-tree-d44c529391d7
    "Medium: “Blockchain Fundamentals #1: What is a Merkle Tree?”"
  [tag]: https://sqitch.org/docs/manual/sqitch-tag/
  [release]: https://sqitch.org/docs/manual/sqitch-tag/
  [PDX.pm Presentation]: https://speakerdeck.com/theory/sane-database-change-management-with-sqitch
  [PDXPUG Presentation]: https://vimeo.com/50104469
  [Agile Database Development]: https://speakerdeck.com/theory/agile-database-development-2ed
  [Git]: https://git-scm.org
  [pgTAP]: https://pgtap.org
  [Dist::Zilla]: https://metacpan.org/module/Dist::Zilla
  [Installation documentation]: https://sqitch.org/download/
