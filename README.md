
# D118-PerformanceMattersSchedules

Gets the PS course data for students in their current term and exports it to a tab delimited .txt file for import into Performance Matters

## Overview

The script first does a query for all students in PowerSchool. It then begins to go through each student one at a time, only processing further for active students.
Then it takes the current date and does a query to find all terms from the *terms* table in PowerSchool, and each term's start and end dates are compared to today's date to find the term (or terms) that is currently active for that student.
A third query is run for the student, finding enrollments from the *cc* table for the current term and student to retrieve the section information and teacher ID. A final query is performed to retrieve the teacher information for that course based on the teacher ID.
Then all the information about the student, course section, and teacher of that section is printed out to a tab delimited.txt file formatted to align with Performance Matter's template, and the file is closed.
Then a SFTP connection is established to the Performance Matters server, and the .txt file is uploaded to the server.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- PERFORMANCE_MATTERS_SFTP_USERNAME
- PERFORMANCE_MATTERS_SFTP_PASSWORD
- PERFORMANCE_MATTERS_SFTP_ADDRESS

These are fairly self explanatory, slightly more context is provided in the script comments.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

**As part of the pysftp connection to the SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

## Customization

This script should *"just work"* even for other districts outside of D118 as it uses standard PowerSchool tables and outputs to the format required by Performance Matters, as long as the requirements above are met.
If you need to only include terms that are not a whole year (quarters, trimesters, semesters only), you can use `WHERE isyearrec = 0` in the terms finding query
