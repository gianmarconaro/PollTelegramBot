import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    PollAnswerHandler,
    PollHandler,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)

# Define the different states a chat can be in
(
    ENTER_START_CREATION,
    ENTER_QUESTION,
    ENTER_OPTIONS,
    ENTER_CORRECT_ANSWER,
    ENTER_CREATE_POLL,
    ENTER_EXPLANATION,
    ENTER_SEND_POLL,
) = range(7)

# Dictionary to store the currently created poll
current_poll = {}

# Dictionary to store all the created polls
surveys = {}

# Variable to store the id of the current poll
current_poll_id = 0


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


# Function to handle the /reset command
async def reset(update: Update, context: CallbackContext):
    current_poll.clear()
    reply_markup = ReplyKeyboardRemove()
    await update.message.reply_text(
        "Poll resetted successfully!\n\nPress /create to create a new poll or /help to see the available commands.",
        reply_markup=reply_markup,
    )


# Function to handle the /poll command
async def chose_creation(update: Update, context: CallbackContext):
    current_poll.clear()
    await update.message.reply_text(
        "Choose what you want to do:",
        reply_markup=ReplyKeyboardMarkup([["Create Poll"]]),
    )
    return ENTER_START_CREATION


# Function to handle the /poll command
async def start_creation(update: Update, context: CallbackContext):
    reply_markup = ReplyKeyboardRemove()
    text = update.message.text
    if text == "Create Poll":
        # Start the poll creation conversation
        await update.message.reply_text(
            "Okay, let's create a poll!\n\nWrite the question:",
            reply_markup=reply_markup,
        )
    if text == "/reset":
        await reset(update, context)
        return ConversationHandler.END

    return ENTER_QUESTION


# Function to handle the question of the poll
async def enter_question(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "/reset":
        await reset(update, context)
        return ConversationHandler.END

    current_poll["question"] = text
    await update.message.reply_text(
        "Nice! Now send me the options separated with a comma (,). For example: Option 1,Option 2,Option 3,Option 4"
    )
    return ENTER_OPTIONS


# Function to handle the options of the poll
async def enter_options(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "/reset":
        await reset(update, context)
        return ConversationHandler.END

    options = text.split(",")
    current_poll["options"] = options
    keyboard = [
        [InlineKeyboardButton(option, callback_data=str(index))]
        for index, option in enumerate(options)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Now choose the correct answer:", reply_markup=reply_markup
    )
    return ENTER_CORRECT_ANSWER


# Function to handle the correct answer of the poll
async def enter_correct_answer(update: Update, context: CallbackContext):
    selected_option = update.callback_query.data
    current_poll["correct_option"] = int(selected_option)
    print(current_poll)
    # scrivi un messaggio con il riepilogo del sondaggio
    await update.callback_query.message.reply_text(
        "Nice! Now send me the explanation of the correct answer:"
    )
    return ENTER_EXPLANATION


# Function to handle the explanation of the poll
async def enter_explanation(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "/reset":
        await reset(update, context)
        return ConversationHandler.END
    text_len = len(text)
    if text_len > 200:
        await update.message.reply_text(
            "The explanation is "
            + text_len
            + " characters! Please write a shorter one."
        )
        return ENTER_EXPLANATION

    current_poll["explanation"] = text
    await update.message.reply_text(
        "Okay, the poll is ready!\n\nHere's a summary of the poll:\n\nQuestion: "
        + str(current_poll["question"])
        + "\n\nOptions:\nA) "
        + str(current_poll["options"][0])
        + "\nB) "
        + current_poll["options"][1]
        + "\nC) "
        + current_poll["options"][2]
        + "\nD) "
        + current_poll["options"][3]
        + "\n\nCorrect answer: "
        + str(current_poll["correct_option"])
        + "\n\nExplanation: "
        + current_poll["explanation"]
        + "\n\nDo you want to create the poll?",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Yes", callback_data=str(0)
                    ),  # callback_data is used to identify different buttons
                    InlineKeyboardButton("No", callback_data=str(1)),
                ]
            ]
        ),
    )
    return ENTER_CREATE_POLL


async def enter_create_poll(update: Update, context: CallbackContext):
    # create the poll and save it in the surveys dictionary with a unique id
    selected_option = update.callback_query.data
    if selected_option == "0":
        surveys[current_poll_id] = current_poll
        await update.callback_query.message.reply_text(
            "Poll created successfully!\n\nDo you want send the poll to the group?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Yes", callback_data=str(0)
                        ),  # callback_data is used to identify different buttons
                        InlineKeyboardButton("No", callback_data=str(1)),
                    ]
                ]
            ),
        )
    else:
        await update.callback_query.message.reply_text(
            "Poll creation aborted!\n\nPress /create to create a new poll or /help to see the available commands."
        )
    return ENTER_SEND_POLL


async def enter_send_poll(update: Update, context: CallbackContext):
    # send the poll to the group
    selected_option = update.callback_query.data
    if selected_option == "0":
        # send the poll to the group
        poll_message = await context.bot.send_poll(
            chat_id=os.environ.get("GROUP_ID"),
            question=current_poll["question"],
            options=current_poll["options"],
            is_anonymous=False,
            type="quiz",
            correct_option_id=current_poll["correct_option"],
            explanation=current_poll["explanation"],
        )
        start_time = datetime.now()
        surveys[current_poll_id]["start_time"] = start_time
        surveys[current_poll_id]["end_time"] = start_time + timedelta(hours=24)
        surveys[current_poll_id]["message_id"] = poll_message.message_id
        surveys[current_poll_id]["closed"] = False

        await update.callback_query.message.reply_text(
            "Poll sent successfully!\n\nPress /create to create a new poll or /help to see the available commands."
        )
    else:
        await update.callback_query.message.reply_text(
            "Poll sending aborted!\n\nPress /create to create a new poll or /help to see the available commands."
        )
    return ConversationHandler.END


def main():
    load_dotenv()

    application = ApplicationBuilder().token(os.environ.get("TELEGRAM_TOKEN")).build()

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler("create", chose_creation)],
        states={
            ENTER_START_CREATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, start_creation)
            ],
            ENTER_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_question)
            ],
            ENTER_OPTIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_options)
            ],
            ENTER_CORRECT_ANSWER: [CallbackQueryHandler(enter_correct_answer)],
            ENTER_EXPLANATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_explanation)
            ],
            ENTER_CREATE_POLL: [CallbackQueryHandler(enter_create_poll)],
            ENTER_SEND_POLL: [CallbackQueryHandler(enter_send_poll)],
        },
        fallbacks=[],
        allow_reentry=True,
    )
    # conversation
    application.add_handler(conversation_handler)

    # welcome
    welcome_handler = CommandHandler("start", start)
    application.add_handler(welcome_handler)

    # help
    help_handler = CommandHandler("help", help)
    application.add_handler(help_handler)

    # reset
    reset_handler = CommandHandler("reset", reset)
    application.add_handler(reset_handler)

    # unknown
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
