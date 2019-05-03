#!/usr/bin/python3
"""Tool for scoring query homework and exam."""
import os
import argparse
import subprocess


def directory(path):
    """Check input path if it is a directory."""
    if not os.path.isdir(path):
        msg = f"{path} does not exist or isn't a a directory"
        raise argparse.ArgumentTypeError(msg)
    return path


def list_dir(path=None):
    """Return list of unhidden directorys in given/current directory."""
    if path is None:
        dirs = os.listdir()
    else:
        dirs = map(lambda d: os.path.join(path, d), os.listdir(path))
    dirs = filter(os.path.isdir, dirs)
    dirs = filter(lambda d: not d.startswith('.'), dirs)
    return list(dirs)


def mysql_server(path, start=True):
    """Start or stop MySQL server."""
    if not os.path.exists(path):
        msg = f'{path} does not exist'
        raise Exception(msg)
    s = 'start' if start else 'stop'
    print(f'{s}ing MySQL server...')
    ret = subprocess.run(path, stdout=subprocess.DEVNULL,
                         stderr=subprocess.PIPE)
    if ret.returncode != 0:
        print(f'Fail to {s} MySQL server\n{ret.stderr.decode()}')
        exit(1)
    print(f'{s} success')


def run_query(sql_file, database='', out_file=''):
    """Run the sql file."""
    if not os.path.isfile(sql_file):
        msg = f'{sql_file} does not exist'
        raise Exception(msg)

    mount_loc = '/data'
    sql_folder = os.path.dirname(os.path.abspath(sql_file))
    cmd = ('docker run --link some-mysql:mysql'
           f' -v {sql_folder}:{mount_loc} --rm mysql:5.7'
           ' sh -c \'exec mysql -h"$MYSQL_PORT_3306_TCP_ADDR"'
           ' -P"$MYSQL_PORT_3306_TCP_PORT"'
           ' -uroot -p"$MYSQL_ENV_MYSQL_ROOT_PASSWORD"'
           f' -N {database}'
           f' < {os.path.join(mount_loc, os.path.basename(sql_file))}\'')
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True,
                            universal_newlines=True)


def check_batch(batch):
    """Check each student's result in this batch."""
    ans_folder = os.path.join(batch, 'answer')
    student_folders = list(filter(lambda d: d != ans_folder, list_dir(batch)))


def main():
    """Perform main task."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Query homework and exam scoring tool.')
    parser.add_argument('-s', '--students', type=str, default='students.csv',
                        help='Student ID or csv file containing all IDs')
    parser.add_argument('-b', '--batches', type=directory,
                        default=list_dir(), nargs='*',
                        help='Batch(directory) to score, default all batches')
    parser.add_argument('-d', '--data', type=directory, default='data',
                        help='Folder containing dataset and setup script')
    args = parser.parse_args()

    # Start MySQL server
    mysql_server('./start_mysql_server.sh')

    # Setup database and tables
    setup_sql = os.path.join(args.data, 'setup.sql')
    run_query(setup_sql)

    # Check answer in each batch
    batches = filter(lambda d: d != args.data, args.batches)
    for batch in batches:
        check_batch(batch)

    # Clean up MySQL server
    mysql_server('./cleanup_mysql_server.sh', start=False)


if __name__ == '__main__':
    main()
