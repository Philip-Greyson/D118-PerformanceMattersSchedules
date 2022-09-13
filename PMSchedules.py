# Script to export all classes for students in the current term
# Data Export Manager in PS only lets you choose the entire year term,
# Which is an issue especially for HS students who have different periods per semester


# importing module
import oracledb
import sys
import datetime
import os
from datetime import *

un = 'PSNavigator' #PSNavigator is read only, PS is read/write
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD') #the password for the PSNavigator account
cs = os.environ.get('POWERSCHOOL_PROD_DB') #the IP address, port, and database name to connect to

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
badnames = ['USE', 'training1','trianing2','trianing3','trianing4','planning','admin','nurse','user', 'use ', 'payroll', 'human', "benefits", 'test', 'teststudent','test student','testtt','testtest']

with oracledb.connect(user=un, password=pw, dsn=cs) as con: # create the connecton to the database
    with con.cursor() as cur:  # start an entry cursor
        with open('pmschedules.txt', 'w') as outputfile:  # open the output file
            print("Connection established: " + con.version)
            print('SchoolID,Course Number,Section ID,Section Number,Expression,Student ID,Teacher Number,Teacher DCID', file=outputfile) #print header line in output file
            try:
                outputLog = open('schedule_log.txt', 'w') #open a second file for the log output

            except Exception as er:
                print('Unknown Error: '+str(er))
                print('Unknown Error: '+str(er), file=outputLog)
