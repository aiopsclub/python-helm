======
PyHelm
======

Python bindings for the Helm package manager

Helm gRPC
---------

The helm gRPC libraries are located in the hapi directory.  They were generated with the grpc_tools.protoc utility against Helm 2.9.3.  Should you wish to re-generate them you can easily do so::

    git clone https://github.com/kubernetes/helm ./helm
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/chart/*
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/services/*
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/release/*
    python -m grpc_tools.protoc -I helm/_proto --python_out=. --grpc_python_out=. _proto/hapi/version/*



How to use Pyhelm
-----------------

Looks like Pyhelm support only install chart from local folder

1. First you need repo_url and chart name to download chart::

    from pyhelm.repo import from_repo

    chart_path = chart_versions = from_repo('https://kubernetes-charts.storage.googleapis.com/', 'mariadb')

    print(chart_path)
    "/tmp/pyhelm-kibwtj8d/mongodb"


2. Now you can see that chart folder of mongodb::

    In [3]: ls -la /tmp/pyhelm-kibwtj8d/mongodb
    total 40
    drwxr-xr-x  7 andrii  wheel   224 Mar 21 17:26 ./
    drwx------  3 andrii  wheel    96 Mar 21 17:26 ../
    -rwxr-xr-x  1 andrii  wheel     5 Jan  1  1970 .helmignore*
    -rwxr-xr-x  1 andrii  wheel   261 Jan  1  1970 Chart.yaml*
    -rwxr-xr-x  1 andrii  wheel  4394 Jan  1  1970 README.md*
    drwxr-xr-x  8 andrii  wheel   256 Mar 21 17:26 templates/



3. Next step to build ChartBuilder instance to manipulate with Tiller::

    from pyhelm.chartbuilder import ChartBuilder

    chart = ChartBuilder({'name': 'mongodb', 'source': {'type': 'directory', 'location': '/tmp/pyhelm-kibwtj8d/mongodb'}})

    # than we can get chart meta data etc
    In [9]: chart.get_metadata()
    Out[9]:
    name: "mongodb"
    version: "0.4.0"
    description: "Chart for MongoDB"


4. Install chart::

    from pyhelm.chartbuilder import ChartBuilder
    from pyhelm.tiller import Tiller

    chart = ChartBuilder({'name': 'mongodb', 'source': {'type': 'directory', 'location': '/tmp/pyhelm-kibwtj8d/mongodb'}})
    t.install_release(chart.get_helm_chart(), dry_run=False, namespace='default')

    Out[9]:
    release {
      name: "fallacious-bronco"
      info {
        status {
          code: 6
        }
        first_deployed {
          seconds: 1521647335
          nanos: 746785000
        }
        last_deployed {
          seconds: 1521647335
          nanos: 746785000
        }
        Description: "Dry run complete"
      }
      chart {....
    }
