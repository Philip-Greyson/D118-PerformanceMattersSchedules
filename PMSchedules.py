# Script to export all classes for students in the current term
# Data Export Manager in PS only lets you choose the entire year term,
# Which is an issue especially for HS students who have different periods per semester
# Lots of debug / error catching because I had a lot of issues and wanted to narrow down which sections threw errors

# See the following for table information
# https://ps.powerschool-docs.com/pssis-data-dictionary/latest/cc-4-ver3-6-1
# https://ps.powerschool-docs.com/pssis-data-dictionary/latest/terms-13-ver3-6-1

# needs oracledb: pip install oracledb --upgrade
# needs pysftp: pip install pysftp --upgrade

# importing module
import oracledb # used to connect to PowerSchool database
import datetime # used to get current date for course info
import os # needed to get environement variables
import pysftp # used to connect to the Performance Matters sftp site and upload the file
from datetime import *

un = os.environ.get('POWERSCHOOL_READ_USER') # username for read-only database user
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD') # the password for the database account
cs = os.environ.get('POWERSCHOOL_PROD_DB') # the IP address, port, and database name to connect to

# set up sftp login info, stored as environment variables on system
sftpUN = os.environ.get('PERFORMANCE_MATTERS_SFTP_USERNAME') # the username provided by PM to log into their SFTP server
sftpPW = os.environ.get('PERFORMANCE_MATTERS_SFTP_PASSWORD') # the password provided by PM to log in using the username above
sftpHOST = os.environ.get('PERFORMANCE_MATTERS_SFTP_ADDRESS') # the URL/server IP provided by PM
cnopts = pysftp.CnOpts(knownhosts='known_hosts') # connection options to use the known_hosts file for key validation


print(f"Username: {un} |Password: {pw} |Server: {cs}") # debug so we can see where oracle is trying to connect to/with
print(f"SFTP Username: {sftpUN} |SFTP Password: {sftpPW} |SFTP Server: {sftpHOST}") # debug so we can see where oracle is trying to connect to/with
badnames = ['use', 'training1','trianing2','trianing3','trianing4','planning','admin','nurse','user', 'use ', 'payroll', 'human', "benefits", 'test', 'teststudent','test student','testtt','testtest']

