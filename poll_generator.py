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

from utils import authenticated

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
pill_emote = "💊 "  # title poll
alarm_emote = "⏰ "  # poll closed
light_bulb_emote = "💡 "  # leaderboard

top_emote = "🔝 "  # longest streak
sos_emote = "🆘 "
boom_emote = "💥 "
sad_emote = "😢 "
sun_emote = "☀️ "
astronaut_emote = "👨‍🚀 "
man_emote = "👨 "
toothbrush_emote = "🪥 "
walking_emote = "🚶‍♂️ "
rocket_emote = "🚀 "
earth_emote = "🌍 "
star_emote = "⭐️ "
satellite_emote = "🛰 "
hi_emote = "👋 "
moon_emote = "🌕 "
footsteps_emote = "👣 "
alien_emote = "👽 "
knife_emote = "🔪 "
gun_emote = "🔫 "
meat_emote = "🥩 "
chef_emote = "👨‍🍳 "
comet_emote = "☄️ "
medal_emote = "🎖 "
mayori_emote = "🗿 "
ufo_emote = "🛸 "
crown_emote = "👑 "
statue_emote = "🗽 "


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
@authenticated
async def reset(update: Update, _: CallbackContext):
    current_poll.clear()
    reply_markup = ReplyKeyboardRemove()
    await update.message.reply_text(
        "Poll resetted successfully!\n\nPress /create to create a new poll or /help to see the available commands.",
        reply_markup=reply_markup,
    )

@authenticated
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
    if len(text) > 200:
        await update.message.reply_text(
            "The explanation is "
            + len(text)
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
        end_time = start_time + timedelta(hours=24)
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


@authenticated
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


@authenticated
async def close_poll(bot, poll_id, message_id, delete):
    telegram_poll_id = db.Poll().get_telegram_poll_id_from_poll_id(poll_id)
    if not db.Poll().get_poll(telegram_poll_id):
        return
    
    db.Poll().close_poll(poll_id)
    await bot.stop_poll(chat_id=os.environ.get("GROUP_ID"), message_id=message_id)

    if not delete:
        message = alarm_emote + "DEILIPILL #" + str(poll_id) + " closed!"
        await bot.send_message(chat_id=os.environ.get("GROUP_ID"), text=message)

        db.Poll().update_scores(poll_id)
        await print_scoreboard(bot)


async def schedule_close_poll(bot, poll_id, message_id, end_date):
    delta = end_date - datetime.now()
    await asyncio.sleep(delta.total_seconds())

    telegram_poll_id = db.Poll().get_telegram_poll_id_from_poll_id(poll_id)
    if db.Poll().get_poll(telegram_poll_id)[9] == 1:
        return
    
    await close_poll(bot, poll_id, message_id, False)


async def print_scoreboard(bot):
    scoreboard = db.Poll().get_scoreboard()
    intro = f"{light_bulb_emote} SCOREBOARD:\n\n"
    results_string = intro + "\n\n".join(
        [
            compose_string(grid_position, score_tuple)
            for grid_position, score_tuple in enumerate(scoreboard, 1)
        ]
    )

    await bot.send_message(
        chat_id=os.environ.get("GROUP_ID"),
        text=results_string,
    )


def compose_string(grid_position, score_tuple):
    _, username, score, streak, longest_streak = score_tuple
    user_score = f"{grid_position}.\n{username}: {score} "
    if streak == 0 and longest_streak == 0:
        return (
            user_score
            + f"points\nStreak not found{sad_emote}\n{top_emote}streak: {longest_streak}"
        )
    if streak == 0:
        return (
            user_score
            + f"points\n{sos_emote}{boom_emote}Streak over...{sad_emote}\n{top_emote}streak: {longest_streak}"
        )
    elif streak == 1:
        return (
            user_score
            + f"points\n({streak} in a row) {astronaut_emote}Get dressed... \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 2:
        return (
            user_score
            + f"points\n({streak} in a row) {rocket_emote}{walking_emote}Walking in... \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 3:
        return (
            user_score
            + f"points\n({streak} in a row) {earth_emote}{rocket_emote}Leaving Earth... \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 4:
        return (
            user_score
            + f"points\n({streak} in a row) {rocket_emote}{star_emote}In orbit! \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 5:
        return (
            user_score
            + f"points\n({streak} in a row) {rocket_emote}{hi_emote}{satellite_emote}Waving Starlink! \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 6:
        return (
            user_score
            + f"points\n({streak} in a row) {rocket_emote}{moon_emote}Approaching Moon... \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 7:
        return (
            user_score
            + f"points\n({streak} in a row) {astronaut_emote}{footsteps_emote}Walking on Moon... \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 8:
        return (
            user_score
            + f"points\n({streak} in a row) {astronaut_emote}{hi_emote}{alien_emote}Meeting Bang-o Bong-o!# \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 9:
        return (
            user_score
            + f"points\n({streak} in a row) {astronaut_emote}{knife_emote}{alien_emote}Killing Bang-o Bong-o!# \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 10:
        return (
            user_score
            + f"points\n({streak} in a row) {chef_emote}{meat_emote}Eating Bang-o Bong-o!# \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 11:
        return (
            user_score
            + f"points\n({streak} in a row) {moon_emote}{rocket_emote}Leaving Moon... \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 12:
        return (
            user_score
            + f"points\n({streak} in a row) {rocket_emote}{comet_emote}Watching Halley's comet! \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 13:
        return (
            user_score
            + f"points\n({streak} in a row) {rocket_emote}{earth_emote}Coming back to Earth... \n{top_emote}streak: {longest_streak}"
        )
    elif streak == 14:
        return (
            user_score
            + f"points\n({streak} in a row) {man_emote}{medal_emote}Obtaining honors! \n{top_emote}streak: {longest_streak}"
        )
    elif streak > 14:
        return (
            user_score
            + f"points\n({streak} in a row) {mayori_emote}You are a Chad! \n{top_emote}streak: {longest_streak}"
        )

