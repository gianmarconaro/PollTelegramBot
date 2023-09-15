import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, PollAnswerHandler, PollHandler, CallbackContext, ConversationHandler

# Define the different states a chat can be in
ENTER_START_CREATION, ENTER_QUESTION, ENTER_OPTIONS, ENTER_CORRECT_ANSWER = range(4)

# Dictionary to store the currently created poll
current_poll = {}

# Dictionary to store all the created polls
surveys = {}

# Function to handle unknown commands
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command."
    )

# Function to handle the /start command
async def start(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Welcome to the poll bot!\n\nPress /help to see the available commands.",
    )

# Function to handle the /help command 
async def help(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        "Hello! This bot can be used to create polls.\n\n/create - Create a poll\n/reset - Reset the current poll\n/help - Show this message\n/start - Start the bot",
    )

# Function to handle the /reset command
async def reset(update: Update, context: CallbackContext) -> int:
    current_poll.clear()
    reply_markup = ReplyKeyboardRemove()
    await update.message.reply_text(
        "Poll resetted successfully!\n\nPress /create to create a new poll or /help to see the available commands.",
        reply_markup=reply_markup
    )

# Function to handle the /poll command
async def chose_creation(update: Update, context: CallbackContext) -> int:
    current_poll.clear()
    await update.message.reply_text(
        "Choose what you want to do:",
        reply_markup=ReplyKeyboardMarkup([["Create Poll"]])
    )
    return ENTER_START_CREATION

# Function to handle the /poll command
async def start_creation(update: Update, context: CallbackContext) -> int:
    reply_markup = ReplyKeyboardRemove()
    text = update.message.text
    if text == "Create Poll":
        # Start the poll creation conversation
        await update.message.reply_text(
            "Okay, let's create a poll!\n\nWrite the question:",
            reply_markup=reply_markup
        )
    if text == "/reset":
        await reset(update, context)
        return ConversationHandler.END
        
    return ENTER_QUESTION

# Function to handle the question of the poll
async def enter_question(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == "/reset":
        await reset(update, context)
        return ConversationHandler.END  
    
    current_poll['question'] = text
    await update.message.reply_text(
        "Nice! Now send me the options separated with a comma (,). For example: Option 1,Option 2,Option 3,Option 4"
    )
    return ENTER_OPTIONS

# Function to handle the options of the poll
async def enter_options(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    if text == "/reset":
        await reset(update, context)
        return ConversationHandler.END
    
    options = text.split(",")
    context.user_data['options'] = options
    keyboard = [[InlineKeyboardButton(option, callback_data=str(index))] for index, option in enumerate(options)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Ora seleziona la risposta corretta:",
        reply_markup=reply_markup
    )
    return ENTER_CORRECT_ANSWER

# Function to handle the correct answer of the poll
async def enter_correct_answer(update: Update, context: CallbackContext) -> int:    
    query = update.callback_query
    context.user_data['correct_option'] = int(query.data)

    # Creazione del sondaggio
    question = current_poll['question']
    options = current_poll['options']
    correct_option = current_poll['correct_option']
    end_time = datetime.now() + timedelta(hours=24)
    surveys[question] = {'options': options, 'correct_option': correct_option, 'end_time': end_time, 'answers': {}}
    
    # Invia il sondaggio nella chat specificata
    context.bot.send_message(chat_id=os.environ.get("GROUP_ID"), text=f"Survey: {question}")
    for index, option in enumerate(options):
        context.bot.send_message(chat_id=os.environ.get("GROUP_ID"), text=f"{index+1}. {option}")
    
    await update.message.reply_text(
        "Poll created successfully!"
    )
    return ConversationHandler.END

def main():
    load_dotenv()

    application = ApplicationBuilder().token(
        os.environ.get("TELEGRAM_TOKEN")).build()
    
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('create', chose_creation)],
        states={
            ENTER_START_CREATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, start_creation)],
            ENTER_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_question)],
            ENTER_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_options)],
            ENTER_CORRECT_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_correct_answer)],
        },
        fallbacks=[],
        allow_reentry=True
    )
    # conversation
    application.add_handler(conversation_handler)

    # welcome
    welcome_handler = CommandHandler('start', start)
    application.add_handler(welcome_handler)

    # help
    help_handler = CommandHandler('help', help)
    application.add_handler(help_handler)

    # reset
    reset_handler = CommandHandler('reset', reset)
    application.add_handler(reset_handler)

    # unknown
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()

if __name__ == "__main__":
    main()