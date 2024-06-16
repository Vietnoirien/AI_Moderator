import sqlite3
import sys

def db_init():
    connection = sqlite3.connect('database.db')

    with open('schema.sql') as f:
        connection.executescript(f.read())

    connection.commit()
    connection.close()
    return 0

if __name__ == '__main__':
    code = db_init()
    sys.exit(code)