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
        register(('lncn.org', get_str_config('DNS', 'lncn', '162.159.211.93')))
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
    return json.loads(response3.text)


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
    if not hasattr(get_ssr_list, 'date') or get_ssr_list.date != lncn_data['date']:
        # 需要更新缓存
        # plaintext = aes_decrypt(key=base64.b64decode(lncn_data['code'] + '===').decode(), ciphertext=lncn_data['ssrs'])
        # 2022年2月28号修改，lncn网站算法更新，key放在了ssrs中，code参数已取消
        ciphertext, key = lncn_data['ssrs'].split('2022')
        plaintext = aes_decrypt(key=key, ciphertext=ciphertext)
        plaintext_json = json.loads(plaintext)
        get_ssr_list.date = lncn_data['date']
        get_ssr_list.data = [i['url'] for i in plaintext_json]
    return get_ssr_list.date, get_ssr_list.data


@async_exec
def update_qiniu(ssr_list: List[str]) -> None:
    """
    更新七牛云上面的节点
    http://slproweb.com/download/Win64OpenSSL-1_1_1L.exe
    :param ssr_list: ssr节点列表
    :return: None
    """
    if not hasattr(update_qiniu, 'qiniu_obj'):
        ak = get_str_config('QINIU', 'ak', '')
        sk = get_str_config('QINIU', 'sk', '')
        if ak and sk:
            update_qiniu.qiniu_obj = Qiniu(ak, sk)
        else:
            update_qiniu.qiniu_obj = Qiniu()
    update_qiniu.qiniu_obj.upload_stream_file(base64.urlsafe_b64encode('\n'.join(ssr_list).encode()), 'node.txt')
    pass


if __name__ == '__main__':
    date, ssr_list = get_ssr_list()
    logging.info('爬取ssr节点')
    if ssr_list:
        logging.info(f'爬取到源站节点，源站更新时间为：{date}')
        logging.info('更新七牛云订阅内容')
        update_qiniu(ssr_list)
    else:
        logging.info(f'爬取源站数据失败')
