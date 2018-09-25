#-*- coding:utf-8 -*-
"""
repo 包含repo处理的简单函数,包括返回chart版本列表
chart名称列表以及根据字符搜索chart等功能
"""
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
import os
import git
import requests
import shutil
import tarfile
import tempfile
import yaml

from utils.exceptions import CustomError

__all__ = ["RepoUtils", "repo_chart", "repo_search", "chart_versions", "repo_index", "from_repo", "git_clone", "source_cleanup"]


class RepoUtils(object):
    """Utils for repo control
    
    该类实现repo的基本分析操作.
    """

    @staticmethod
    def repo_chart(index_data):
        """return all item of chart

        return all item for index_data.

        Args:
            index_data: index.yaml的dict格式数据

        Returns:
            由chart名称所组成的list

        """
        return index_data["entries"].keys()

    @staticmethod
    def repo_search(index_data, search_string):
        """search chart name by keyword
         
        搜索包含search_string的chart,并返回列表
        Args:
            index_data: index.yaml的dict格式数据
            search_string: 搜索字符串 

        Returns:
            由chart名称所组成的list

        """
        search_result = []
        for item in index_data["entries"].keys():
            if item.find(search_string) != -1:
                search_result.append(item)
        return search_result

    @staticmethod
    def chart_versions(index_data, chart_name):
        """return chart all versions"
        返回chart_name的所有版本列表 
        
        Args:
            index_data: index.yaml的dict格式数据(dict)
            chart_name: chart_name(str) 

        Returns:
            由chart version所组成的list

        """
        chart_all_versions = index_data["entries"][chart_name]
        chart_version_list = [item["version"] for item in chart_all_versions]
        return chart_version_list

    @staticmethod
    def repo_index(repo_url, timeout=3):
        """Downloads the Chart's repo index
        
        返回repo_url的字典格式数据 
        
        Args:
            repo_url: repo的链接(str)
            timeout: 请求超时时间

        Returns:
            repo_url的字典数据
        """
        index_url = os.path.join(repo_url, 'index.yaml')
        index = requests.get(index_url, timeout=timeout)
        return yaml.safe_load(index.content)

    @staticmethod
    def from_repo(repo_url, chart, version=None, timeout=3):
        """Downloads the chart from a repo.

        返回下载并解压后的chart目录 
        
        Args:
            repo_url: repo的链接(str)
            chart: chart名称(str)
            version: chart版本(str)
            timeout: 请求超时时间(int)

        Returns:
            返回下载并解压后的chart目录 
        """
        _tmp_dir = tempfile.mkdtemp(prefix='pyhelm-', dir='/tmp')
        index = RepoUtils.repo_index(repo_url)

        if chart not in index['entries']:
            raise CustomError('Chart not found in repo')

        versions = index['entries'][chart]

        if version is not None:
            versions = filter(lambda k: k['version'] == version, versions)

        metadata = sorted(versions, key=lambda x: x['version'])[0]
        for url in metadata['urls']:
            req = requests.get(url, stream=True, timeout=timeout)
            fobj = StringIO(req.content)
            tar = tarfile.open(mode="r:*", fileobj=fobj)
            tar.extractall(_tmp_dir)
            return os.path.join(_tmp_dir, chart)

    @staticmethod
    def git_clone(repo_url, branch='master'):
        """clones repo to a /tmp/ dir

        git clone代码到/tmp
        Args:
            repo_url: repo链接 
            branch: 分支名称

        Returns:
            临时目录
        """

        _tmp_dir = tempfile.mkdtemp(prefix='pyhelm-', dir='/tmp')
        git.Repo.clone_from(url=repo_url, to_path=_tmp_dir, branch=branch)

        return _tmp_dir

    @staticmethod
    def source_cleanup(target_dir):
        """Clean up source.

        清理临时目录 
        
        Args:
            target_dir: 待清理的目录 

        Returns:
        """
        shutil.rmtree(os.path.split(target_dir)[0])

if __name__ == "__main__":

    import repo
    print(help(repo))
