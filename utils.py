from functools import wraps
import os
from telegram import Update
from telegram.ext import CallbackContext

def authenticated(handler):
    @wraps
    async def handler_with_auth(update: Update, context: CallbackContext):
        admin_id = os.environ.get("ADMIN_ID")
        if not admin_id or not update.message:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Something went wrong.",
            )
        elif update.message.from_user != admin_id:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You are not an admin.",
            )
        else:
            return await handler(update, context)
    return handler_with_auth
