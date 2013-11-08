#! /usr/bin/env python

import sys, os, subprocess

def clear_cache():
    clear_os_cache()

def clear_os_cache():
    subprocess.call(["sync"])
    subprocess.call(["clearcache"])
