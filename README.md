# AI Moderator: Your Discord Moderation AI

This project is a Python application that combines a Discord bot with a Flask web application and an SQLite database. The Discord bot is designed to moderate user messages, inspect their content for harmful or inappropriate language, and propose appropriate sanctions based on the severity of the message. The Flask app provides a web interface to manage and display the moderated messages, moderations, and sanctions stored in the database.

## Features

- **Discord bot for moderating user messages**
- **LLAMA3-powered content inspection and moderation**
- **Customizable moderation rules and sanctions**
- **SQLite database for storing user messages, moderations, and sanctions**
- **Flask web application for managing and displaying moderated content**
- **User interface for viewing moderated messages, moderations, and sanctions**

## Requirements

- Python 3.x
- Discord.py library
- Flask
- SQLite3

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Vietnoirien/AI_Moderator
    ```

2. **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up the DISCORD_TOKEN and other environment variables in a `.env` file.**

4. **Initialize the SQLite database by running the `init_db` script.**
   ```bash
   python init_db.py
   ```

## Usage

1. **Start the Flask application:**
    ```bash
    python project.py
    ```

2. **Access the web interface at [http://localhost:5000](http://localhost:5000).**

3. **From the web interface, you can:**
    - Start the Discord bot
    - View moderated messages, moderations, and sanctions
    - Manage the application

4. **On the Discord server, users can interact with the bot using various commands (e.g., `/chat`, `/help`, `/about`).**

5. **The bot will automatically moderate user messages, inspect their content, and propose sanctions if necessary.**

6. **Moderated messages, moderations, and sanctions will be stored in the SQLite database and displayed in the web interface.**

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.
