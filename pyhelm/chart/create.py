# -*- coding: utf-8 -*-
import os
import tempfile

from pyhelm.utils.const import DEFAULT_CHART
from pyhelm.utils.const import CHART_DEFAULT_VALUE
from pyhelm.utils.const import TEMPLATE_FILENAME_MAP
from pyhelm.utils.const import CHART_FILENAME_MAP
from pyhelm.utils.exceptions import CustomError


class CreateChart(object):
    """Create default chart.

    like `helm create <chart_name>`
    """
    _tmp_dir = tempfile.mkdtemp(prefix='pyhelm-', dir='/tmp')

    @classmethod
    def create_chart(cls, chart_name):
        chart_path = os.path.join(cls._tmp_dir, chart_name)
        print(chart_path)
        if os.path.exists(chart_path) and os.path.isfile(chart_path):
            raise CustomError("Chart path `%s` already exists or path is not a directory" % chart_path)

        chart_path = cls._mkdir_chart_directory(cls._tmp_dir, chart_name)
        cls._mkdir_chart_directory(chart_path, "charts")
        template_path = cls._mkdir_chart_directory(chart_path, "templates")
        cls._save_chart_template_to_file(chart_path, chart_name=chart_name, is_chart=True)
        cls._save_chart_template_to_file(template_path)

    @classmethod
    def _mkdir_chart_directory(cls, chart_path, name, mode=0755):
        """Create directory to save chart template.

        :param chart_path: the path of the chart
        :param name: the name of the chart
        :param mode: the file mode of the chart
        :return:
        """
        path = os.path.join(chart_path, name)
        if not os.path.exists(path):
            try:
                os.makedirs(path, mode=mode)
                return path
            except OSError as e:
                raise CustomError("Create directory failed, %s" % e)
        return path


    @classmethod
    def _save_chart_template_to_file(cls, base_path, chart_name=None, is_chart=False):
        """Save chart template to file

        :param base_path:
        :param chart_name: if is_chart == True, chart_name need
        :param is_chart:
        :return:
        """
        if is_chart:
            chart_yaml = DEFAULT_CHART.format(name=chart_name,
                                              version=CHART_DEFAULT_VALUE['version'],
                                              apiversion=CHART_DEFAULT_VALUE['apiversion'],
                                              appversion=CHART_DEFAULT_VALUE['appversion'],
                                              description=CHART_DEFAULT_VALUE['description'])
            chart_yaml_path = os.path.join(base_path, 'Chart.yaml')
            with open(chart_yaml_path, 'wb') as f:
                f.write(chart_yaml)

            for name, template in CHART_FILENAME_MAP.items():
                name_path = os.path.join(base_path, name)
                with open(name_path, 'wb') as f:
                    f.write(template)
        else:
            for name, template in TEMPLATE_FILENAME_MAP.items():
                name_path = os.path.join(base_path, name)
                with open(name_path, 'wb') as f:
                    f.write(template)



if __name__ == '__main__':
    chart = CreateChart.create_chart('hello')
    print(chart)
