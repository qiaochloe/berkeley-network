
def dbConnect():
    from dotenv import load_dotenv
    from os import environ
    import mysql.connector

    # Load env constants
    load_dotenv()
    DB_NAME = environ.get("databaseName")
    HOST = environ.get("host")
    USER = environ.get("user")
    PASSWORD = environ.get("password")

    # Connect to DB
    db = mysql.connector.connect(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DB_NAME
    )
    cursor = db.cursor()

    return cursor, db

# Removes empty strings from an array and returns
def removeEmptyElements(array):
    out = [i for i in array if i]
    if len(out) == 0:
        out = None
    return out