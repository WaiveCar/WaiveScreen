#!/usr/bin/env python3
import lib.db as db
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--action", choices=["add", "remove", "list"], help="What to do to the record")


def add(datatype, date, path):

