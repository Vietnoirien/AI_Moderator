# AI Moderator: Your Discord Server's Guardian Angel 🛡️✨

Welcome to AI Moderator, an innovative solution designed to keep your Discord server environment safe, respectful, and engaging. This project combines the power of natural language processing with a user-friendly interface to provide comprehensive moderation services tailored to your community's needs.

## Features 📊

- **Intelligent Moderation**: Utilizing advanced NLP models, AI Moderator can understand context and sentiment within conversations for precise intervention.

- **Real-Time Analysis**: Messages are analyzed on the fly to detect inappropriate content or behavior, ensuring a healthy server environment.

- **Customizable Interventions**: Tailor moderation responses to align with your community's culture and guidelines for consistent communication.

- **Engaging Conversations**: Beyond moderation, AI Moderator can interact with users, providing information or entertainment as needed.

- **Future-Proof Design**: Built on the Ollama API framework, our bot stays up-to-date with the latest advancements in language models for continuous improvement.

- **Privacy and Security**: We prioritize user privacy, adhering to strict guidelines and Discord's terms of service while handling data responsibly.

## How AI Moderator Enhances Your Server 🌱

AI Moderator is more than just a bot, it's an essential tool that adapts to your server's unique dynamics. Here's how:

- **Contextual Understanding**: By maintaining conversation history, the bot can make informed decisions based on the context of interactions rather than isolated messages.

- **Sentiment Analysis for Harmony**: Detecting shifts in tone and mood helps prevent conflicts or harassment by intervening at the right moments with appropriate responses.

- **Scalable Moderation**: As your server grows, AI Moderator scales accordingly, ensuring that moderation remains effective without compromising performance.

- **Seamless Integration**: Easily integrate additional features or services to enhance functionality and provide a more comprehensive experience for your community members.

## Getting Started with AI Moderator 🚀

To begin using AI Moderator, follow these simple steps:

1. Install the bot on your Discord server following standard procedures. 🛠️
2. Configure initial settings to align with your server's guidelines and culture. ✍️
3. Allow the bot access to necessary permissions for effective moderation. ✅
4. Customize response templates and intervention strategies as desired. 🎨
5. Monitor interactions and provide feedback to refine AI Moderator's performance over time. 🔍
6. Enjoy a healthier, more engaging server environment! 🎉

## Requirements 📋

- discord.py
- Flask
- python-dotenv
- psutil
- ollama
- torch
- numpy
- duckduckgo_search

## Installation 🛠️

1. **Clone the repository:**
    ```bash
    git clone https://github.com/Vietnoirien/AI_Moderator
    ```

2. **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Set up the DISCORD_TOKEN and other environment variables in a `.env` file.**
    ```bash
    DISCORD_TOKEN=<your token>
    ```

4. **Initialize the SQLite database by running the `init_db` script.**
   ```bash
   python init_db.py
   ```

## Usage 💻

1. **Start the application:**
    ```bash
    python project.py
    ```

2. **Access the web interface at [http://localhost:5000](http://localhost:5000).**

3. **From the web interface, you can:**
    - View moderated users.

    - View moderated user's messages, moderations, and sanctions.

    - User's analysis using a "psychotherapist_agent".

    - Manage AI models

4. **On the Discord server, users can interact with the bot by mentioning it or using various commands (e.g., `/search`, `/help`, `/about`).**

5. **The bot will automatically moderate user messages, inspect their content, and propose sanctions if necessary.**

6. **Moderated user's messages, moderations, and sanctions will be stored in the SQLite database and displayed in the flask API.**



## Contributing 🤝

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## Conclusion: Your Server's Guardian Angel 🛡️✨

AI Moderator is here to ensure that your Discord community thrives in a respectful and engaging environment. With its advanced capabilities and user-centric design, it stands as a testament to what technology can achieve when aligned with the values of its users. Welcome aboard! 🎉