#!/usr/bin/python3
"""Tool for scoring query homework and exam."""
import os
import argparse
import subprocess


def directory(path):
    """Check input path if it is a directory."""
    if not os.path.exists(path) or not os.path.isdir(path):
        msg = f"{path} does not exist or isn't a a directory"
        raise argparse.ArgumentTypeError(msg)
    return path


def all_dir():
    """Return list of unhidden directorys in working directory."""
    dirs = list(filter(os.path.isdir, os.listdir()))
    dirs = [dir_ for dir_ in dirs if not dir_.startswith('.')]
    return dirs


def sql_file(path):
    """Check input path if it is a sql file."""
    if (not os.path.exists(path) or not os.path.isfile(path)
            or not path.endswith('.sql')):
        msg = f"{path} does not exist or isn't a sql file"
        raise argparse.ArgumentTypeError(msg)
    return path


def start_server(path):
    """Start MySQL server."""
    print('Starting MySQL server...')
    if not os.path.exists(path):
        msg = f'{path} does not exist'
        raise Exception(msg)
    ret = subprocess.run(path)
    if ret.returncode != 0:
        print('Fail to start MySQL server')
        exit(1)
    print('Start complete')


def main():
    """Perform main task."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Query homework and exam scoring tool.')
    parser.add_argument('-s', '--students', type=str, default='students.csv',
                        help='Student ID or csv file containing all IDs')
    parser.add_argument('-b', '--batches', type=directory,
                        default=all_dir(), nargs='*',
                        help='Batch(directory) to score, default all batches')
    parser.add_argument('-d', '--data', type=directory, default='data',
                        help='Dataset directory, default "data"')
    parser.add_argument('--db_sql', type=sql_file,
                        help='Sql file for creating and using database')
    parser.add_argument('--tb_sql', type=sql_file,
                        help='Sql file for creating and table')
    parser.add_argument('--import_sql', type=sql_file,
                        help='Sql file for importing data')
    args = parser.parse_args()

    # Start MySQL server
    start_server('./start_mysql_server.sh')


if __name__ == '__main__':
    main()
