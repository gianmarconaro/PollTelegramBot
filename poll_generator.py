import os
import poll_db as db
from datetime import datetime, timedelta
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
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)
import asyncio

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

# emotes
pill_emote = "💊 "
alarm_emote = "⏰ "
light_bulb_emote = "💡 "  # leaderboard
fire_emote = "🔥 "  # 3 streak
plane_emote = "✈️ "  # 5 streak
rocket_emote = "🚀 "  # 7 streak
star_emote = "⭐️ "  # 10 streak
planet_emote = "🪐 "  # 12 streak
trophy_emote = "🏆 "  # 15 streak
crown_emote = "👑 "  # 17 streak
moyai_emote = "🗿 "  # 20 streak


def conversation_handler():
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

    return conversation_handler


# Function to handle the /reset command
async def reset(update: Update, _: CallbackContext):
    current_poll.clear()
    reply_markup = ReplyKeyboardRemove()
    await update.message.reply_text(
        "Poll resetted successfully!\n\nPress /create to create a new poll or /help to see the available commands.",
        reply_markup=reply_markup,
    )


# Function to handle the /poll command
async def chose_creation(update: Update, _: CallbackContext):
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

    current_poll_id = db.Poll().get_next_poll_id()
    intro = pill_emote + "DEILIPILL #" + str(current_poll_id)
    current_poll["question"] = intro + "\n\n" + text
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
        "Okay, the poll is ready!\n\nHere's a summary of the poll:\n\nQuestion:\n"
        + str(current_poll["question"])
        + "\n\nOptions:\n"
        + "\n".join(current_poll["options"])
        + "\n\nCorrect answer: "
        + str(current_poll["correct_option"] + 1)
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


# Function to create the poll
async def enter_create_poll(update: Update, context: CallbackContext):
    # create the poll and save it in the surveys dictionary with a unique id
    selected_option = update.callback_query.data
    if selected_option == "0":
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
        await update.callback_query.message.reply_text("Poll creation aborted!")
        await reset(update, context)
    return ENTER_SEND_POLL


# Function to send the poll to the group
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
        current_poll_id = db.Poll().get_next_poll_id()
        telegram_poll_id = poll_message.poll.id
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=30)
        options = ", ".join(current_poll["options"])

        # add the poll to the database
        db.Poll().add_poll(
            current_poll_id,
            telegram_poll_id,
            poll_message.message_id,
            current_poll["question"],
            options,
            current_poll["correct_option"],
            current_poll["explanation"],
            start_time,
            end_time,
        )

        # schedule the poll to be closed
        asyncio.create_task(
            schedule_close_poll(
                context.bot, current_poll_id, poll_message.message_id, end_time
            )
        )

        await update.callback_query.message.reply_text("Poll sent successfully!")
    else:
        await update.callback_query.message.reply_text("Poll sending aborted!")
        await reset(update, context)
    return ConversationHandler.END


async def generate_test_poll(update: Update, context: CallbackContext):
    # create a poll with a direct command instead of the conversation handler
    current_poll_id = db.Poll().get_next_poll_id()
    intro = pill_emote + "DEILIPILL #" + str(current_poll_id)
    question = intro + "\n\n" + "What is the capital of Italy?"
    options = ["Rome", "Milan", "Turin", "Naples"]
    correct_option = 1
    explanation = "Milan is the capital of Italy."
    poll_message = await context.bot.send_poll(
        chat_id=os.environ.get("GROUP_ID"),
        question=question,
        options=options,
        is_anonymous=False,
        type="quiz",
        correct_option_id=correct_option,
        explanation=explanation,
    )
    telegram_poll_id = poll_message.poll.id
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=10)
    options = ", ".join(options)

    # add the poll to the database
    db.Poll().add_poll(
        current_poll_id,
        telegram_poll_id,
        poll_message.message_id,
        question,
        options,
        correct_option,
        explanation,
        start_time,
        end_time,
    )
    await update.message.reply_text("Poll sent successfully!")

    asyncio.create_task(
        schedule_close_poll(
            context.bot, current_poll_id, poll_message.message_id, end_time
        )
    )

    return ConversationHandler.END


async def close_poll(bot, poll_id, message_id):
    db.Poll().close_poll(poll_id)
    await bot.stop_poll(chat_id=os.environ.get("GROUP_ID"), message_id=message_id)

    message = alarm_emote + "DEILIPILL #" + str(poll_id) + " closed!"
    await bot.send_message(chat_id=os.environ.get("GROUP_ID"), text=message)

    db.Poll().update_scores(poll_id)
    await print_scoreboard(bot)


async def schedule_close_poll(bot, poll_id, message_id, end_date):
    delta = end_date - datetime.now()
    await asyncio.sleep(delta.total_seconds())
    await close_poll(bot, poll_id, message_id)


async def print_scoreboard(bot):

    def compose_string(score_tuple):
        telegram_player_id, username, score, streak, longest_streak = score_tuple
        if streak >= 3 and streak < 5:
            return f"{username}: {score} points - {streak} in streak {fire_emote}"
        if streak >= 5 and streak < 7:
            return f"{username}: {score} points - {streak} in streak {plane_emote}"
        if streak >= 7 and streak < 10:
            return f"{username}: {score} points - {streak} in streak {rocket_emote}"
        if streak >= 10 and streak < 12:
            return f"{username}: {score} points - {streak} in streak {star_emote}"
        if streak >= 12 and streak < 15:
            return f"{username}: {score} points - {streak} in streak {planet_emote}"
        if streak >= 15 and streak < 17:
            return f"{username}: {score} points - {streak} in streak {trophy_emote}"
        if streak >= 17 and streak < 20:
            return f"{username}: {score} points - {streak} in streak {crown_emote}"
        if streak >= 20:
            return f"{username}: {score} points - {streak} in streak {moyai_emote}"
        else:
            return f"{username}: {score} points"
    
    scoreboard = db.Poll().get_scoreboard()
    intro = f"{light_bulb_emote} SCOREBOARD:\n\n"
    results_string = intro + "\n- ".join([compose_string(score_tuple) for score_tuple in scoreboard])

    await bot.send_message(
        chat_id=os.environ.get("GROUP_ID"),
        text=results_string,
    )
