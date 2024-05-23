import discord
import ollama
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
import sqlite3
from threading import Thread
from dotenv import load_dotenv
import os

load_dotenv()

class Agent:
    ############MODELS###########
    INSPECT_AGENT='''
    FROM llama3
    SYSTEM You are an IA rating model, you inspect text messages and rate them as harmful, neutral or harmless depending on the content. You tolerate light speech as you are a member of a gaming community. You tolerate some aduld content as you are a member of a mature community.you only reply with harmful, neutral or harmless. don't add anything else.
    '''

    MODERATOR_AGENT='''
    FROM llama3
    SYSTEM You are a discord moderator model, you moderate discord messages that contain harmful or harrassing language by alerting the user and proposing sanctions to give according to the gravity of the message. You tolerate light speech as you are a member of a gaming community. You tolerate some aduld content as you are a member of a mature community. You format your response with "Alerte" "Moderation" and "Sanction" on different lines. You keep Alerte and Sanction section short and clear, and you can use a maximum of 10 words for each response. You explain a bit more in the Moderation section.
    '''

    GREETING_MODEL='''
    FROM llama3
    SYSTEM You are a welcoming model, given a user name you welcome them to "Vietnoirie General Hospital" and give them some tips on how to use the bot. like /AI to talk with llama3, /help to get help on how to use the bot and /about to get information about the bot. dont ask question
    '''

    SYSTEM_MSG='''
    FROM llama3
    SYSTEM You are a system message model, you reply concise messages. You are not here to joke or to be polite, you provide useful information as you are an essential part of an informatic system. You do what is asked and don't add anything else.
    '''

    USER_ADD="reply in french"

    ############OLLAMA###########
    def __init__(self):
        ollama.create(model="inspector", modelfile=self.INSPECT_AGENT)
        ollama.create(model="moderator", modelfile=self.MODERATOR_AGENT)
        ollama.create(model="greeting", modelfile=self.GREETING_MODEL)
        ollama.create(model="system", modelfile=self.SYSTEM_MSG)

    def prompt(self, prompt, role="user", model="llama3"):
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
            response = self.prompt(message, role="user", model="system")
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)

    def inspect(self, message):
        try:
            response = self.prompt(message, role="user", model="inspector")
            print(response)
            return response.lower()
        except ollama.ResponseError as e:
            print('Error:', e.error)


    def moderate(self, message):
        try:
            response = self.prompt(message, role="user", model="moderator")
            print(response)
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)

    def greeting(self, user):
        try:
            response = self.prompt(user, role="user", model="greeting")
            print(response)
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)



############DISCORD###########
TOKEN = os.getenv("DISCORD_TOKEN")


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
            user = get_user(str(message.author))
            if flagged(user):
                previous_messages = get_messages(user)
                blame = f"Has already been warned {len(previous_messages)} times" if len(previous_messages) > 1 else ""
                moderation = agent.moderate(message.content + "already been warned for" + str(previous_messages) + blame)
            else:
                flag(user)
                moderation = agent.moderate(message.content)
            store_moderation(message.author, message.content, moderation)
            await message.channel.send(alert)
            await message.channel.send(moderation)


async def on_member_join(member):
    guild = member.guild
    if guild.system_channel is not None:
        await guild.system_channel.send(agent.greeting(member.mention)) 


def run_bot():
    client.run(TOKEN)
    return "Bot is running"


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
    conn = get_db_connection()
    message = conn.execute("SELECT message FROM posts WHERE username = ?", (username,)).fetchall()
    conn.close()
    return message

def get_user(username):
    conn = get_db_connection()
    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if user is None:
        conn.execute("INSERT INTO users (username) VALUES (?)", (username,))
        user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.commit()  
    conn.close()
    return user

def flagged(user_id):
    conn = get_db_connection()
    flagged = conn.execute("SELECT is_warned FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return True if flagged == "TRUE" else False
def flag(user_id):
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_warned=TRUE WHERE id = ?", (user_id,))
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
    bot = Thread(target=run_bot, daemon=True)
    bot.start()
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
