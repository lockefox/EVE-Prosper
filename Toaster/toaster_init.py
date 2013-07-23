#!/Python27/python.exe

import sys,csv, sys, math, os, gzip, getopt, subprocess, math, datetime, time
import ConfigParser
import urllib2
import MySQLdb
import threading,Queue

config_file = "config.ini"
config = ConfigParser.ConfigParser()
config.read(config_file)