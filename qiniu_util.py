import os
import time
from typing import List, Dict, Any

from qiniu import Auth, BucketManager, etag, put_file, put_data, CdnManager
from qiniu.services.cdn.manager import create_timestamp_anti_leech_url

from config import logging

default_access_key = '_QqOw3NH7uqTiKdUcYDQWNnseuD9b8Xcu4nRtbV6'
default_secret_key = 'FuzD9heFEHhZrMbMQl5mMUBhg4iDqTpLlWZ5wFc9'
default_encrypt_key = '3f8bfa9959abb28aa28931aa478a1a9a949b0e9b'
# default_bucket_name = 'xqshare'
# default_domain_name = 'wmymz.2bit.cn'
default_dead_time = 3600


class Qiniu(object):
    def __init__(self, access_key=default_access_key, secret_key=default_secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.auth_obj: Auth = Auth(self.access_key, self.secret_key)
        self.bucket_manager: BucketManager = BucketManager(self.auth_obj)
        buckets = self.bucket_manager.list_bucket('')[0]
        self.cdn_manager: CdnManager = CdnManager(self.auth_obj)
        if len(buckets) > 0:
            self.bucket_name = buckets[0].get('id')
        else:
            raise Exception('七牛云没有创建空间')
        self.domain: str = self.bucket_manager.bucket_domain(self.bucket_name)

    def is_exist(self, file_name: str) -> bool:
        """
        判断七牛云中是否存在特定文件
        :param file_name: 文件名
        :return: 存在则返回True，否则返回False
        """
        ret, _ = self.bucket_manager.stat(self.bucket_name, file_name)
        return ret is not None

    def get_file_list(self) -> List[Dict[str, Any]]:
        """
        查询七牛云中保存的文件列表
        :return: 文件信息的列表
        """
        ret, _, _ = self.bucket_manager.list(self.bucket_name)
        return ret['items']

    def upload_local_file(self, file_path: str, save_name=None, delete_after_days=None) -> None:
        """
        上传本地文件
        :param file_path: 本地文件的路径
        :param save_name: 保存在七牛云的文件名
        :param delete_after_days: 上传后自动删除的时间
        :return: None
        """
        if not save_name:
            save_name = file_path.split(os.sep)[-1]
        token = self.auth_obj.upload_token(self.bucket_name, save_name)
        ret, _ = put_file(token, save_name, file_path)
        logging.info('正在验证文件hash...')
        if ret['key'] == save_name and ret['hash'] == etag(file_path):
            logging.info('文件hash验证无误！')
        else:
            logging.info('文件上传过程中损坏')
        if delete_after_days:
            self.delete_file(save_name, delete_after_days)

    def upload_stream_file(self, file_stream, save_name=None, delete_after_days=None):
        """
        上传二进制文件流到七牛云
        :param file_stream:二进制文件流
        :param save_name:保存在七牛云的文件名
        :param delete_after_days:上传后自动删除的时间
        :return:
        """
        token = self.auth_obj.upload_token(self.bucket_name, save_name)
        put_data(token, save_name, file_stream)
        if delete_after_days:
            self.delete_file(save_name, delete_after_days)

    def fetch_url(self, url: str, save_name=None, delete_after_days=None) -> None:
        """
        抓取网络资源，可用于离线下载
        :param url: 网络资源url，可以是普通的下载地址
        :param save_name: 保存在七牛云的文件名
        :param delete_after_days: 离线下载后自动删除的时间
        :return: None
        """
        if not save_name:
            save_name = url.split('/')[-1].split('?')[0] or 'unknown'
        self.bucket_manager.fetch(url, self.bucket_name, save_name)
        if delete_after_days:
            self.delete_file(save_name, delete_after_days)

    def delete_file(self, file_name: str, delete_after_days=None):
        """
        删除七牛云文件
        :param file_name: 文件名称
        :param delete_after_days: 设置后会延迟删除
        :return:
        """
        if self.is_exist(file_name):
            if delete_after_days:
                self.bucket_manager.delete_after_days(self.bucket_name, file_name, delete_after_days)
            else:
                self.bucket_manager.delete(self.bucket_name, file_name)

    def get_download_link(self, file_name: str) -> str:
        return f'http://{self.domain}/{file_name}'

    def get_timestamp_link(self, file_name: str, dead_time=default_dead_time, encrypt_key=default_encrypt_key) -> str:
        deadline = int(time.time()) + dead_time
        link = create_timestamp_anti_leech_url(
            self.domain, file_name, None, encrypt_key, deadline)
        return f'http://{link}'

    def refresh(self, file_name: str) -> str:
        """
        刷新七牛云
        :param file_name:
        :return:
        """
        self.cdn_manager.refresh_urls([f'http://{self.domain}/{file_name}'])


if __name__ == '__main__':
    obj: Qiniu = Qiniu()
    obj.fetch_url('http://slproweb.com/download/Win64OpenSSL-1_1_1L.msi', 'test.msi')
    pass
