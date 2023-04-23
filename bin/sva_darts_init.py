#!/usr/bin/env python

import getopt
import re
import sys

import libsvadarts as sva

from pprint import pprint


def main(argv):
    parameters = {
    }

    try:
        opts, args = getopt.getopt(
            argv, "hsp:v:",
            [
                "help"])
    except getopt.GetoptError as err:
        print(err)
        usage()

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()

    # pprint(parameters)

    sva.init_clean_db()
    sva.load_all_data_into_db()


def usage():
    print('''read_file.py 
        

        ''')
    sys.exit()


if __name__ == "__main__":
    main(sys.argv[1:])
