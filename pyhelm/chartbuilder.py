import logging
import os
import yaml

from hapi.chart.template_pb2 import Template
from hapi.chart.chart_pb2 import Chart
from hapi.chart.metadata_pb2 import Metadata
from hapi.chart.config_pb2 import Config
from supermutes.dot import dotify

from .repo import RepoUtils 

LOG = logging.getLogger('pyhelm')


class ChartBuilder(object):
    '''
    This class handles taking chart intentions as a paramter and
    turning those into proper protoc helm charts that can be
    pushed to tiller.

    It also processes chart source declarations, fetching chart
    source from external resources where necessary
    '''

    def __init__(self, chart, parent=None):
        '''
        Initialize the ChartBuilder class

        Note that tthis will trigger a source pull as part of
        initialization as its necessary in order to examine
        the source service many of the calls on ChartBuilder
        '''

        # cache for generated protoc chart object
        self._helm_chart = None

        # record whether this is a dependency based chart
        self.parent = parent

        # store chart schema
        self.chart = dotify(chart)

        # extract, pull, whatever the chart from its source
        self.source_directory = self.source_clone()

    # 合并字典,将src的中的键值整合到dst中
    @staticmethod
    def coalesceTables(dst, src):
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

    # 根据path生成对应的字典结构结构:
    # example: server.port = 80 result: {"server":{"port": 80}}
    @staticmethod
    def pathtomap(path, data):
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

    # 生成对应的value参数
    @staticmethod
    def generate_values(valuesfile="", values={}):
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
        '''
        Clone the charts source

        We only support a git source type right now, which can also
        handle git:// local paths as well
        '''

        subpath = self.chart.source.get('subpath', '')

        if not 'type' in self.chart.source:
            LOG.exception("Need source type for chart %s",
                          self.chart.name)
            return

        if self.parent:
            LOG.info("Cloning %s/%s as dependency for %s",
                     self.chart.source.location,
                     subpath, self.parent)
        else:
            LOG.info("Cloning %s/%s for release %s",
                     self.chart.source.location,
                     subpath, self.chart.name)

        if self.chart.source.type == 'repo':
            self._source_tmp_dir = RepoUtils.from_repo(self.chart.source.location,
                                                  self.chart.name,
                                                  self.chart.version)
        elif self.chart.source.type == 'directory':
            self._source_tmp_dir = self.chart.source.location

        else:
            LOG.exception("Unknown source type %s for chart %s",
                          self.chart.name,
                          self.chart.source.type)
            return

        return os.path.join(self._source_tmp_dir, subpath)

    def source_cleanup(self):
        '''
        Cleanup source
        '''
        RepoUtils.source_cleanup(self._source_tmp_dir)

    def get_metadata(self):
        '''
        Process metadata
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
        Return (non-template) files in this chart

        TODO(alanmeadows): Not implemented
        '''
        return []

    def get_values(self):
        '''
        Return the chart (default) values
        '''

        # create config object representing unmarshaled values.yaml
        if os.path.exists(os.path.join(self.source_directory, 'values.yaml')):
            raw_values = open(os.path.join(self.source_directory,
                                           'values.yaml')).read()
        else:
            LOG.warn("No values.yaml in %s, using empty values",
                     self.source_directory)
            raw_values = ''

        return Config(raw=raw_values)

    def get_templates(self):
        '''
        Return all the chart templates
        '''

        # process all files in templates/ as a template to attach to the chart
        # building a Template object
        #import ipdb; ipdb.set_trace()
        templates = []
        if not os.path.exists(os.path.join(self.source_directory,
                                           'templates')):
            LOG.warn("Chart %s has no templates directory,"
                     "no templates will be deployed", self.chart.name)
        for root, _, files in os.walk(os.path.join(self.source_directory,
                                                   'templates'), topdown=True):
            for tpl_file in files:
                tname = os.path.relpath(os.path.join(root, tpl_file),
                                        os.path.join(self.source_directory,
                                                     'templates'))

                templates.append(Template(name=tname,
                                          data=open(os.path.join(root,
                                                                 tpl_file),
                                                    'rb').read()))
        return templates

    def get_dependencies(self):
        """
        Return chart dependencies
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

    def dump(self):
        '''
        This method is used to dump a chart object as a
        serialized string so that we can perform a diff

        It should recurse into dependencies
        '''
        return self.get_helm_chart().SerializeToString()
