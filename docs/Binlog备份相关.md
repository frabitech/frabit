# binlog文件备份
运行在备份slave，通过调用mysqlbinlog去主库实时拉取binlog,实际运行的命令的结果与下列等效：
```bash
mysqlbinlog --raw --read-from-remote-server --stop-never --verify-binlog-checksum --user=${mysql_user} --
password=${mysql_password} --host=${source_mysql_host} --port=${source_mysql_port}  --stop-never-slave-server-id=
54060 $first_binlog_file 2>&1
```

