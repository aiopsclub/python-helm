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

class RepoUtils(object):

    @staticmethod
    def repo_chart(index_data):
        """return all item of chart"""
        return index_data["entries"].keys()
    
    @staticmethod
    def repo_search(index_data, search_string):
        """search chart name by keyword"""
        search_result = []
        for item in index_data["entries"].keys():
            if item.find(search_string) != -1:
                search_result.append(item)
        return search_result
    
    @staticmethod
    def chart_versions(index_data, chart_name):
        """return chart all versions"""
        chart_all_versions = index_data["entries"][chart_name]
        chart_version_list = [item["version"] for item in chart_all_versions]
        return chart_version_list
    
    
    @staticmethod
    def repo_index(repo_url, timeout=3):
        """Downloads the Chart's repo index"""
        index_url = os.path.join(repo_url, 'index.yaml')
        index = requests.get(index_url, timeout=timeout)
        return yaml.safe_load(index.content)
    
    @staticmethod
    def from_repo(repo_url, chart, version=None, timeout=3):
        """Downloads the chart from a repo."""
        _tmp_dir = tempfile.mkdtemp(prefix='pyhelm-', dir='/tmp')
        index = repo_index(repo_url)
    
        if chart not in index['entries']:
            raise RuntimeError('Chart not found in repo')
    
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
        """clones repo to a /tmp/ dir"""
    
        _tmp_dir = tempfile.mkdtemp(prefix='pyhelm-', dir='/tmp')
        git.Repo.clone_from(url=repo_url, to_path=_tmp_dir, branch=branch)
    
        return _tmp_dir
    
    @staticmethod
    def source_cleanup(target_dir):
        """Clean up source."""
        shutil.rmtree(os.path.split(target_dir)[0])
