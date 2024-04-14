import base64
import os
import re
from typing import List

from config import *
import logging
from dns_util import activate, register
from qiniu_util import Qiniu
from request_util import requests_obj


def spider_lncn():
    if os.environ.get('LNCN', ''):
        register(('lncn.org', os.environ['LNCN']))
        logging.info(os.environ['LNCN'])
    else:
        register(('lncn.org', get_str_config('DNS', 'lncn', '104.16.58.66')))
    activate()
    try:
        # response = requests_obj.get('https://lncn.org/api/ssr-list')
        # return response.json()
        # lncn更新了，api接口返回的节点是旧的，只能通过解析页面得到订阅地址
        response = requests_obj.get('https://lncn.org')
        assert response.status_code == 200
        return re.compile('(?<=")ssr://[^"]*').findall(response.text)
    except Exception as e:
        logging.error(e)
        raise Exception('请求被cf拦截了')


def get_ssr_list() -> List[str]:
    """
    获取ssr节点地址列表
    :return: ssr节点地址列表
    """
    lncn_data = spider_lncn()
    # 2023.9 api响应变更成了明文
    return lncn_data


# @async_exec
def update_qiniu(ssr_list: List[str]) -> None:
    """
    更新七牛云上面的节点
    http://slproweb.com/download/Win64OpenSSL-1_1_1L.exe
    :param ssr_list: ssr节点列表
    :return: None
    """
    if not hasattr(update_qiniu, 'qiniu_obj'):
        ak = os.environ.get('QINIU_AK', '')
        sk = os.environ.get('QINIU_SK', '')
        if ak and sk:
            logging.info('ak: '+ak[:5]+'***')
            logging.info('sk: '+sk[:5]+'***')
            update_qiniu.qiniu_obj = Qiniu(ak, sk)
        else:
            update_qiniu.qiniu_obj = Qiniu()
    update_qiniu.qiniu_obj.upload_stream_file(base64.urlsafe_b64encode('\n'.join(ssr_list).encode()), 'nodes/lncn.txt')
    logging.info('七牛云上传成功')
    update_qiniu.qiniu_obj.refresh('nodes/lncn.txt')
    logging.info('CDN刷新成功')
    pass


if __name__ == '__main__':
    ssr_list = get_ssr_list()
    logging.info('爬取ssr节点')
    if ssr_list:
        logging.info('爬取到源站节点')
        logging.info('更新七牛云订阅内容')
        update_qiniu(ssr_list)
    else:
        logging.info('爬取源站数据失败')
