# ==============================================================================
# leave.py - Force Leave Command (Sudo Only)
# ==============================================================================
# This plugin allows sudo users to make the bot and assistant leave any chat.
#
# Commands:
# - /leave - Make bot and assistant leave the current chat
#
# Only sudo users can use this command.
# ==============================================================================

from pyrogram import filters, types, errors

from HasiiMusic import app, db, lang


@app.on_message(filters.command(["leave"]) & app.sudo_filter)
@lang.language()
async def _leave(_, m: types.Message):
    """
    Command handler for /leave
    Makes both bot and assistant leave the current chat.
    """
    chat_id = m.chat.id
    chat_name = m.chat.title or "this chat"

    # Send confirmation message
    sent = await m.reply_text(
        f"<blockquote><b>👋 Leaving Chat</b></blockquote>\n\n"
        f"<blockquote>Bot and assistant are leaving <b>{chat_name}</b>...</blockquote>"
    )

    # Try to make assistant leave if it's in the chat
    try:
        client = await db.get_client(chat_id)
        try:
            await client.leave_chat(chat_id)
        except errors.UserNotParticipant:
            # Assistant is not in the chat, skip
            pass
        except Exception as e:
            # Log any other errors but continue with bot leaving
            pass
    except Exception:
        # If getting client fails, just continue with bot leaving
        pass

    # Make bot leave the chat
    try:
        await app.leave_chat(chat_id)
    except Exception as e:
        # If bot can't leave, inform the sudo user
        await sent.edit_text(
            f"<blockquote><b>❌ Error</b></blockquote>\n\n"
            f"<blockquote>Failed to leave chat: {str(e)}</blockquote>"
        )
