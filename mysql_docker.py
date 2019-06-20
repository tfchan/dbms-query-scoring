"""Class file for mysql docker."""
import docker


class MysqlDocker:
    """Class for manipulating MySQL container."""

    _client = docker.from_env()

    def __init__(self):
        """Imitialize everything."""
        self._server = None

    def start_server(self):
        """Start mysql server container."""
        if self._server is None:
            self._server = self._client.containers.run(
                'mysql:5.7', detach=True, name='mysql-server',
                environment=['MYSQL_ROOT_PASSWORD="dbms"'])
