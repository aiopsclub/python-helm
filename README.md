## Welcome to python-helm ###

**python-helm** is a helm client for python.

1. [功能介绍](#功能)
2. [Tiller控制列表](#Tiller控制)  
3. [grpc接口生成](#该项目主要依赖于官方的hapi的grpc接口)   
4. [使用方法](#How-to-use-it)  
## 功能 ##

**python-helm** 可以实现对Tiller的访问

**Tiller控制**  
--
- 安装  
- 升级  
- 回滚  
- 删除  
- 测试 
- 获取版本历史 

**该项目主要依赖于官方的hapi的grpc接口** 
--
helm grpc 生成方式：  

The helm gRPC libraries are located in the hapi directory.  
They were generated with the grpc_tools.protoc utility against Helm 2.9.1.   
Should you wish to re-generate them you can easily do so:  

grpc python协议文件生成  

\# git clone https://github.com/kubernetes/helm ./helm  
\# python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. ./helm/_proto/hapi/chart/*  
\# python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. ./helm/_proto/hapi/services/*  
\# python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. ./helm/_proto/hapi/release/*  
\# python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. ./helm/_proto/hapi/version/*  

完成后，将在当前目录下生成hapi目录，这就是我们需要的grpc协议文件  

\# ls ./hapi
\# total 0   
\# drwxr-xr-x 2 root root 200 Jul 9 16:47 chart  
\# drwxr-xr-x 2 root root 294 Jul 9 16:47 release  
\# drwxr-xr-x 2 root root 53 Jul 9 16:47 rudder  
\# drwxr-xr-x 2 root root 53 Jul 9 16:47 services  
\# drwxr-xr-x 2 root root 55 Jul 9 16:47 version  

**How to use it** 
--
1. First you need repo_url and chart name to download chart:  
   \# from pyhelm.repo import RepoUtils  
   \# chart_path = from_repo('https://kubernetes-charts.storage.googleapis.com/', 'mariadb')  
   \# print(chart_path)  
   \# "/tmp/pyhelm-kibwtj8d/mongodb"  

2. Next step to build ChartBuilder instance to manipulate with Tiller.  
   \# from pyhelm.chartbuilder import ChartBuilder  
   \# chart = ChartBuilder({'name': 'mongodb', 'source': {'type': 'directory', 'location': '/tmp/pyhelm-kibwtj8d/mongodb'}})   
 
3. Control tiller  
   \# from pyhelm.chartbuilder import ChartBuilder  
   \# from pyhelm.tiller import Tiller  
   \# 构建chart元数据  
   \# chart = ChartBuilder({'name': 'mongodb', 'source': {'type': 'directory', 'location': '/tmp/pyhelm-kibwtj8d/mongodb'}})  
   \# 生成tiller连接实例  
   \# tiller_ins = Tiller(tiller_host, tiller_port)  
   \# 安装 release  
   \# tiller_ins.install_release(chart.get_helm_chart(), dry_run=False, namespace='default')  
   \# 列出 release  
   \# tiller_ins.list_releases(limit=RELEASE_LIMIT, status_codes=[], namespace=None)  
   \# 删除 release  
   \# tiller_ins.uninstall_release(release_name)  
   \# 获得 release 版本历史  
   \# tiller_ins.get_history(name, max=MAX_HISTORY)  
   \# 回滚 release  
   \# tiller_ins.rollback_release(name, version, timeout=REQUEST_TIMEOUT)
