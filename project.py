import re
import discord
import ollama
from flask import Flask, render_template, request, session, url_for, flash, redirect
from werkzeug.exceptions import abort
import sqlite3
from threading import Thread
from dotenv import load_dotenv
import os
import json
import signal
import sys
import asyncio
import aiohttp
from functools import wraps
import torch
import numpy as np

flask_thread = None
bot_thread = None
running_bot = None
connector = None
client_session = None

agent = None

vault_content = []
vault_embed = []
vault_embed_tensor = None

conversation_history = []
system_message = "You are a helpful assistant that is an expert at extracting the most useful information from a given text. You are on a discord server and have messages on the format 'user': 'message'"

load_dotenv()



############OLLAMA###########
class Agent:
    USER_ADD="reply in french"
    sys_models = ["system_msg", "relevancy_agent"]
    
    def __init__(self):
        with open('models.json', 'r') as f:
            models = json.load(f)
        self.model_names = {}
        installed = ollama.list()
        for model in installed['models']:
            if model['name'] == 'mxbai-embed-large:latest':
                print("found mxbai")
            else:
                ollama.pull('mxbai-embed-large:latest')
        reset_vault()
        load_vault()
        embed_vault()
        for model_name, model_data in models.items():
            name = str(model_data['model'])
            prompt = str(model_data['sysprompt'])
            ollama.create(model=name, modelfile=prompt)
            self.model_names[model_name] = name
        

    def prompt(self, prompt, role="user", model_name="llama3"):
        model = self.model_names.get(model_name, "llama3")
        add = "Keep your reply short" if model == "llama3" else ""
        user_add = self.USER_ADD if model_name not in self.sys_models else ""
        message = {'role': role, 'content': user_add + " " + prompt + add,}
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
            return response.lower()
        except ollama.ResponseError as e:
            print('Error:', e.error)


    def moderate(self, message):
        try:
            message = str(message)
            response = self.prompt(message, role="user", model_name="moderator_agent")
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)

    def greeting(self, user):
        try:
            response = self.prompt(user, role="user", model_name="greeting_model")
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)

    def evaluate(self, user):
        messages = str(get_messages(user))
        prompt ="Your patient is {} here his past messages: {}. Just provide a short comment on the patient state, 2 sentences maximum.".format(user, messages)
        try:
            response = self.prompt(prompt, role="user", model_name="psychotherapist_agent")
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)

    def get_context(self, user_input, vault_embed, vault_content, top_k = 3):
        if vault_embed.nelement() == 0:
            return []
        input_embed = ollama.embeddings(model = "mxbai-embed-large", prompt = user_input)["embedding"]
        cos_scores = torch.cosine_similarity(torch.tensor(input_embed).unsqueeze(0), vault_embed)
        top_k = min(top_k, len(cos_scores))
        top_indices = torch.topk(cos_scores, k=top_k).indices.tolist()
        return [vault_content[i] for i in top_indices]
    
    def chat(self, user_input, system_message, vault_embed, vault_content, model, conversation_history, user):
        user_input = f"{user}: {user_input}"
        print(user_input)
        info = self.is_relevant(user_input)
        print(f"relevancy_agent: {info}")
        if _ := re.search("yes", info, re.IGNORECASE):
            self.summarize(user_input)
        relevant_context = self.get_context(user_input, vault_embed_tensor, vault_content, 3)
        if relevant_context:
            context_str = "\n".join(relevant_context)
            print(context_str)
        else:
            print("No context found")
        if relevant_context:
            user_input_with_context = "{} \n\n Remember: {}".format(user_input, context_str)
        conversation_history.append({"role": "user", "content": user_input_with_context})
        messages = [
            {"role": "system", "content": system_message + self.USER_ADD},
            *conversation_history
        ]
        response = ollama.chat(
            model=model,
            messages= messages
        )
        conversation_history.append({"role": "assistant", "content": response['message']['content']})
        return response['message']['content']
    
    def is_relevant(self, user_input):
        try:
            response = self.prompt(user_input, role="user", model_name="relevancy_agent")
            return response
        except ollama.ResponseError as e:
            print('Error:', e.error)
            
    def summarize(self, user_input):
        try:
            response = self.prompt(user_input, role="user", model_name="summarizer_agent")
            print(f"summarizer_agent: {response}")
        except ollama.ResponseError as e:
            print('Error:', e.error)

############OLLAMA###########

def summoning():
    global agent
    agent = Agent()
    msg = agent.sysmsg("message is Agent has been summoned")
    return msg


############RAG###############


def load_vault():
    global vault_content
    if os.path.exists('vault.txt'):
        with open('vault.txt', 'r', encoding = 'utf-8') as f:
            vault_content = f.readlines()

def embed_vault():
    global vault_embed, vault_embed_tensor
    for content in vault_content:
        try:
            response = ollama.embeddings(model="mxbai-embed-large", prompt=content)
            vault_embed.append(response["embedding"])
        except ollama.ResponseError as e:
            print('Error:', e.error)
    print("embedded")
    vault_embed_array = np.array(vault_embed)
    print(vault_embed_array)
    vault_embed_tensor = torch.tensor(vault_embed_array)
    print(vault_embed_tensor)
    return "Vault has been embedded"

def to_vault(message):
    with open("vault.txt", "a") as f:
        f.write(f"{message}\n")

def reset_vault():
    global vault_content, vault_embed, vault_embed_tensor
    vault_content = []
    vault_embed = []
    vault_embed_tensor = None

def reset_history():
    global conversation_history
    conversation_history = []
    response = agent.sysmsg("message is history has been reset")
    return response


