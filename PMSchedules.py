# Script to export all classes for students in the current term
# Data Export Manager in PS only lets you choose the entire year term,
# Which is an issue especially for HS students who have different periods per semester
# Lots of debug / error catching because I had a lot of issues and wanted to narrow down which sections threw errors

# See the following for table information
# https://docs.powerschool.com/PSDD/powerschool-tables/cc-4-ver3-6-1
# https://docs.powerschool.com/PSDD/powerschool-tables/terms-13-ver3-6-1

# importing module
import oracledb #used to connect to PowerSchool database
import sys
import datetime #used to get current date for course info
import os #needed to get environement variables
import pysftp #used to connect to the Performance Matters sftp site and upload the file
from datetime import *

un = 'PSNavigator' #PSNavigator is read only, PS is read/write
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD') #the password for the PSNavigator account
cs = os.environ.get('POWERSCHOOL_PROD_DB') #the IP address, port, and database name to connect to

#set up sftp login info, stored as environment variables on system
sftpUN = os.environ.get('PERFORMANCE_MATTERS_SFTP_USERNAME')
sftpPW = os.environ.get('PERFORMANCE_MATTERS_SFTP_PASSWORD')
sftpHOST = os.environ.get('PERFORMANCE_MATTERS_SFTP_ADDRESS')

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
print("SFTP Username: " + str(sftpUN) + " |SFTP Password: " + str(sftpPW) + " |SFTP Server: " + str(sftpHOST)) #debug so we can see where oracle is trying to connect to/with
badnames = ['USE', 'training1','trianing2','trianing3','trianing4','planning','admin','nurse','user', 'use ', 'payroll', 'human', "benefits", 'test', 'teststudent','test student','testtt','testtest']

