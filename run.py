import requests
from subprocess import call
from lxml import etree
import os
import time
import re
import json
import yaml
from mytools import wash


def load_yaml(file):
    """
    读取 info.yaml 文件内容
    """
    with open(file, 'r', encoding='utf8') as f:
        res = yaml.load(f, Loader=yaml.FullLoader)

    return res

basic = load_yaml(os.getcwd() + '/info.yaml')

"""
{'target_url': 'https://litu100.xyz/comic/id-62121d751d8fe.html',
 'idm_engine': 'C:\\Program Files (x86)\\Internet Download Manager\\IDMan.exe',
 'headers': {'User_Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'},
 'picDownUrl_fmt': 'https://img2.xchina.fun/comics/{}/{}/{}.jpg'}
"""

root = basic['target_url']
idm = basic['idm_engine']
headers = basic['headers']
fmt = basic['picDownUrl_fmt']


def root_info(url=root):
    """获取root页面中的信息，包括漫画名、国家、作者、简介、章节名、章节数等"""
    res = requests.get(url, headers=headers)
    html = etree.HTML(res.text)

    fingerprint = re.search('id-(.*?)\.html', url).group(1)
    title = html.xpath('//div[@class="comic-info"]/div[@class="title"]/text()')[0]
    country = html.xpath('//div[@class="comic-info"]/div[@class="country"]/text()')[0]
    author = html.xpath('//div[@class="comic-info"]/div[@class="author"]/text()')[0]
    brief = html.xpath('//div[@class="comic-info"]/div[@class="status"][2]/text()')[0]
    chapterNames = html.xpath('//div[@class="chapters"]/a/div/text()')

    return {
        'fingerprint': fingerprint,
        'title': wash(title),
        'country': wash(country, mode='colon'),
        'author': wash(author, mode='colon'),
        'brief': wash(brief, mode='colon'),
        'chapterNames': [wash(i) for i in chapterNames],
        'chapterNum': len(chapterNames)
    }


def parse_chapter(infoDict, breaktime=3):
    url = root[:-5] + '/{}' + '.html'
    picNumLst = []
    for i in range(1, infoDict['chapterNum']+1):
        res = requests.get(url=url.format(i), headers=headers)
        imgs = etree.HTML(res.text).xpath('//div[@class="article comic"]/div/img')
        picNumLst.append(len(imgs))
        time.sleep(breaktime)

    return picNumLst


def write_url(dic):
    for chapter_index, (name, picNum) in enumerate(zip(dic['chapterNames'],dic['picNumLst']), 1):
        try:
            os.mkdir(f"Down/{bag['title']}/{name}")
        except FileExistsError:
            pass

        with open(f'Down/{bag["title"]}/{name}/urls.txt', 'w', encoding='utf8') as f:
            for i in range(1, picNum+1):
                f.write(fmt.format(dic['fingerprint'], chapter_index, str(i).zfill(basic['placeholder'])))
                f.write('\n')


if __name__ == '__main__':
    bag = root_info()
    bag['picNumLst'] = parse_chapter(bag)

    try:
        os.mkdir(f"Down/{bag['title']}")
        with open(f"Down/{bag['title']}/download_info.json", 'w', encoding='utf8') as f:
            json.dump(bag, f, ensure_ascii=False)
    except FileExistsError:
        raise FileExistsError('漫画已下载，请检查文件名')
    
    write_url(bag)

    for i in range(bag['chapterNum']):
        book = bag['chapterNames'][i]
        with open(f'Down/{bag["title"]}/{book}/urls.txt', 'r', encoding='utf8') as f:
            urls = f.read().splitlines()
            for index, url in enumerate(urls, 1):
                call([idm, '/d', url, '/p', os.path.abspath(f'Down/{bag["title"]}/{book}'), '/f', f'{index}.jpg', '/a'])
    call([idm, '/s'])