############DISCORD###########
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
summoning()


@client.event
async def on_ready():
    ready = agent.sysmsg("message is the validation that bot is logged as" + str(client.user))
    print(ready)

    

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    mentions = message.mentions
    user_id = message.author.id
    mention = f"<@{user_id}>"

    if client.user in mentions:
        mention_pattern = r'<@(\d+)>'
        message_content = message.content  
        clean_message = re.sub(mention_pattern, '', message_content)
        print(clean_message)
        response = agent.chat(clean_message, system_message, vault_embed_tensor, vault_content, "llama3", conversation_history, message.author)
        await message.channel.send(response)
        return

    if message.content.startswith('/help'):
        await message.channel.send('''
            Pour parler avec llama3, mentionnez le bot
/help : Affiche cette page
/about : Information à propos du bot
        ''')
        return
    
    if message.content.startswith('/about'):
        await message.channel.send('''
            Votre-pire-cauchemard est un bot Discord développé par Vietnoirien qui évalue les messages en fonction de leur contenu et alerte les modérateurs en cas d'offense, proposant des sanctions appropriées !
        ''')
        return
    
    if message.content.startswith('/test_greeting'):
        await message.channel.send(agent.greeting(message.author.name))
        return
    
    if message.content.startswith('/rag') and message.author.guild_permissions.administrator:
        reset_vault()
        load_vault()
        response = agent.sysmsg(embed_vault())
        await message.channel.send(response)
        return
    
    if message.content.startswith('/reset') and message.author.guild_permissions.administrator:
        response = reset_history()
        await message.channel.send(response)

    else:
        if agent.inspect(message.content) == "harmful":
            alert = f'{mention} a dis {message.content}'
            user = get_user_id(message.author)
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

async def create_session():
    global client_session, connector
    connector = aiohttp.TCPConnector()
    client_session = aiohttp.ClientSession(connector=connector)

async def close_discord_client():
    await client.close()
    await client_session.close()
    await connector.close()

def run_bot():
    global bot_thread
    bot_thread = Thread(target=client.run, args=(TOKEN,), daemon=True)
    bot_thread.start()


##############DATABASE###########


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def get_posts():
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts").fetchall()
    conn.close()
    return posts

def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

def get_user_posts(username):
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts WHERE author=? ", (username,)).fetchall()
    conn.close()
    return posts

def get_messages(username):
    username = str(username)
    conn = get_db_connection()
    cursor = conn.execute("SELECT message FROM posts WHERE author = ? ORDER BY created DESC", (username,))
    messages = [row[0] for row in cursor.fetchall()]
    conn.close()
    return messages

def get_message(post_id):
    conn = get_db_connection()
    message = conn.execute("SELECT message FROM posts WHERE id = ?", (post_id,)).fetchone()
    conn.close()
    if message is None:
        abort(404)
    return message[0]
    

def get_moderation(username):
    username = str(username)
    conn = get_db_connection()
    cursor = conn.execute("SELECT moderation FROM posts WHERE author = ? ORDER BY created DESC", (username,))
    moderations = [row[0] for row in cursor.fetchall()]
    conn.close()
    return moderations

def number_of_messages(username):
    username = str(username)
    conn = get_db_connection()
    cursor = conn.execute("SELECT COUNT(*) FROM posts WHERE author = ?", (username,))
    number = cursor.fetchone()[0]
    conn.close()
    return number

def get_sanction(username):
    username = str(username)
    get_moderation(username)
    sanctions = []
    for moderation in get_moderation(username):
        sanction = re.search(r'Sanction: (.*)', moderation)
        if sanction:
            sanctions.append(sanction[1])
    return sanctions

def get_user_id(username):
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


def template_utils(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        template_utils = {
            'get_user': get_user_id,
            'flagged': flagged,
            'number_of_messages': number_of_messages,
        }
        kwargs['utils'] = template_utils
        return func(*args, **kwargs)
    return wrapper


@app.route('/')
@template_utils
def index(utils):
    posts = get_posts()
    return render_template('index.html', posts=posts, **utils)

@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

@app.route('/models')
def models():
    with open('models.json', 'r') as f:
        models = json.load(f)
    return render_template('models.html', models=models)

@app.route('/models/<model_name>/edit', methods=['GET', 'POST'])
def edit_model(model_name):
    with open('models.json', 'r') as f:
        models = json.load(f)
    model_data = models.get(model_name)
    if request.method == 'POST':
        model_data['model'] = request.form['model']
        model_data['sysprompt'] = request.form['sysprompt']
        if not model_data['model'] or not model_data['sysprompt']:
            flash("Model and system prompt are required")
        else:
            with open('models.json', 'w') as f:
                json.dump(models, f, indent=2)
            return redirect(url_for('models'))
    return render_template('edit_model.html', model_name=model_name, model_data=model_data)

@app.route('/summon_agent', methods=['POST'])
def summon_agent():
    summoned = summoning()
    flash(summoned)
    return redirect(url_for('models'))

@app.route('/<string:username>')
def users(username):
    analysis = agent.evaluate(username)
    posts = get_user_posts(username)
    return render_template('user.html', analysis=analysis, posts=posts, username=username)



###########SIGNAL HANDLER/MAINLOOP############


def signal_handler(signal, frame):
    print("Arrêt du bot Discord...")
    if bot_thread and bot_thread.is_alive():
        asyncio.run_coroutine_threadsafe(close_discord_client(), client.loop)
        bot_thread.join()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(create_session())
    thread = Thread(target=run_bot)
    thread.start()
    app.run()

