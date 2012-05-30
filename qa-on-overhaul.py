#!/usr/bin/env python
"""Test the upgrade process for EAV versioning by running each SQL query agains the given DB

On jemueller-dt, during use of this script, you'll probably find these useful:

./qa-on-overhaul.py preoverhaul-check.sql postgresql://plone:pl0n3@gibbon-test-db/avrc_data

./qa-on-overhaul.py overhaul-qa.sql postgresql://plone:pl0n3@gibbon-test-db/avrc_data

./qa-on-overhaul.py postcontext-check.sql postgresql://plone:pl0n3@gibbon-qa/avrc_data

"""

def main():
    """Handle argv, specialize globals, launch job."""
    import sys
    usage = """./qa-on-overhaul.py FILE NEWCONNECT"""
    if len(sys.argv) != 3:
        print usage
        sys.exit(-1)
    filename = sys.argv[1]
    connectionString = sys.argv[2]
    testQueries = getTestQueries(filename)
    for query in testQueries:
        freshCursor = getPsycopg2Cursor(connectionString)
        runQueryAndReportAnyRows(query,freshCursor)

def cleanSqlFromFile(inSQL):
    """Return SQL lacking weird characters up front."""
    newSQL = inSQL
    normal = r'abcdefghijklmnopqrstuvwxyz"'
    normal += normal.upper()
    normal += "0123456789 \n\t\\!@#$%^&*()-_+='<,>./?"
    while newSQL[0] not in normal:
        newSQL = newSQL[1:]
    return newSQL

def getTestQueries(filename):
    f = open(filename)
    text = f.read()
    f.close()
    for badword in ["UPDATE"]:
        if badword in text:
            raise Exception("You shouldn't have %s in the file!"%badword)
    goodEnough = "abcdefghijklmnopqrstuvwxyz"
    goodEnough = "-" + goodEnough + goodEnough.upper()
    queries = map((lambda s: s.strip()),text.split(";"))
    out = []
    for qry in queries:
        if not qry:
            continue
        cleaned = cleanSqlFromFile(qry)
        cleaned = cleaned.strip()
        if cleaned:
            out.append(cleaned)
    return out

def getPsycopg2Cursor(connectionString,dictionary=True):
    """Returns a postgres DB cursor object given a connection string.

    Expected input: postgresql://plone:pl0n3@gibbon-test-db/avrc_data

    This method is less DB agnostic than the sqlalchemy way of doing it
    but you have more ability to simply feed in SQL and get back a table
    without restating the table and column names in the python code over
    and over so the sqlalchemy machinery knows what to look for."""
    from psycopg2 import connect
    from psycopg2 import OperationalError
    from psycopg2.extras import RealDictCursor
    ## connectionString parsing...
    protocol, connectTo = connectionString.split("//")
    if "postgr" not in protocol:
        raise Exception("weird input: " + connectionString)
    machine,db = connectTo.split("/")
    if "@" in machine:
        login,host = machine.split("@")
        if ":" in login:
            user,pw = login.split(":")
        else:
            user,pw = None,None
    else:
        host = machine
        user,pw = None,None
    ## Default values for everything...
    inP = {
         "user":[user,"plone"]
        ,"host":[host,"gibbon-test-db"]
        ,"db":[db,"avrc_data"]
        ,"pw":[pw,"pl0n3"]}
    for tag in inP: 
        if inP[tag][0]:
            inP[tag] = inP[tag][0]
        else:
            inP[tag] = inP[tag][1]
    ## Compose the actual connection string...
    conn_string = "host='%(host)s' dbname='%(db)s' user='%(user)s' password='%(pw)s'"
    conn_string = conn_string % inP
    ## Connect with error reporting to help debug
    try: 
        conn = connect(conn_string)
    except OperationalError as err: 
        print "conn_string[:-10] =",conn_string[:-10]
        raise err
    if dictionary:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:
        cursor = conn.cursor()
    return cursor



def runQueryAndReportAnyRows(sql,cursor):
    import psycopg2
    try:
        cursor.execute(sql+";")
    except psycopg2.ProgrammingError as err:
        print "="*20
        print "COULDN'T EVEN RUN THIS DUE TO ERROR:"
        print err.__str__()
        print sql
        return None
    results = cursor.fetchall()
    if len(results):
        print "="*20
        print "PROBLEM WITH DATABASE FOUND!"
        print sql
        print "-"*15
        for row in results:
            print row

if __name__ == '__main__':
    main()

