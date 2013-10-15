DB_Builder.py

A program that builds a local copy of the hosted Prosper DB on google appengine
Since DB time costs on appengine, it is expected that collaborators debug on local resources before an Alpha test on the live data

SETUP:
tested with CYGWIN on a windows machine

	1) Download cygwin: http://cygwin.com/install.html
	2) Select cygwin packages
		- database: install all
		- python: install all
		- shells: bash recommended
	3) configure cygwin python to include mySQL module
		$>: easy_install mysql-python
	4) get mySQL host program: tested on mySQL Dashboard: http://dev.mysql.com/downloads/workbench/5.2.html
	5) initialize localhost database controller
	6) add database login credentials to config.ini
		-defaults-
		- root_dbname=eve_marketdata
		- db_IP=127.0.0.1 (IP suggested.  "localhost" doesn't resolve correctly)
		- db_username=root
		- db_pw=bar
		- db_port=3306
	7) update any defaults required in config.ini
	8) run DB_Builder.py in command line
		- Defaults:
		- startdate: 2011-11-29 (cruicible release)
		- enddate: today
	9) enjoy a shiney new market DB of all the data on the prosper service!
	