# -*- coding:utf-8 -*-
""" Tiller class 注意包含对tiller的控制函数"""

import grpc
import logging
import sys
import os
sys.path.insert(0, os.path.split(os.path.abspath(os.path.dirname(__file__)))[0])

from hapi.services.tiller_pb2 import ReleaseServiceStub, ListReleasesRequest, \
    InstallReleaseRequest, UpdateReleaseRequest, UninstallReleaseRequest, \
    GetReleaseContentRequest, GetReleaseStatusRequest, GetVersionRequest, \
    RollbackReleaseRequest, GetHistoryRequest, TestReleaseRequest

LOG = logging.getLogger('pyhelm')
TILLER_PORT = 44134
TILLER_VERSION = b'2.9.1'
TILLER_TIMEOUT = 300
REQUEST_TIMEOUT = 5
RELEASE_LIMIT = 0
MAX_HISTORY = 64

__all__ = ["Tiller", "metadata", "get_channel", "tiller_status", "get_release_content",
           "get_release_status", "list_releases", "list_charts", "update_release",
           "install_release", "rollback_release", "get_history", "test_release",
           "uninstall_release", "get_version", "chart_cleanup"]
class Tiller(object):
    '''
    Tiller class 通过grpc协议与tiller进行交流.
    '''

    def __init__(self, host, port=44134, ssl_verification=False,
                 root_certificates=None, cert_key=None,
                 cert_cert=None, ssl_target_name_override='tiller-server'):
        """Tiller Class 构造函数
        Args:
            host: Tiller host(str)
            port: Tiller port(int)
            ssl_verification: 是否开启加密模式(bool) default(False)
            root_certificates: 根证书路径(str)
            cert_key: 客户端key
            cert_cert: 客户端证书
            ssl_target_name_override: 必须和tiller端证书的common name一致
        Returns:
            无返回值
        注意ssl_target_name_override参数,必须和tiller端证书的common name一致,否则会提示无法链接
        """
        # init k8s connectivity
        self._host = host
        self._port = str(port)
        self.ssl_verification = ssl_verification
        self.root_certificates = root_certificates
        self.cert_key = cert_key
        self.cert_cert = cert_cert
        self.ssl_target_name_override = ssl_target_name_override

        # init tiller channel
        self.channel = self.get_channel()

        # init timeout for all requests
        # and assume eventually this will
        # be fed at runtime as an override
        self.timeout = TILLER_TIMEOUT

    @property
    def metadata(self):
        '''
        Args:
            无参数
        Returns:
            Return tiller metadata for requests

        注意:TILLER_VERSION必须与实际版本一致
        '''
        return [(b'x-helm-api-client', TILLER_VERSION)]

    def get_channel(self):
        '''
        Args:
            无参数
        Return:
            Return a tiller channel
        '''
        if self.ssl_verification:
            cert_key_file = None
            cert_cert_file = None
            with open(self.root_certificates, 'rb') as f:
                ca_cert_file = f.read()
            if self.cert_key is not None:
                with open(self.cert_key, 'rb') as f:
                    cert_key_file = f.read()
            if self.cert_cert is not None:
                with open(self.cert_cert, 'rb') as f:
                    cert_cert_file = f.read()
            creds = grpc.ssl_channel_credentials(ca_cert_file, cert_key_file, cert_cert_file)
            return grpc.secure_channel(self._host + ":" + self._port, creds, 
                                       options=(('grpc.ssl_target_name_override',
                                       self.ssl_target_name_override,),))
        else:
            return grpc.insecure_channel('%s:%s' % (self._host, self._port))

    def tiller_status(self):
        '''判断__init__中host参数是否已经配置.
        Args:
            无参数
        Returns:
            return if tiller exist or not(bool)
        '''
        if self._host:
            return True

        return False

    def get_release_content(self, name):
        """获得具体release的内容
        Args:
            name: release名称
        Returns:
            Release content
        """
        stub = ReleaseServiceStub(self.channel)
        req = GetReleaseContentRequest(name=name)
        release_content = stub.GetReleaseContent(req, self.timeout,
                                                 metadata=self.metadata)
        return release_content

    def get_release_status(self, name):
        """获得具体release的状态
        Args:
            name: release名称
        Returns:
            Release状态
        """

        stub = ReleaseServiceStub(self.channel)
        req = GetReleaseStatusRequest(name=name)
        release_status = stub.GetReleaseStatus(req, self.timeout,
                                                metadata=self.metadata)
        return release_status

    def list_releases(self, limit=RELEASE_LIMIT, status_codes=[], namespace=None):
        '''获得release列表
        Argss:
            :params limit - number of result
            :params status_codes - status_codes list used for filter
                可选值(UNKNOWN, DEPLOYED, DELETED, SUPERSEDED, FAILED,
                       DELETING, PENDING_INSTALL, PENDING_UPGRADE,
                       PENDING_ROLLBACK)
            :params namespace(srt) - k8s namespace
        Returns:
            List Helm Releases
        '''
        releases = []
        stub = ReleaseServiceStub(self.channel)
        req = ListReleasesRequest(limit=limit, status_codes=status_codes, namespace=namespace or '')
        release_list = stub.ListReleases(req, self.timeout,
                                         metadata=self.metadata)
        for y in release_list:
            releases.extend(y.releases)
        return releases

    def list_charts(self):
        '''
        List Helm Charts from Latest Releases
        Args:
            无参数
        Return:
            list of (name, version, chart, values)
        '''
        charts = []
        for latest_release in self.list_releases():
            try:
                charts.append((latest_release.name, latest_release.version,
                               latest_release.chart,
                               latest_release.config.raw))
            except IndexError:
                continue
        return charts

    def update_release(self, chart, name, dry_run=False,
                       disable_hooks=False, values=None, recreate=False,
                       reset_values=False, reuse_values=False, force=False,
                       timeout=REQUEST_TIMEOUT):
        """升级release
        Args:
            :params - chart - chart 元数据,由函数生成
            :params - name - release name
            :params - dry_run - simulate an upgrade
            :params - values - 额外的values,用来进行value值替换
            :params - disable_hooks - prevent hooks from running during rollback(bool)
            :params - recreate - performs pods restart for the resource if applicable(bool)
            :params - reset_values - when upgrading, reset the values to the ones built into the chart(bool)
            :params - reuse_values - when upgrading, reuse the last release's values and merge in any overrides from the command line via --set and -f. If '--reset-values' is specified, this is ignored.(bool)
            :params - force - 是否强制升级(bool)
        Returns:
            返回升级release的grpc响应对象
        """

        #values = Config(raw=yaml.safe_dump(values or {}))

        # build update release request
        stub = ReleaseServiceStub(self.channel)
        release_request = UpdateReleaseRequest(
            chart=chart,
            dry_run=dry_run,
            recreate=recreate,
            reset_values=reset_values,
            reuse_values=reuse_values,
            force=force,
            disable_hooks=disable_hooks,
            values=values,
            timeout=timeout,
            name=name)

        return stub.UpdateRelease(release_request, self.timeout,
                                  metadata=self.metadata)

    def install_release(self, chart, namespace, disable_hooks=False,
                        reuse_name=False, disable_crd_hook=False,
                        timeout=REQUEST_TIMEOUT, dry_run=False,
                        name=None, values=None):
        """安装release
        Args:
            :params - chart - chart 元数据,由函数生成
            :params - name - release name,为空时随机生成
            :params - namespace - kubernetes namespace 
            :params - dry_run - simulate an install 
            :params - values - 额外的values,用来进行value值替换
            :params - disable_hooks - prevent hooks from running during install(bool)
            :params - disable_crd_hook - prevent CRD hooks from running, but run other hooks(bool) 
            :params - reuse_name - re-use the given name, even if that name is already used. This is unsafe in production(bool) 
            :params - timeout - time in seconds to wait for any individual Kubernetes operation (like Jobs for hooks) (default 300) 
        Returns:
            返回安装release的grpc响应对象
        """

        #values = Config(raw=yaml.safe_dump(values or {}))

        # build release install request
        stub = ReleaseServiceStub(self.channel)
        release_request = InstallReleaseRequest(
            chart=chart,
            disable_hooks=disable_hooks,
            reuse_name=reuse_name,
            disable_crd_hook=disable_crd_hook,
            dry_run=dry_run,
            timeout=timeout,
            values=values,
            name=name or '',
            namespace=namespace)
        return stub.InstallRelease(release_request,
                                   self.timeout,
                                   metadata=self.metadata)

    def rollback_release(self, name, version, timeout=REQUEST_TIMEOUT,
                         dry_run=False, disable_hooks=False,
                         recreate=False, wait=False, force=False):
        """回滚release
        Args:
            :params - name - release nam
            :params - version - release version
            :params - dry_run - simulate a rollback
            :params - disable_hooks - prevent hooks from running during rollback
            :params - recreate - performs pods restart for the resource if applicable
        Returns:
            返回回滚release的grpc响应对象
        """
        # build rollback release request
        stub = ReleaseServiceStub(self.channel)
        rollback_release_request = RollbackReleaseRequest(
            name=name,
            timeout=timeout,
            version=version,
            dry_run=dry_run,
            disable_hooks=disable_hooks,
            recreate=recreate,
            wait=wait,
            force=force)
        return stub.RollbackRelease(rollback_release_request,
                                    self.timeout,
                                    metadata=self.metadata)

    def get_history(self, name, max=MAX_HISTORY):
        """usage: ReleaseHistory retrieves a releasse's history
        Args:
            :params - name(string) - release name
            :params - max(int) - max items of release history
        Return:
            返回版本的历史的grpc响应对象

        """
        # build get history request
        stub = ReleaseServiceStub(self.channel)
        get_history_request = GetHistoryRequest(name=name,
                                                max=max)
        return stub.GetHistory(get_history_request,
                               self.timeout,
                               metadata=self.metadata)

    def test_release(self, name, cleanup=False, timeout=REQUEST_TIMEOUT):
        """usage: RunReleaseTest executes the tests defined of a named release
        Args:
            :params - name(string) - release name
            :params - cleanup(bool) - delete test pods upon completion
        Returns:
            返回测试安装的grpc响应对象
        """
        # build  releaseTest request
        stub = ReleaseServiceStub(self.channel)
        test_release_request = TestReleaseRequest(name=name,
                                                  cleanup=cleanup)
        return stub.RunReleaseTest(test_release_request,
                                   self.timeout,
                                   metadata=self.metadata)

    def uninstall_release(self, release, timeout=REQUEST_TIMEOUT,
                          disable_hooks=False, purge=False):
        """deletes a helm chart from tiller
        Args:
            :params - release - helm chart release name
            :params - purge - deep delete of chart
        Returns:
            返回卸载release的grpc响应对象
        """

        # build release install request
        stub = ReleaseServiceStub(self.channel)
        release_request = UninstallReleaseRequest(name=release,
                                                  timeout=timeout,
                                                  disable_hooks=disable_hooks,
                                                  purge=purge)
        return stub.UninstallRelease(release_request,
                                     self.timeout,
                                     metadata=self.metadata)

    def get_version(self):
        """GetVersion returns the current version of the server
        Args:
        
        Returns:
            返回tiller的版本grpc响应对象
        """
        # build get version request
        stub = ReleaseServiceStub(self.channel)
        get_version_request = GetVersionRequest()
        return stub.GetVersion(get_version_request,
                               self.timeout,
                               metadata=self.metadata)

    def chart_cleanup(self, prefix, charts):
        """
        :params charts - list of yaml charts
        :params known_release - list of releases in tiller

        :result - will remove any chart that is not present in yaml
        """
        def release_prefix(prefix, chart):
            """
            how to attach prefix to chart
            """
            return "{}-{}".format(prefix, chart["chart"]["release_name"])

        valid_charts = [release_prefix(prefix, chart) for chart in charts]
        actual_charts = [x.name for x in self.list_releases()]
        chart_diff = list(set(actual_charts) - set(valid_charts))

        for chart in chart_diff:
            if chart.startswith(prefix):
                LOG.debug("Release: %s will be removed", chart)
                self.uninstall_release(chart)

if __name__ == "__main__":
    import tiller
    print(help(tiller))
