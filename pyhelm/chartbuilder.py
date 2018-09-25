# -*- coding:utf-8 -*-
"""class ChartBuilder 主要功能是生成tiller所需的chart元数据"""

import logging
import os
import sys
sys.path.insert(0, os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])

import yaml
from supermutes.dot import dotify

from hapi.chart.chart_pb2 import Chart
from hapi.chart.config_pb2 import Config
from hapi.chart.metadata_pb2 import Metadata
from hapi.chart.template_pb2 import Template
from google.protobuf.any_pb2 import Any

from utils.exceptions import CustomError
from repo import RepoUtils

LOG = logging.getLogger('pyhelm')

__all__ = ["ChartBuilder", "coalesceTables", "pathtomap", "generate_values",
           "source_clone", "source_cleanup", "get_metadata", "get_files",
           "get_values", "get_templates", "get_dependencies", "get_helm_chart",
           "dump", "selectfile"]


class ChartBuilder(object):
    """
    This class handles taking chart intentions as a paramter and
    turning those into proper protoc helm charts that can be
    pushed to tiller.

    It also processes chart source declarations, fetching chart
    source from external resources where necessary
    """

    def __init__(self, chart):
        """
        构造函数,目的是生成tiller所需的chart数据
        Args:
            chart: chart的信息字典
        Return:
            无返回值
        注意chart的格式(dict):
            1. {'name': 'mongodb', 'source': {'type': 'directory', 'location': '/tmp/pyhelm-kibwtj8d/mongodb'}}
            2. {'name': 'mongodb', 'source': {'type': 'repo', 'version':'0.0.0', 'location': 'http://test.com/charts'}}
        使用第二种格式必须制定version(推荐使用2).

        """
        # cache for generated protoc chart object
        self._helm_chart = None

        # store chart schema
        self.chart = dotify(chart)

        # extract, pull, whatever the chart from its source
        self.source_directory = self.source_clone()

    def __str__(self):
        pass

    def __repr__(self):
        pass

    @staticmethod
    def coalesceTables(dst, src):
        """合并字典,将src的中的键值整合到dst中
        工具函数
        Args:
            dst: 目标字典
            src: 源字典

        ReturnS:
            合并后的字典
        """
        for key, val in src.items():
            if isinstance(val, dict):
                if key not in dst.keys():
                    dst[key] = val
                elif isinstance(dst[key], dict):
                    ChartBuilder.coalesceTables(dst[key], val)
                else:
                    continue
            else:
                if key not in dst.keys():
                    dst[key] = val
                elif isinstance(dst[key], dict):
                    continue
                elif isinstance(dst[key], (str, int, float)):
                    dst[key] = val
                else:
                    continue
        return dst

    @staticmethod
    def pathtomap(path, data):
        """根据path生成对应的字典结构结构
           example: server.port = 80 result: {"server":{"port": 80}}
        Args:
            path: server.port(str)
            data: 80
        Return:
            返回生成的字典
        """

        if path == ".":
            return data
        ap = path.split(".")
        if len(ap) == 0:
            return None
        n = []
        for item in ap:
            n.append({item: {}})
        i = 0
        for item in n:
            for k in item.keys():
                z = i + 1
                if z == len(n):
                    n[i][k] = data
                    break
                n[i][k] = n[z]
            i += 1
        return n[0]

    @staticmethod
    def generate_values(valuesfile="", values=None):
        """生成对应的value参数,以便在tiller升级和安装过程中替换值
        Args:
            valuesfile: yaml格式的数据(包括"\n")(str)
            valuesfile: 默认None,可接受的类型为dict

        Returns:
            返回tiller可接受的config对象
        """

        if values is None:
            values = {}
        if len(valuesfile):
            base_values = yaml.safe_load(valuesfile)
        else:
            base_values = {}
        for key, val in values.items():
            base_values = ChartBuilder.coalesceTables(base_values,
                                                      ChartBuilder.pathtomap(key, val))
        if len(base_values.keys()):
            return Config(raw=yaml.safe_dump(base_values,
                                             default_flow_style=False))
        else:
            return Config(raw="")

    def source_clone(self):
        '''Clone the charts source
        Args:
            无参数
        Returns:
            返回chart的文件所在目录
        '''

        if not 'type' in self.chart.source:
            raise CustomError(
                "Need source type for chart {}".format(self.chart.name))

        if self.chart.source.type == 'repo':
            self._source_tmp_dir = RepoUtils.from_repo(self.chart.source.location,
                                                       self.chart.name,
                                                       self.chart.version)
        elif self.chart.source.type == 'directory':
            self._source_tmp_dir = self.chart.source.location

        else:
            raise CustomError("Unknown source type {} for chart {}".format(
                self.chart.source.type, self.chart.name))

        return os.path.join(self._source_tmp_dir)

    def source_cleanup(self):
        '''Cleanup source

        清理临时的chart文件目录
        '''
        RepoUtils.source_cleanup(self._source_tmp_dir)

    def get_metadata(self):
        '''Process metadata
        获取chart的metadata数据
        Args:

        Returns:
            返回tiller所需的metadata对象
        '''
        # extract Chart.yaml to construct metadata
        chart_yaml = dotify(yaml.load(open(
            os.path.join(self.source_directory, 'Chart.yaml')).read()))

        # construct Metadata object
        return Metadata(
            description=chart_yaml.description,
            name=chart_yaml.name,
            version=chart_yaml.version
        )

    def get_files(self):
        '''
        根据官方的golang实现,未测试
        Args:
            无参数
        Returns:
            返回tiller所需的文件对象列表
        '''
        file_list = []
        for root, _, files in os.walk(self.source_directory, topdown=True):
            for tpl_file in files:
                relativepath = os.path.relpath(os.path.join(root, tpl_file), self.source_directory)
                if self.selectfile(relativepath):
                    file_list.append(Any(type_url=relativepath, value=bytes(open(os.path.join(root, tpl_file)).read(), encoding="utf-8")))

        return file_list

    def get_values(self):
        '''
        Return the chart (default) values
        获取chart的values数据
        Args:

        Returns:
            返回tiller所需的values对象
        '''

        # create config object representing unmarshaled values.yaml
        if os.path.exists(os.path.join(self.source_directory, 'values.yaml')):
            raw_values = open(os.path.join(self.source_directory,
                                           'values.yaml')).read()
        else:
            raw_values = ''

        return Config(raw=raw_values)

    def get_templates(self):
        '''
        Return all the chart templates
        获取chart的templates数据
        Args:

        Returns:
            返回tiller所需的templates对象
        '''
        # process all files in templates/ as a template to attach to the chart
        # building a Template object
        #import ipdb; ipdb.set_trace()
        templates = []
        if not os.path.exists(os.path.join(self.source_directory, 'templates')):
            pass
        for root, _, files in os.walk(os.path.join(self.source_directory,
                                                   'templates'), topdown=True):
            for tpl_file in files:
                tname = os.path.relpath(os.path.join(root, tpl_file), self.source_directory)

                templates.append(Template(name=tname,
                                          data=open(os.path.join(root,
                                                                 tpl_file),
                                                    'rb').read()))
        return templates

    def get_dependencies(self):
        """
        获取chart的dependecies数据
        Args:

        Returns:
            返回tiller所需的dependcies对象
        """
        dependencies = []
        if os.path.exists(os.path.join(self.source_directory, "requirements.yaml")):
            with open(os.path.join(self.source_directory, "requirements.yaml")) as fd:
                dependencies_info = yaml.safe_load(fd.read())
                if dependencies_info:
                    return [ChartBuilder({'name': item["name"],
                                          'version': item["version"],
                                          'source': {'type': 'repo',
                                                     'location': item["repository"]}}).get_helm_chart()
                            for item in dependencies_info["dependencies"]]

                else:
                    return dependencies

        else:
            return dependencies

    def get_helm_chart(self):
        '''
        Return a helm chart object
        获取tiller所需的chart数据
        Args:

        Returns:
            返回tiller所需的chart对象
        '''

        if self._helm_chart:
            return self._helm_chart

        helm_chart = Chart(
            metadata=self.get_metadata(),
            templates=self.get_templates(),
            dependencies=self.get_dependencies(),
            values=self.get_values(),
            files=self.get_files(),
        )

        self._helm_chart = helm_chart
        self.source_cleanup()
        return helm_chart

    def selectfile(self, filepath):

        if filepath == "Chart.yaml" or filepath == "values.yaml" or filepath =="values.toml" or filepath.startswith("templates/") or filepath.startswith("charts/"):
            return False
        else:
            return True

    def dump(self):
        '''
        序列化chart对象
        This method is used to dump a chart object as a
        serialized string so that we can perform a diff
        It should recurse into dependencies
        '''
        return self.get_helm_chart().SerializeToString()


if __name__ == "__main__":
    import chartbuilder
    print(help(chartbuilder))
