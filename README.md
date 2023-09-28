# Poll Telegram Bot

This is a Telegram bot for creating and managing polls directly on Telegram. You can create quiz polls and send it to a group telegram chat.

## Features

- Create polls with multiple-choice questions
- Close polls after 24h automatically
- Manage existing polls
- Collect and analyze poll results

## Requirements

- Python 3.6 or higher
- Telegram bot access token (see [Telegram Bot API](https://core.telegram.org/bots/api))

## Installation
1. Clone the repository to your local machine: `git clone https://github.com/gianmarconaro/PollTelegramBot.git`
2. Create a bot with `@BotFather`
3. Create a `.env` file in the project's main directory and enter your Telegram bot access token in the following format:
   
   `TELEGRAM_TOKEN="YOUR_TOKEN"`
   
   `GROUP_ID="YOUR_GROUP_CHAT"`
4. Install dependencies: `pip install -r requirements.txt`

## Usage

Run the bot using the command: `python bot.py` or host it on a `server`.

The bot will now be active on Telegram. You can start creating polls and interact with them directly from the private chat with the bot.

## Contributing

If you'd like to contribute to this project, follow these steps:

1. Fork the project
2. Create a new branch (`git checkout -b enhancements`)
3. Commit your changes (`git commit -m 'Added a new feature'`)
4. Push the branch (`git push origin enhancements`)
5. Open a new Pull Request

## Issue Reporting

If you find a bug or have a suggestion, please open a new issue [here](https://github.com/gianmarconaro/PollTelegramBot/issues).

