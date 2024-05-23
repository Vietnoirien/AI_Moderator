AI Moderator, your Discord Moderation Bot
This project is a Python application that combines a Discord bot with a Flask web application and an SQLite database. The Discord bot is designed to moderate user messages, inspect their content for harmful or inappropriate language, and propose appropriate sanctions based on the severity of the message. The Flask app provides a web interface to manage and display the moderated messages, moderations, and sanctions stored in the database.

Features
Discord bot for moderating user messages
AI-powered content inspection and moderation
Customizable moderation rules and sanctions
SQLite database for storing user messages, moderations, and sanctions
Flask web application for managing and displaying moderated content
User interface for viewing moderated messages, moderations, and sanctions
Ability to start and stop the Discord bot from the web interface
Requirements
Python 3.x
Discord.py library
Flask
SQLite3
Installation
Clone the repository:
git clone https://github.com/your-repo/discord-moderation-bot.git



Install the required dependencies:
pip install -r requirements.txt



Set up the Discord bot token and other environment variables in a .env file.

Initialize the SQLite database by running the schema.sql script.

Usage
Start the Flask application:
python app.py



Access the web interface at http://localhost:5000.

From the web interface, you can start the Discord bot, view moderated messages, moderations, and sanctions, and manage the application.

On the Discord server, users can interact with the bot using various commands (e.g., /chat, /help, /about).

The bot will automatically moderate user messages, inspect their content, and propose sanctions if necessary.

Moderated messages, moderations, and sanctions will be stored in the SQLite database and displayed in the web interface.

Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.
