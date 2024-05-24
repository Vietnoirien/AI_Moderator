import re
import discord
import ollama
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
import sqlite3
from threading import Thread
from dotenv import load_dotenv
import os
import psutil
import sys
import signal
import json

flask_thread = None
bot_thread = None
running_bot = None
load_dotenv()



############OLLAMA###########
with open('models.json', 'r') as f:
    models = json.load(f)

class Agent:

    USER_ADD="reply in french"

    
    def __init__(self):
        self.model_names = {}
        for model_name, model_data in models.items():
            name = str(model_data['model'])
            prompt = str(model_data['sysprompt'])
            ollama.create(model=name, modelfile=prompt)
            self.model_names[model_name] = name

    def prompt(self, prompt, role="user", model_name="llama3"):
        model = self.model_names.get(model_name, "llama3")
        add = "Keep your reply short" if model == "llama3" else ""
        user_add = self.USER_ADD if model != "system" else ""
        message = {'role': role, 'content': user_add + prompt + add,}
        try:
            response = ollama.chat(model=model, messages=[message])
            return response['message']['content']
        except ollama.ResponseError as e:
            print('Error:', e.error)


    def sysmsg(self, message):
        try:
            response = self.prompt(message, role="user", model_name="system_msg")
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)

    def inspect(self, message):
        try:
            response = self.prompt(message, role="user", model_name="inspect_agent")
            print(response)
            return response.lower()
        except ollama.ResponseError as e:
            print('Error:', e.error)


    def moderate(self, message):
        try:
            message = str(message)
            response = self.prompt(message, role="user", model_name="moderator_agent")
            print(response)
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)

    def greeting(self, user):
        try:
            response = self.prompt(user, role="user", model_name="greeting_model")
            print(response)
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)



############DISCORD###########
TOKEN = os.getenv("DISCORD_TOKEN")
print(TOKEN)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
agent = Agent()

@client.event
async def on_ready():
    ready=agent.sysmsg("give a validation that you are logged as" + str(client.user))
    print(ready)
    

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('/chat'):
        await message.channel.send(agent.prompt(message.content[4:]))

    if message.content.startswith('/help'):
        await message.channel.send('''
            /chat : pour parler avec llama3
/help : Affiche cette page
/about : Information à propos du bot
        ''')
    
    if message.content.startswith('/about'):
        await message.channel.send('''
            Votre-pire-cauchemard est un bot Discord développé par Vietnoirien qui évalue les messages en fonction de leur contenu et alerte les modérateurs en cas d'offense, proposant des sanctions appropriées !
        ''')

    if message.content.startswith('/test_greeting'):
        await message.channel.send(agent.greeting(message.author.name))
            

    else:
        if agent.inspect(message.content) == "harmful":
            alert = f'`{message.author} a dis {message.content}`'
            user = get_user(message.author)
            if flagged(user) is True:
                previous_messages = get_messages(message.author)
                if len(previous_messages) > 1:
                    blame = f"Has already been warned {len(previous_messages)} times"
                else:
                    blame = "Second warning"
                previous = str(previous_messages)
                last_sanction = get_sanction(message.author)
                sanction = str(last_sanction)
                print(sanction)
                moderation = agent.moderate(message.content + "This is a recidivist" + blame + "Previous sanction was:" + sanction + "Has already been warned for his previous message:" + previous)
            else:
                flag(user)
                blame = "First warning"
                moderation = agent.moderate(message.content + blame)
            store_moderation(message.author, message.content, moderation)
            await message.channel.send(alert)
            await message.channel.send(moderation)


async def on_member_join(member):
    guild = member.guild
    if guild.system_channel is not None:
        await guild.system_channel.send(agent.greeting(member.mention)) 


def run_bot():
    global running_bot, bot_thread

    # Vérifier si le bot est déjà en cours d'exécution
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'python.exe' and 'discord' in ' '.join(proc.cmdline()).lower():
            running_bot = proc
            break

    if running_bot:
        # Le bot est déjà en cours d'exécution, l'arrêter
        running_bot.terminate()
        print("Bot arrêté")
        running_bot = None
        if bot_thread:
            bot_thread.join()
            bot_thread = None
    else:
        # Démarrer le bot dans un nouveau thread
        bot_thread = Thread(client.run(TOKEN))
        bot_thread.start()
        print("Bot démarré")

    return "Bot démarré" if running_bot is None else "Bot arrêté"

##############DATABASE###########


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

def get_messages(username):
    username = str(username)
    conn = get_db_connection()
    cursor = conn.execute("SELECT message FROM posts WHERE author = ? ORDER BY created DESC", (username,))
    messages = [row[0] for row in cursor.fetchall()]
    conn.close()
    return messages

def get_moderation(username):
    username = str(username)
    conn = get_db_connection()
    cursor = conn.execute("SELECT moderation FROM posts WHERE author = ? ORDER BY created DESC", (username,))
    moderations = [row[0] for row in cursor.fetchall()]
    conn.close()
    return moderations

def get_sanction(username):
    username = str(username)
    get_moderation(username)
    sanctions = []
    for moderation in get_moderation(username):
        sanction = re.search(r'Sanction: (.*)', moderation)
        if sanction:
            sanctions.append(sanction[1])
    return sanctions

def get_user(username):
    username = str(username)
    conn = get_db_connection()
    cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if user is None:
        conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
        cursor = conn.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
    conn.commit()  
    conn.close()
    if user is not None:
        user_id = user[0]

    return user_id

def flagged(user_id):
    user_id = str(user_id)
    conn = get_db_connection()
    cursor = conn.execute("SELECT is_warned FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result is None:
        return None
    is_warned = result[0]
    print(is_warned)
    return True if is_warned == 1 else False

def flag(user_id):
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_warned=1 WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return "User flagged"

def store_moderation(user, message, moderation):
    conn = get_db_connection()
    conn.execute("INSERT INTO posts (author, message, moderation) VALUES (?, ?, ?)", (str(user), str(message), str(moderation)))
    conn.commit()
    conn.close()
    return "Message stored"

############FLASK###########


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()
    return render_template('index.html', posts=posts)

@app.route('/run', methods=['POST'])
def run():
    print(run_bot())
    return redirect(url_for('index'))


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title or not content:
            flash('Title and content are required!')
        else:
            conn = get_db_connection()
            conn.execute("INSERT INTO posts (title, content) VALUES (?, ?)", (title, content))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title or not content:
            flash('Title and content are required!')
        else:
            conn = get_db_connection()
            conn.execute("UPDATE posts SET title=?, content=? WHERE id=?", (title, content, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted!'.format(post['title']))
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()

    def signal_handler(signal, frame):
        print('Arrêt de l\'application...')
        if bot_thread:
            bot_thread.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()