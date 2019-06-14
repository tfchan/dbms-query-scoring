"""Class file for mysql docker."""
import docker


class MysqlDocker:
    """Class for manipulating MySQL container."""

    _client = docker.from_env()

    def __init__(self):
        """Imitialize everything."""
