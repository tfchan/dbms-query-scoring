#!/usr/bin/python3
"""Tool for scoring query homework and exam."""
import os
import argparse
import subprocess
import filecmp
import signal
import pandas as pd
import tqdm
import numpy as np


_timeout = 120
_mysql_username = 'user'
_mysql_pw = 'user'
_db = 'exam'


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
    s = 'Start' if start else 'Stop'
    print(f'{s}ing MySQL server...')
    ret = subprocess.run(path, stdout=subprocess.DEVNULL,
                         stderr=subprocess.PIPE)
    if ret.returncode != 0:
        print(f'Fail to {s} MySQL server\n{ret.stderr.decode()}')
        exit(1)
    print(f'{s} success')


def sigalrm_handler(signum, frame):
    """Handle SIGALRM."""
    subprocess.run('docker stop client', stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, shell=True)


def run_query(sql_file, database=None, out_file=None, root=False):
    """Run the sql file."""
    if not os.path.isfile(sql_file):
        return 1

    # Generate docker command to run query
    mount_loc = '/data'
    sql_folder = os.path.dirname(os.path.abspath(sql_file))
    # Run mysql container, mount query folder, disable header
    cmd = ('docker run --name client --link some-mysql:mysql'
           f' -u `id -u` -v {sql_folder}:{mount_loc} --rm mysql:5.7'
           ' sh -c \'exec mysql -h"$MYSQL_PORT_3306_TCP_ADDR"'
           ' -P"$MYSQL_PORT_3306_TCP_PORT"')
    # Run with root or not
    if root:
        cmd += ' -uroot -p"$MYSQL_ENV_MYSQL_ROOT_PASSWORD"'
    else:
        cmd += f' -u{_mysql_username} -p"{_mysql_pw}"'
    # No header
    cmd += ' -N'
    # Specific database
    cmd += '' if database is None else f' {database}'
    # Redirect query in sql file to stdin of container
    cmd += f' < {os.path.join(mount_loc, os.path.basename(sql_file))}'
    # Redirect stdout of container to a file
    if not (out_file is None):
        cmd += f' > {os.path.join(mount_loc, os.path.basename(out_file))}'
    cmd += '\''
    try:
        signal.alarm(_timeout)
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=True,
                                universal_newlines=True)
    except UnicodeDecodeError:
        result = 2
    signal.alarm(0)
    return result


def qname2aname(q):
    """Convert question file name to answer file names."""
    a = q.replace('.sql', '.txt').replace('q', 'a')
    return a


def generate_query_results(folder, questions=None):
    """Run query file in folder and generate results."""
    if questions is None:
        questions = list(filter(
            lambda f: f.endswith('.sql'), os.listdir(folder)))
    results = {}
    for query_file in questions:
        out_file = qname2aname(query_file)
        query_path = os.path.join(folder, query_file)
        out_file = os.path.join(folder, out_file)
        ret = run_query(query_path, database=_db, out_file=out_file)
        if isinstance(ret, int):
            if ret == 2:
                err_str = 'Unicode decode error'
            else:
                err_str = 'No submission'
        else:
            if ret.returncode == 0:
                err_str = ''
            elif ret.returncode == 137:
                err_str = 'Timeout'
            else:
                with open(out_file, 'a') as f:
                    f.write(ret.stderr.splitlines()[1])
                err_str = 'Syntax error'
        results[query_file] = err_str
    return results


def cmp_results(ans_dir, student_dir, file_to_cmp):
    """Compare two directories for specific files."""
    same = []
    for f in file_to_cmp:
        ans_file = os.path.join(ans_dir, f)
        student_file = os.path.join(student_dir, f)
        try:
            # Check identical of files
            if filecmp.cmp(ans_file, student_file):
                same += [f]
            # Only check numeric columns when files aren't completely identical
            else:
                f1 = pd.read_csv(ans_file, sep='\t', header=None)
                f2 = pd.read_csv(student_file, sep='\t', header=None)
                if f1.shape != f2.shape or np.any(f1.dtypes != f2.dtypes):
                    continue
                all_same = True
                # Compare each column if they are close to each other
                for c in f1:
                    if (pd.api.types.is_numeric_dtype(f1[c])
                            and pd.api.types.is_numeric_dtype(f2[c])):
                        all_same = all_same and np.allclose(f1[c], f2[c])
                if all_same:
                    same += [f]
        except (pd.errors.EmptyDataError, FileNotFoundError):
            continue
    return same


def check_batch(ids, results, batch):
    """Check each student's result in this batch."""
    ans_folder = os.path.join(batch, 'answer')
    student_folders = list(filter(lambda d: d != ans_folder, list_dir(batch)))
    student_folders.sort()
    if not (ids is None):
        scoring_ids = set(map(lambda id: os.path.join(batch, id), ids))
        batch_ids = set(student_folders)
        if scoring_ids.isdisjoint(batch_ids):
            return
        else:
            student_folders = list(scoring_ids.intersection(batch_ids))
    ret = generate_query_results(ans_folder)
    success_q = list(filter(lambda k: ret[k] == '', ret.keys()))
    success_q.sort()
    print(f'Questions {success_q} will be checked')
    student_folders_tqdm = tqdm.tqdm(student_folders)
    for student_folder in student_folders_tqdm:
        student_folders_tqdm.set_description(f'Running {student_folder}')
        ret = generate_query_results(student_folder, success_q)
        file_to_cmp = [qname2aname(q) for q in success_q]
        same = cmp_results(ans_folder, student_folder, file_to_cmp)
        student_id = int(os.path.basename(student_folder))
        for q in success_q:
            if qname2aname(q) in same and ret[q] == '':
                results.loc[student_id, q] = 'V'
            else:
                results.loc[student_id, q] = 'X' if ret[q] == '' else ret[q]


def main():
    """Perform main task."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Query homework and exam scoring tool.')
    parser.add_argument('-i', '--id', type=str, nargs='*',
                        help='Student ID of submission to be scored')
    parser.add_argument('-r', '--results', type=str, default='results.csv',
                        help='Result file, update if already exist')
    parser.add_argument('-b', '--batches', type=directory,
                        default=list_dir(), nargs='*',
                        help='Batch(directory) to score, default all batches')
    parser.add_argument('-d', '--data', type=directory, default='data',
                        help='Folder containing dataset and setup script')
    args = parser.parse_args()

    results = pd.read_csv(args.results).set_index('id')
    results = results.sort_index()

    # Start MySQL server
    mysql_server('./start_mysql_server.sh')

    # Setup database and tables
    print('Setting up...')
    setup_sql = os.path.join(args.data, 'setup.sql')
    run_query(setup_sql, root=True)

    # Check answer in each batch
    signal.signal(signal.SIGALRM, sigalrm_handler)
    batches = list(filter(lambda d: d != args.data, args.batches))
    batches.sort()
    for i, batch in enumerate(batches):
        print(f'Running batch [{batch}], {i + 1} of {len(batches)}')
        check_batch(args.id, results, batch)
    results.to_csv(args.results)

    # Clean up MySQL server
    mysql_server('./cleanup_mysql_server.sh', start=False)


if __name__ == '__main__':
    main()
