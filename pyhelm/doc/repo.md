#Help on module repo:

NAME
    repo

DESCRIPTION
    repo 包含repo处理的简单函数,包括返回chart版本列表
    chart名称列表以及根据字符搜索chart等功能

CLASSES
    builtins.object
        RepoUtils
    
    class RepoUtils(builtins.object)
     |  Utils for repo control
     |  
     |  该类实现repo的基本分析操作.
     |  
     |  Static methods defined here:
     |  
     |  chart_versions(index_data, chart_name)
     |      return chart all versions"
     |      返回chart_name的所有版本列表 
     |      
     |      Args:
     |          index_data: index.yaml的dict格式数据(dict)
     |          chart_name: chart_name(str) 
     |      
     |      Returns:
     |          由chart version所组成的list
     |  
     |  from_repo(repo_url, chart, version=None, timeout=3)
     |      Downloads the chart from a repo.
     |      
     |      返回下载并解压后的chart目录 
     |      
     |      Args:
     |          repo_url: repo的链接(str)
     |          chart: chart名称(str)
     |          version: chart版本(str)
     |          timeout: 请求超时时间(int)
     |      
     |      Returns:
     |          返回下载并解压后的chart目录
     |  
     |  git_clone(repo_url, branch='master')
     |      clones repo to a /tmp/ dir
     |      
     |      git clone代码到/tmp
     |      Args:
     |          repo_url: repo链接 
     |          branch: 分支名称
     |      
     |      Returns:
     |          临时目录
     |  
     |  repo_chart(index_data)
     |      return all item of chart
     |      
     |      return all item for index_data.
     |      
     |      Args:
     |          index_data: index.yaml的dict格式数据
     |      
     |      Returns:
     |          由chart名称所组成的list
     |  
     |  repo_index(repo_url, timeout=3)
     |      Downloads the Chart's repo index
     |      
     |      返回repo_url的字典格式数据 
     |      
     |      Args:
     |          repo_url: repo的链接(str)
     |          timeout: 请求超时时间
     |      
     |      Returns:
     |          repo_url的字典数据
     |  
     |  repo_search(index_data, search_string)
     |      search chart name by keyword
     |       
     |      搜索包含search_string的chart,并返回列表
     |      Args:
     |          index_data: index.yaml的dict格式数据
     |          search_string: 搜索字符串 
     |      
     |      Returns:
     |          由chart名称所组成的list
     |  
     |  source_cleanup(target_dir)
     |      Clean up source.
     |      
     |      清理临时目录 
     |      
     |      Args:
     |          target_dir: 待清理的目录 
     |      
     |      Returns:
     |  
     |  ----------------------------------------------------------------------
     |  Data descriptors defined here:
     |  
     |  __dict__
     |      dictionary for instance variables (if defined)
     |  
     |  __weakref__
     |      list of weak references to the object (if defined)

DATA
    __all__ = ['RepoUtils', 'repo_chart', 'repo_search', 'chart_versions',...

FILE
    /opt/python-helm/pyhelm/repo.py


None
