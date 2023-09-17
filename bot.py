import os
import asyncio
import poll_db as db
from poll_generator import (
    conversation_handler,
    reset,
    generate_test_poll,
    close_poll,
    schedule_close_poll,
)
from datetime import datetime
from dotenv import load_dotenv
from telegram import (
    Update,
)
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackContext,
    PollAnswerHandler,
)

load_dotenv()
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("GROUP_ID")


# Function to handle unknown commands
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


# Function to handle the /start command
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Welcome to the poll bot!\n\nPress /help to see the available commands.",
    )


# Function to handle the /help command
async def help(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Hello! This bot can be used to create polls.\n\n/create - Create a poll\n/reset - Reset the current poll\n/help - Show this message\n/start - Start the bot",
    )


async def receive_poll_answer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    telegram_poll_id = answer.poll_id

    poll = db.Poll().get_poll(telegram_poll_id)
    user_option = answer.option_ids[0]
    correct_option = poll[5]
    telegram_user_id = answer.user.id

    db.Poll().add_player(telegram_user_id, answer.user.username)

    if user_option == correct_option:
        db.Poll().save_vote(telegram_user_id, telegram_poll_id, True)
        # db.Poll().increment_score_player(telegram_user_id)
    else:
        db.Poll().save_vote(telegram_user_id, telegram_poll_id, False)
        # db.Poll().reset_streak_player(telegram_user_id)


# create a function that loads all the polls from db that are not closed,
# then gets the end_date, and launches with asyncio a function to be executed at the required date
async def close_expired_polls(bot: ApplicationBuilder.bot):
    polls = db.Poll().get_open_polls()

    for poll in polls:
        poll_id, message_id, end_date = poll[0], poll[2], poll[8]
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S.%f")

        if end_date < datetime.now():
            asyncio.create_task(close_poll(bot, poll_id, message_id))
        else:
            asyncio.create_task(schedule_close_poll(bot, poll_id, message_id, end_date))


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # conversation
    application.add_handler(conversation_handler())

    # welcome
    welcome_handler = CommandHandler("start", start)
    application.add_handler(welcome_handler)

    # help
    help_handler = CommandHandler("help", help)
    application.add_handler(help_handler)

    # reset
    reset_handler = CommandHandler("reset", reset)
    application.add_handler(reset_handler)

    # test
    test_handler = CommandHandler("test", generate_test_poll)
    application.add_handler(test_handler)

    # unknown
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.add_handler(PollAnswerHandler(receive_poll_answer))

    loop.run_until_complete(close_expired_polls(application.bot))

    application.run_polling()


if __name__ == "__main__":
    main()
