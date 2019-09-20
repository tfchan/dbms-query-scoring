"""Class file for mysql docker."""
import docker


class MysqlDocker:
    """Class for manipulating MySQL container."""

    _client = docker.from_env()

    def __init__(self, start=True):
        """Imitialize everything."""
        self._server = None
        self._root_pw = None
        if start:
            self.start_server()

    def start_server(self, version='5.7', name=None, root_pw='admin'):
        """Start mysql server container."""
        if self._server is None:
            hc = docker.types.healthcheck.Healthcheck(
                test=['CMD', 'mysqladmin', 'ping', '-h', 'localhost'])
            self._server = self._client.containers.run(
                f'mysql:{version}', detach=True, name=name,
                healthcheck=hc,
                environment=[f'MYSQL_ROOT_PASSWORD="{root_pw}"'])
            self._root_pw = root_pw
            return self._server.short_id