if __name__ == '__main__': # main file execution
    with oracledb.connect(user=un, password=pw, dsn=cs) as con: # create the connecton to the database
        with con.cursor() as cur:  # start an entry cursor
            with open('schedule_log.txt', 'w') as log: # open a file for log output first
                with open('pmschedules.txt', 'w') as outputfile:  # open the output file
                    startTime = datetime.now()
                    startTime = startTime.strftime('%H:%M:%S')
                    print(f'INFO: Execution started at {startTime}')
                    print(f'INFO: Execution started at {startTime}', file=log)
                    print("INFO: Connection established: " + con.version)
                    print('SchoolID\tCourse Number\tSection ID\tSection Number\tExpression\tStudent ID\tTeacher Number\tTeacher DCID', file=outputfile) # print header line in output file
                    try:
                        cur.execute('SELECT student_number, first_name, last_name, id, schoolid, enroll_status, dcid FROM students ORDER BY student_number DESC')
                        students = cur.fetchall()  # fetchall() is used to fetch all records from result set and store the data from the query into the rows variable
                        today = datetime.now()  # get todays date and store it for finding the correct term later
                        # today = datetime.now() + timedelta(days = 120) #testing purposes
                        # print(f"DBUG: today = {today}")  # debug
                        # print(f"DBUG: today = {today}", file=log)  # debug

                        for student in students: #go through each entry in the students result. Each entry is a single student's data
                            try:
                                print(student, file=log)  # debug
                                if not str(student[1]).lower() in badnames and not str(student[2]).lower() in badnames: #check first and last name against array of bad names, only print if both come back not in it
                                    idNum = int(student[0]) #what we would refer to as their "ID Number" aka 6 digit number starting with 22xxxx or 21xxxx
                                    firstName = str(student[1])
                                    lastName = str(student[2])
                                    internalID = int(student[3]) #get the internal id of the student that is referenced in the classes entries
                                    schoolID = str(student[4])
                                    status = int(student[5]) #active on 0, inactive 1 or 2, 3 for graduated
                                    stuDCID = str(student[6])

                                    if (status == 0): # only worry about the students who are active
                                        #do another query to get their classes, filter to just the current term based on their school
                                        try:
                                            cur.execute("SELECT id, firstday, lastday, schoolid, dcid FROM terms WHERE schoolid = :school ORDER BY dcid DESC", school=schoolID)  # get a list of terms for the school, filtering to not full years. using bind variables as best practice https://python-oracledb.readthedocs.io/en/latest/user_guide/bind.html#bind
                                            terms = cur.fetchall()
                                            for term in terms:  # go through every term
                                                termStart = term[1]
                                                termEnd = term[2]
                                                # print(term) #debug
                                                #compare todays date to the start and end dates with 2 days before start so it populates before the first day of the term
                                                if ((termStart - timedelta(days=2) < today) and (termEnd + timedelta(days=1) > today)):
                                                    termid = str(term[0])
                                                    termDCID = str(term[4])
                                                    # print(f"Found good term for student {idNum}: {termid} | {termDCID}"
                                                    print(f"Found good term for student {idNum}: {termid} | {termDCID}", file=log)
                                                    # now for each term that is valid, do a query for all their courses and start processing them
                                                    try:
                                                        cur.execute("SELECT schoolid, course_number, sectionid, section_number, expression, teacherid FROM cc WHERE studentid = :studentid AND termid = :term ORDER BY course_number", studentid=internalID, term=termid)
                                                        userClasses = cur.fetchall()
                                                        for tuples in userClasses:
                                                            classEntry = list(tuples)
                                                            print (classEntry, file=log) # debug
                                                            # get the info for each course that we will want to print out
                                                            schoolID = str(classEntry[0])
                                                            courseNum = str(classEntry[1])
                                                            sectionID = str(classEntry[2])
                                                            sectionNum = str(classEntry[3])
                                                            expression = str(classEntry[4])
                                                            # get the teacher info so we can get/print out their info as well
                                                            teacherID = str(classEntry[5])
                                                            # now get the teacher name and number from the users table using the schoolstaff id find the staff member
                                                            cur.execute("SELECT users.teachernumber, users.lastfirst, users.dcid FROM schoolstaff LEFT JOIN users ON schoolstaff.users_dcid = users.dcid WHERE schoolstaff.id = :staffid", staffid=teacherID)
                                                            teachers = cur.fetchall() # there should really only be one row, so don't bother doing a loop and just take the first result
                                                            teacherNum = str(teachers[0][0])
                                                            teacherName = str(teachers[0][1])
                                                            teacherDCID = str(teachers[0][2])
                                                            #print out all the info for the class entry
                                                            print(f'{schoolID}\t{courseNum}\t{sectionID}\t{sectionNum}\t{expression}\t{idNum}\t{teacherNum}\t{teacherDCID}', file=outputfile)

                                                    except Exception as err:
                                                        print(f'ERROR finding course or teacher info for {idNum}: {er}')
                                                        print(f'ERROR finding course or teacher info for {idNum}: {er}', file=log)

                                        except Exception as er:
                                            print(f'ERROR finding term for {idNum}: {er}')
                                            print(f'ERROR finding term for {idNum}: {er}', file=log)            

                            except Exception as err:
                                print(f'ERROR getting student info for {idNum}: {er}')
                                print(f'ERROR getting student info for {idNum}: {er}', file=log)

                    except Exception as er:
                        print(f'ERROR: Unknown initializion problem: {er}')
                        print(f'ERROR: Unknown initializion problem: {er}', file=log)

                #after all the files are done writing and now closed, open an sftp connection to the server and place the file on there
                try:
                    with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
                        print('SFTP connection established')
                        print(sftp.listdir())  # debug
                        sftp.put('pmschedules.txt') #upload the file onto the sftp server
                        print("Schedule file placed on remote server for " + str(today))
                        print("Schedule file placed on remote server for " + str(today), file=log)
                except Exception as er:
                    print(f'ERROR while connecting or uploading to Performance Matters SFTP server: {er}')
                    print(f'ERROR while connecting or uploading to Performance Matters SFTP server: {er}', file=log)
