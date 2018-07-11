============
python-helm
============

python client for  helm.
该项目主要依赖于官方的hapi的grpc接口

Helm gRPC
---------

The helm gRPC libraries are located in the hapi directory.  They were generated with the grpc_tools.protoc utility against Helm 2.9.10.  Should you wish to re-generate them you can easily do so::

    git clone https://github.com/kubernetes/helm ./helm
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/chart/*
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/services/*
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/release/*
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/version/*



How to use
-----------------

1. First you need repo_url and chart name to download chart::

    from pyhelm.repo import RepoUtils 

    chart_path = from_repo('https://kubernetes-charts.storage.googleapis.com/', 'mariadb')

    print(chart_path)
    "/tmp/pyhelm-kibwtj8d/mongodb"


2. Next step to build ChartBuilder instance to manipulate with Tiller::

    from pyhelm.chartbuilder import ChartBuilder

    chart = ChartBuilder({'name': 'mongodb', 'source': {'type': 'directory', 'location': '/tmp/pyhelm-kibwtj8d/mongodb'}})

    # than we can get chart meta data etc
    In [9]: chart.get_metadata()
    Out[9]:
    name: "mongodb"
    version: "0.4.0"
    description: "Chart for MongoDB"


3. Install chart::

    from pyhelm.chartbuilder import ChartBuilder
    from pyhelm.tiller import Tiller
    # 构建chart元数据
    chart = ChartBuilder({'name': 'mongodb', 'source': {'type': 'directory', 'location': '/tmp/pyhelm-kibwtj8d/mongodb'}})

    # 生成tiller连接实例
    tiller_ins = Tiller(tiller_host, tiller_port)

    # 安装 release
    tiller_ins.install_release(chart.get_helm_chart(), dry_run=False, namespace='default')

    # 列出 release 
    tiller_ins.list_releases(limit=RELEASE_LIMIT, status_codes=[], namespace=None)

    # 删除 release
    tiller_ins.uninstall_release(release_name)

    # 获得 release 版本历史 
    tiller_ins.get_history(name, max=MAX_HISTORY)

    # 回滚 release 
    tiller_ins.rollback_release(name, version, timeout=REQUEST_TIMEOUT)
