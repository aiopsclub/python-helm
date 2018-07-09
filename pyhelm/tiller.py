import grpc
import yaml
import logging

from hapi.services.tiller_pb2 import ReleaseServiceStub, ListReleasesRequest, \
    InstallReleaseRequest, UpdateReleaseRequest, UninstallReleaseRequest, \
    GetReleaseContentRequest, GetReleaseStatusRequest, GetVersionRequest, \
    RollbackReleaseRequest, GetHistoryRequest, TestReleaseRequest
from hapi.chart.chart_pb2 import Chart
from hapi.chart.config_pb2 import Config

LOG = logging.getLogger('pyhelm')
TILLER_PORT = 44134
TILLER_VERSION = b'2.9.1'
TILLER_TIMEOUT = 300
REQUEST_TIMEOUT = 5
RELEASE_LIMIT = 0
MAX_HISTORY = 64


class Tiller(object):
    '''
    The Tiller class supports communication and requests to the Tiller Helm
    service over gRPC
    '''

    def __init__(self, host, port=44134, ssl_verification=False,
                 root_certificates=None, cert_key=None,
                 cert_cert=None, ssl_target_name_override='tiller-server'):
        """注意ssl_target_name_override参数,必须和tiller端证书的common name一致,否则会提示无法链接
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
        Return tiller metadata for requests
        '''
        return [(b'x-helm-api-client', TILLER_VERSION)]

    def get_channel(self):
        '''
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
            return grpc.secure_channel(self._host + ":" + self._port, creds, options=(('grpc.ssl_target_name_override', self.ssl_target_name_override,),))
        else:
            return grpc.insecure_channel('%s:%s' % (self._host, self._port))

    def tiller_status(self):
        '''
        return if tiller exist or not
        '''
        if self._host:
            return True

        return False

    def get_release_content(self, name):
        """
        Release content
        """
        stub = ReleaseServiceStub(self.channel)
        req = GetReleaseContentRequest(name=name)
        release_content = stub.GetReleaseContent(req, self.timeout,
                                                 metadata=self.metadata)
        return release_content

    def get_release_status(self, name):
        stub = ReleaseServiceStub(self.channel)
        req = GetReleaseStatusRequest(name=name)
        release_status = stub.GetReleaseStatus(req, self.timeout,
                                                metadata=self.metadata)
        return release_status

    def list_releases(self, limit=RELEASE_LIMIT, status_codes=[], namespace=None):
        '''
        :params limit - number of result 
        :params status_codes - status_codes list used for filter
        :params namespace(srt) - k8s namespace 
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

        Returns list of (name, version, chart, values)
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

    def _pre_update_actions(self, actions, namespace):
        '''
        :params actions - array of items actions
        :params namespace - name of pod for actions
        '''
        try:
            for action in actions.get('delete', []):
                name = action.get("name")
                action_type = action.get("type")
                if "job" in action_type:
                    LOG.info("Deleting %s in namespace: %s", name, namespace)
                    self.k8s.delete_job_action(name, namespace)
                    continue
                LOG.error("Unable to execute name: %s type: %s ", name, type)
        except Exception:
            LOG.debug("PRE: Could not delete anything, please check yaml")

        try:
            for action in actions.get('create', []):
                name = action.get("name")
                action_type = action.get("type")
                if "job" in action_type:
                    LOG.info("Creating %s in namespace: %s", name, namespace)
                    self.k8s.create_job_action(name, action_type)
                    continue
        except Exception:
            LOG.debug("PRE: Could not create anything, please check yaml")

    def _post_update_actions(self, actions, namespace):
        try:
            for action in actions.get('create', []):
                name = action.get("name")
                action_type = action.get("type")
                if "job" in action_type:
                    LOG.info("Creating %s in namespace: %s", name, namespace)
                    self.k8s.create_job_action(name, action_type)
                    continue
        except Exception:
            LOG.debug("POST: Could not create anything, please check yaml")

    def update_release(self, chart, dry_run=False, name=None,
                       disable_hooks=False, values=None, recreate=False,
                       reset_values=False, reuse_values=False, force=False,
                       timeout=REQUEST_TIMEOUT):
        '''
        Update a Helm Release
        '''

        #values = Config(raw=yaml.safe_dump(values or {}))
        #self._pre_update_actions(pre_actions, namespace)

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

        #self._post_update_actions(post_actions, namespace)

    def install_release(self, chart, namespace, disable_hooks=False,
                        reuse_name=False, disable_crd_hook=False,
                        timeout=REQUEST_TIMEOUT, dry_run=False,
                        name=None, values=None):
        """
        Create a Helm Release
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
        """
        :params - name - release name
        :params - version - release version
        :params - dry_run - simulate a rollback
        :params - disable_hooks - prevent hooks from running during rollback
        :params - recreate - performs pods restart for the resource if applicable
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
        """
        :params - name(string) - release name
        :params - max(int) - max items of release history
        usage: ReleaseHistory retrieves a releasse's history
        """
        # build get history request
        stub = ReleaseServiceStub(self.channel)
        get_history_request = GetHistoryRequest(name=name,
                                                max=max)
        return stub.GetHistory(get_history_request,
                               self.timeout,
                               metadata=self.metadata)

    def test_release(self, name, cleanup=False, timeout=REQUEST_TIMEOUT):
        """
        :params - name(string) - release name
        :params - cleanup(bool) - delete test pods upon completion
        usage: RunReleaseTest executes the tests defined of a named release
        """
        # build  ReleaseTest request
        stub = ReleaseServiceStub(self.channel)
        test_release_request = TestReleaseRequest(name=name,
                                                  cleanup=cleanup)
        return stub.RunReleaseTest(test_release_request,
                                   self.timeout,
                                   metadata=self.metadata)

    def uninstall_release(self, release, timeout=REQUEST_TIMEOUT,
                          disable_hooks=False, purge=True):
        """
        :params - release - helm chart release name
        :params - purge - deep delete of chart

        deletes a helm chart from tiller
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
        """
        GetVersion returns the current version of the server
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
