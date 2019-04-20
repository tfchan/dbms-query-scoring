#!/usr/bin/python3
"""Tool for scoring query homework and exam."""
import os
import argparse


def directory(path):
    """Check input path if it is valid directory."""
    if path != '' and not os.path.isdir(path):
        msg = f"{path} isn't a valid directory"
        raise argparse.ArgumentTypeError(msg)
    return path


def all_dir():
    """Return list of unhidden directorys in working directory."""
    dirs = list(filter(os.path.isdir, os.listdir()))
    dirs = [dir_ for dir_ in dirs if not dir_.startswith('.')]
    return dirs


def main():
    """Perform main task."""
    parser = argparse.ArgumentParser(
        description='Query homework and exam scoring tool.')
    parser.add_argument('-b', '--batches', type=directory,
                        default=all_dir(), nargs='*',
                        help='Batch(directory) to score, default all batches')
    parser.add_argument('data', type=directory, default='data',
                        help='Dataset directory, default "data"')
    args = parser.parse_args()


if __name__ == '__main__':
    main()