with oracledb.connect(user=un, password=pw, dsn=cs) as con: # create the connecton to the database
    with con.cursor() as cur:  # start an entry cursor
        with open('pmschedules.txt', 'w') as outputfile:  # open the output file
            print("Connection established: " + con.version)
            print('SchoolID,Course Number,Section ID,Section Number,Expression,Student ID,Teacher Number,Teacher DCID', file=outputfile) #print header line in output file
            outputLog = open('schedule_log.txt', 'w') #open a second file for the log output
            try:
                print("Connection established: " + con.version, file=outputLog)
                cur.execute('SELECT student_number, first_name, last_name, id, schoolid, enroll_status, dcid FROM students ORDER BY student_number DESC')
                rows = cur.fetchall()  # fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
                today = datetime.now()  # get todays date and store it for finding the correct term later
                # today = datetime.now() + timedelta(days = 120) #testing purposes
                print("today = " + str(today))  # debug
                print("today = " + str(today), file=outputLog)  # debug

                for entrytuple in rows: #go through each entry (which is a tuple) in rows. Each entrytuple is a single student's data
                    try:
                        print(entrytuple, file=outputLog)  # debug
                        entry = list(entrytuple) #convert the tuple which is immutable to a list which we can edit. Now entry[] is an array/list of the student data
                        if not str(entry[1]) in badnames and not str(entry[2]) in badnames: #check first and last name against array of bad names, only print if both come back not in it
                            idNum = int(entry[0]) #what we would refer to as their "ID Number" aka 6 digit number starting with 22xxxx or 21xxxx
                            firstName = str(entry[1])
                            lastName = str(entry[2])
                            internalID = int(entry[3]) #get the internal id of the student that is referenced in the classes entries
                            schoolID = str(entry[4])
                            status = str(entry[5]) #active on 0 , inactive 1 or 2, 3 for graduated
                            stuDCID = str(entry[6])

                            if (status == "0"):  # only worry about the students who are active
                                #do another query to get their classes, filter to just the current term based on their school
                                try:
                                    cur.execute("SELECT id, firstday, lastday, schoolid, dcid FROM terms WHERE schoolid = " + schoolID + " ORDER BY dcid DESC")  # get a list of terms for the school, filtering to not full years
                                    terms = cur.fetchall()
                                    for termTuple in terms:  # go through every term
                                        # print(termTuple) #debug
                                        termEntry = list(termTuple)
                                        #compare todays date to the start and end dates with 2 days before start so it populates before the first day of the term
                                        if ((termEntry[1] - timedelta(days=2) < today) and (termEntry[2] + timedelta(days=1) > today)):
                                            termid = str(termEntry[0])
                                            termDCID = str(termEntry[4])
                                            # print("Found good term for student " + str(idNum) + ": " + termid + " | " + termDCID)
                                            print("Found good term for student " + str(idNum) + ": " + termid + " | " + termDCID, file=outputLog)
                                            # now for each term that is valid, do a query for all their courses and start processing them
                                            try:
                                                cur.execute("SELECT schoolid, course_number, sectionid, section_number, expression, teacherid FROM cc WHERE studentid = " + str(internalID) + " AND termid = " + termid + " ORDER BY course_number")
                                                userClasses = cur.fetchall()
                                                for tuples in userClasses:
                                                    classEntry = list(tuples)
                                                    print (classEntry, file=outputLog) # debug
                                                    # get the info for each course that we will want to print out
                                                    schoolID = str(classEntry[0])
                                                    courseNum = str(classEntry[1])
                                                    sectionID = str(classEntry[2])
                                                    sectionNum = str(classEntry[3])
                                                    expression = str(classEntry[4])
                                                    # get the teacher info so we can get/print out their info as well
                                                    teacherID = str(classEntry[5])
                                                    
                                                    cur.execute("SELECT users_dcid FROM schoolstaff WHERE id = " + teacherID) #get the user dcid from the teacherid in schoolstaff
                                                    schoolStaffInfo = cur.fetchall()
                                                    # print(schoolStaffInfo, file=outputLog) # debug
                                                    teacherDCID = str(schoolStaffInfo[0][0]) #just get the result directly without converting to list or doing loop

                                                    cur.execute("SELECT teachernumber, lastfirst FROM teachers WHERE users_dcid = " + teacherDCID) #get the teacher number from the teachers table for that user dcid
                                                    teacherInfo = cur.fetchall()
                                                    # print(teacherInfo, file=outputLog) # debug
                                                    teacherNum = str(teacherInfo[0][0]) #just get the result directly without converting to list or doing loop
                                                    teacherName = str(teacherInfo[0][1])

                                                    #print out all the info for the class entry
                                                    # print(schoolID + '\t' + courseNum + '\t' + sectionID + '\t' + sectionNum + '\t' + expression + '\t' + str(idNum) + '\t' + teacherNum + '\t' + teacherDCID + '\t' + teacherName, file=outputfile)
                                                    print(schoolID + '\t' + courseNum + '\t' + sectionID + '\t' + sectionNum + '\t' + expression + '\t' + str(idNum) + '\t' + teacherNum + '\t' + teacherDCID, file=outputfile)

                                            except Exception as err:
                                                print("Course error on " + str(idNum) + ": " + str(err))
                                                print("Course error on " + str(idNum) + ": " + str(err), file=outputLog)

                                except Exception as er:
                                    print('Term Error on ' + str(entrytuple[0]) + ': ' + str(er))
                                    print('Term Error on ' + str(entrytuple[0]) + ': ' + str(er), file=outputLog)            

                    except Exception as err:
                        print('Unknown Error on ' + str(entrytuple[0]) + ': ' + str(err))
                        print('Unknown Error on ' + str(entrytuple[0]) + ': ' + str(err), file=outputLog)

            except Exception as er:
                print('High Level Unknown Error: '+str(er))
                print('High Level Unknown Error: '+str(er), file=outputLog)

with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW) as sftp:
    print(sftp.listdir())  # debug
    #sftp.put('pmschedules.txt') #upload the file onto the sftp server
