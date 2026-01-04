# ==============================================================================
# channelplay.py - Channel Play Mode Configuration
# ==============================================================================
# This plugin enables playing music in linked channels instead of the group voice chat.
# Useful for groups with linked channels.
#
# Commands:
# - /channelplay linked - Enable for linked channel
# - /channelplay <channel_id> - Enable for specific channel
# - /channelplay disable - Disable channel play mode
#
# Requirements:
# - User must be admin
# - Bot must be admin in the channel
# - For "linked" mode, channel must be linked to the group
# ==============================================================================

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import Message

from HasiiMusic import app, config, db


@app.on_message(filters.command(["channelplay"]) & filters.group & ~app.bl_users)
async def channelplay_command(_, m: Message):
    """Enable or disable channel play mode."""
    # Check if user is admin
    member = await app.get_chat_member(m.chat.id, m.from_user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await m.reply_text("❌ ᴏɴʟʏ ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.")

    if len(m.command) < 2:
        return await m.reply_text(
            f"{m.chat.title} ɪᴄɪɴ ᴋᴀɴᴀʟ ᴏʏɴᴀᴛᴍᴀ ᴀʏᴀʀʟᴀʀɪ\n\n"
            "ʙᴀɢʟᴀɴᴛɪʟɪ ᴋᴀɴᴀʟ ɪᴄɪɴ ᴀᴋᴛɪꜰ ᴇᴛᴍᴇᴋ:\n"
            "`/channelplay linked`\n\n"
            "ʜᴇʀʜᴀɴɢɪ ʙɪʀ ᴋᴀɴᴀʟ ɪᴄɪɴ ᴀᴋᴛɪꜰ ᴇᴛᴍᴇᴋ:\n"
            "`/channelplay [kanal_id]`\n\n"
            "ᴋᴀɴᴀʟ ᴏʏɴᴀᴛᴍᴀʏɪ ᴅᴇᴠʀᴇ ᴅɪꜱɪ ʙɪʀᴀᴋᴍᴀᴋ:\n"
            "`/channelplay disable`"
        )

    query = m.text.split(None, 1)[1].strip()

    # Disable channel play
    if query.lower() == "disable":
        await db.set_cmode(m.chat.id, None)
        return await m.reply_text("✅ ᴄʜᴀɴɴᴇʟ ᴘʟᴀʏ ᴅɪꜱᴀʙʟᴇᴅ.")

    # Enable for linked channel
    elif query.lower() == "linked":
        chat = await app.get_chat(m.chat.id)
        if chat.linked_chat:
            channel_id = chat.linked_chat.id
            await db.set_cmode(m.chat.id, channel_id)
            return await m.reply_text(
                f"✅ ᴋᴀɴᴀʟ ᴏʏɴᴀᴛᴍᴀ ᴀᴋᴛɪꜰ: {chat.linked_chat.title}\n"
                f"ᴋᴀɴᴀʟ ɪᴅ: `{chat.linked_chat.id}`"
            )
        else:
         return await m.reply_text("❌ ʙᴜ ꜱᴏʜʙᴇᴛɪɴ ʙᴀɢʟᴀɴᴛɪʟɪ ʙɪʀ ᴋᴀɴᴀʟɪ ʏᴏᴋᴛᴜʀ.")

    # Enable for specific channel
    else:
        # Handle numeric channel IDs
        if query.lstrip("-").isdigit():
            channel_id = int(query)
        else:
            channel_id = query  # Username or invite link

        try:
            chat = await app.get_chat(channel_id)
        except Exception as e:
            return await m.reply_text(
                f"❌ ᴋᴀɴᴀʟ ᴀʟɪɴᴀᴍᴀᴅɪ.\n\n"
                f"ʜᴀᴛᴀ: `{type(e).__name__}`\n\n"
                "ʙᴏᴛ'ᴜ ᴋᴀɴᴀʟᴅᴀ ʏᴏɴᴇᴛɪᴄɪ ᴏʟᴀʀᴀᴋ ᴇᴋʟᴇᴅɪɢɪɴɪᴢᴅᴇɴ ᴠᴇ ʏᴇᴛᴋɪʟᴇɴᴅɪʀᴅɪɢɪɴɪᴢᴅᴇɴ ᴇᴍɪɴ ᴏʟᴜɴ.\n\n"
                "ɴᴜᴍᴇʀɪᴋ ɪᴅ'ʟᴇʀ ɪᴄɪɴ: `-100` ᴏɴ ᴇᴋɪ ɪʟᴇ ᴛᴀᴍ ɪᴅ'ʏɪ ᴋᴜʟʟᴀɴɪɴ\n"
                "ᴏʀɴᴇᴋ: `/channelplay -1001234567890`"
            )

        if chat.type != ChatType.CHANNEL:
           return await m.reply_text("❌ ꜱᴀᴅᴇᴄᴇ ᴋᴀɴᴀʟʟᴀʀ ᴅᴇꜱᴛᴇᴋʟᴇɴɪʀ.")

        # Check if user is owner of the channel
        owner_username = None
        owner_id = None
        try:
            async for user in app.get_chat_members(
                chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if user.status == ChatMemberStatus.OWNER:
                    owner_username = user.user.username or "Unknown"
                    owner_id = user.user.id
                    break
        except Exception as e:
            return await m.reply_text(
                f"❌ ᴋᴀɴᴀʟ ʏᴏɴᴇᴛɪᴄɪʟᴇʀɪ ᴀʟɪɴᴀᴍᴀᴅɪ.\n\n"
                f"ʜᴀᴛᴀ: `{type(e).__name__}`\n\n"
                "ʙᴏᴛ'ᴜɴ ᴋᴀɴᴀʟᴅᴀ ʏᴏɴᴇᴛɪᴄɪ ᴏʟᴅᴜɢᴜɴᴅᴀɴ ᴇᴍɪɴ ᴏʟᴜɴ."
            )

        if not owner_id:
            return await m.reply_text(
                "❌ ᴋᴀɴᴀʟ ꜱᴀʜɪʙɪ ʙᴜʟᴜɴᴀᴍᴀᴅɪ.\n\n"
                "ʙᴏᴛ'ᴜɴ ᴋᴀɴᴀʟ ʏᴏɴᴇᴛɪᴄɪʟᴇʀɪɴɪ ɢᴏʀᴍᴇ ɪᴢɴɪɴɪɴ ᴏʟᴅᴜɢᴜɴᴅᴀɴ ᴇᴍɪɴ ᴏʟᴜɴ."
            )

        if owner_id != m.from_user.id:
            return await m.reply_text(
                f"❌ ʙᴜ ɢʀᴜʙᴜ ʙᴜ ᴋᴀɴᴀʟᴀ ʙᴀɢʟᴀᴍᴀᴋ ɪᴄɪɴ {chat.title} ᴋᴀɴᴀʟɪɴɪɴ ꜱᴀʜɪʙɪ ᴏʟᴍᴀɴɪᴢ ɢᴇʀᴇᴋɪʀ.\n\n"
                f"ᴋᴀɴᴀʟ ꜱᴀʜɪʙɪ: @{owner_username}\n\n"
                "ʏᴀ ᴅᴀ, ꜱᴏʜʙᴇᴛɪɴɪᴢɪɴ ʙᴀɢʟᴀɴᴛɪʟɪ ᴋᴀɴᴀʟɪɴɪ ᴠᴇ `/channelplay linked` ɪʟᴇ ʙᴀɢʟᴀɴᴛɪʟᴀʙɪʟɪʀꜱɪɴɪᴢ"
            )

        await db.set_cmode(m.chat.id, chat.id)
        return await m.reply_text(
            f"✅ ᴋᴀɴᴀʟ ᴏʏɴᴀᴛᴍᴀ ᴀᴋᴛɪꜰ: {chat.title}\n"
            f"ᴋᴀɴᴀʟ ɪᴅ: `{chat.id}`"
        )