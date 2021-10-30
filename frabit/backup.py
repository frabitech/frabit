# (c) 2020 Frabit Project maintained and limited by Blylei < blylei.info@gmail.com >
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# This file is part of Frabit
#
"""
This module represents a backup.
"""

import os
import sys
import time
import datetime
import re
import logging

from .utils import which
from .backup_executor import *

_logger = logging.getLogger(__name__)


class BackupManager:
    """
    实现对MySQL日常备份、恢复、归档任务的管理
    """
    def __init__(self):
        """执行初始化任务"""
        pass

    def backup(self):
        """ 执行备份任务"""
        pass

    def recover(self, backup_id, dest):
        """执行恢复任务"""
        pass

    def transfer(self, backup_id):
        """将备份集转移到异地机房的任务"""
        pass

    def get_available_backups(self, status_filter):
        """列出备份集"""
        pass

    def get_backup(self, backup_id):
        """从备份集获取指定的备份"""
        pass

    def get_previous_backup(self, backup_id):
        """从备份集里获取上一次备份"""
        pass

    def get_next_backup(self, backup_id):
        """从备份集里获取下一个备份"""
        pass

    def get_first_backup_id(self):
        """从备份集里获取第一个备份的ID"""
        pass

    def get_last_backup_id(self):
        """从备份集里获取最后一个备份的ID"""
        pass

    def get_last_binlog_info(self):
        """从备份集里获取最近的一个binlog文件信息"""
        pass

    def delete_backup(self, backup_id):
        """从备份集里删除指定的备份"""
        pass

    def archiver_binlog(self):
        """从指定主机归档binlog"""
        pass

    def purge_binlog(self):
        """从备份集里清除指定的binlog"""
        pass

    def check(self):
        """根据备份文件保留策略检查备份集的有效性"""
        pass

    def update_backup_strategy(self):
        """管理备份策略"""
        pass

    def server_status(self):
        """获取备份管理服务器的状态信息"""
        pass

    def remove_binlog_before_backup(self, backup_info):
        pass
