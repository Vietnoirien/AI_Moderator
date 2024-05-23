import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

cur.execute("INSERT INTO posts (author, message, moderation) VALUES (?, ?, ?)",
            ('User', 'Content for the first message', 'moderation message'))


cur.execute("INSERT INTO posts (author, message, moderation) VALUES (?, ?, ?)",
            ('Second User', 'Content for the second message', 'moderation message'))


connection.commit()
connection.close()