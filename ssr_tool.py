import base64
import json
import os
#import re
from typing import List, Tuple

from Crypto.Cipher import AES
from requests.packages.urllib3 import disable_warnings

from async_util import async_exec
from cache_util import cache
from config import *
from dns_util import activate, register
from qiniu_util import Qiniu
from request_util import requests_obj

disable_warnings()


def bytes2str(bs: bytes) -> str:
    return base64.b64encode(bs).decode() if isinstance(bs, bytes) else bs


def str2bytes(s: str) -> bytes:
    return base64.b64decode(s + len(s) % 4 * '=') if isinstance(s, str) else s


def spider_lncn():
    if os.environ.get('LNCN', ''):
        register(('lncn.org', os.environ['LNCN']))
        logging.info(os.environ['LNCN'])
    else:
        register(('lncn.org', get_str_config('DNS', 'lncn', '104.16.58.66')))
    activate()
    # response1 = requests.get('https://lncn.org/api/ssrList')
    # return json.loads(response1.text)
    # lncn更新了，api接口被禁，只能通过解析页面得到订阅地址
    # response2 = requests.get('https://lncn.org')
    # return {
    #     'date': re.compile('(?<=date:")[^"]*').findall(response2.text)[0],
    #     'code': re.compile('(?<=code:")[^"]*').findall(response2.text)[0],
    #     'ssrs': re.compile('(?<=ssrs:")[^"]*').findall(response2.text)[0].encode('u8').decode("unicode_escape"),
    # }
    response3 = requests_obj.get('https://lncn.org/api/ssr-list')
    try:
        return json.loads(response3.text)
    except Exception as e:
        logging.error(response3.text)
        raise Exception('请求被cf拦截了')


@cache()
def aes_decrypt(key: str, ciphertext: str) -> str:
    """
    ase解密，使用了第三方网站提供的服务
    :param key:
    :param ciphertext:
    :return: 解密后的明文字符串
    """
    aes = AES.new(str2bytes(key), AES.MODE_ECB)
    plaintext = aes.decrypt(str2bytes(ciphertext))
    return plaintext[:-plaintext[-1]].decode()


def get_ssr_list() -> Tuple[str, list]:
    """
    获取ssr节点地址列表
    :return: ssr节点地址列表
    """
    lncn_data = spider_lncn()
    # 2023.9 api响应变更成了明文
    return [i['shareLink'] for i in lncn_data]


#@async_exec
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
    sub_file = 'nodes/lncn.txt'
    update_qiniu.qiniu_obj.upload_stream_file(base64.urlsafe_b64encode('\n'.join(ssr_list).encode()), sub_file)
    logging.info('七牛云上传成功')
    update_qiniu.qiniu_obj.refresh(sub_file)
    logging.info('CDN刷新成功')
    pass


if __name__ == '__main__':
    ssr_list = get_ssr_list()
    logging.info('爬取ssr节点')
    if ssr_list:
        logging.info(f'爬取到源站节点')
        logging.info('更新七牛云订阅内容')
        update_qiniu(ssr_list)
    else:
        logging.info(f'爬取源站数据失败')
