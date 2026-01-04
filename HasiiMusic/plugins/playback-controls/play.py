# ==============================================================================
# play.py - Main Play Command Handler
# ==============================================================================
# This is the core plugin that handles all play-related commands:
# - /play <query> - Play audio from YouTube search or URL
# - /playforce - Force play (skip queue and play immediately)
# - /cplay - Play in connected channel
# 
# Supports:
# - YouTube search queries
# - YouTube URLs (videos and playlists)
# - Telegram audio files (via reply)
# - Queue management
# - Channel play mode
# ==============================================================================

from pyrogram import filters
from pyrogram import types
from pyrogram.errors import FloodWait, MessageIdInvalid, MessageDeleteForbidden

from HasiiMusic import tune, app, config, db, lang, queue, tg, yt
from HasiiMusic.helpers import buttons, utils
from HasiiMusic.helpers._play import checkUB
import asyncio


async def safe_edit(message, text, **kwargs):
    """
    Safely edit a message with proper error handling for common Telegram API errors.
    
    Args:
        message: The message object to edit
        text: New text content
        **kwargs: Additional arguments for edit_text
        
    Returns:
        True if successful, False otherwise
    """
    try:
        await message.edit_text(text, **kwargs)
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        try:
            await message.edit_text(text, **kwargs)
            return True
        except (MessageIdInvalid, MessageDeleteForbidden, Exception):
            return False
    except (MessageIdInvalid, MessageDeleteForbidden):
        # Message was deleted or became invalid - this is expected
        return False
    except Exception:
        # Other errors - log but don't crash
        return False


def playlist_to_queue(chat_id: int, tracks: list) -> str:
    """
    Add multiple tracks to queue and format them as a message.
    
    Args:
        chat_id: The chat ID where queue is managed
        tracks: List of Track objects to add
        
    Returns:
        Formatted string listing all added tracks
    """
    text = "<blockquote expandable>"
    for track in tracks:
        pos = queue.add(chat_id, track)  # Add track to queue (returns 0-based index)
        text += f"<b>{pos}.</b> {track.title}\n"  # Show actual queue position
    text = text[:1948] + "</blockquote>"  # Limit message length
    return text

@app.on_message(
    filters.command(["play", "vplay", "playforce", "cplay", "cplayforce"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
@checkUB
async def play_hndlr(
    _,
    m: types.Message,
    force: bool = False,
    url: str = None,
    cplay: bool = False,
    video: bool = False,
) -> None:
    # Detect if video mode is requested (only /vplay command)
    command = m.command[0].lower()
    video = (command == 'vplay')
    
    # Restrict video playback to sudo users only
    if video and m.from_user.id not in app.sudoers:
        return await m.reply_text(m.lang["vplay_sudo_only"])
    
    # Handle channel play mode
    chat_id = m.chat.id
    if cplay:
        channel_id = await db.get_cmode(m.chat.id)
       if channel_id is None:
            return await m.reply_text(
                "❌ **Kanal oynatma etkin değil.**\n\n"
                "**Bağlantılı kanal için etkinleştirmek:**\n"
                "`/channelplay linked`\n\n"
                "**Herhangi bir kanal için etkinleştirmek:**\n"
                "`/channelplay [kanal_id]`"
            )
        try:
            chat = await app.get_chat(channel_id)
            chat_id = channel_id
        except:
            await db.set_cmode(m.chat.id, None)
            return await m.reply_text(
                "❌ **Kanal alınamadı.**\n\n"
                "Kanaldan yönetici olduğumdan ve kanal oynatmanın doğru ayarlandığından emin olun."
            )

    try:
        sent = await m.reply_text(m.lang["play_searching"])
    except FloodWait as e:
        await asyncio.sleep(e.value)
        sent = await m.reply_text(m.lang["play_searching"])
    except Exception:
        return  # If we can't even send initial message, abort
    
    mention = m.from_user.mention
    media = tg.get_media(m.reply_to_message) if m.reply_to_message else None
    tracks = []
    file = None  # Initialize file variable

    # Check media first (Telegram files) before URL extraction
    if media:
        setattr(sent, "lang", m.lang)
        file = await tg.download(m.reply_to_message, sent)

    elif url:
        if "playlist" in url:
            await safe_edit(sent, m.lang["playlist_fetch"])
            try:
                tracks = await yt.playlist(
                    config.PLAYLIST_LIMIT, mention, url, False
                )
            except Exception as e:
                await safe_edit(
                    sent,
                    f"<blockquote>❌ ᴏʏɴᴀᴛᴍᴀ ʟɪꜱᴛᴇꜱɪ ᴀʟɪɴᴀᴍᴀᴅɪ.\n\n"
                    f"ʏᴏᴜᴛᴜʙᴇ ᴏʏɴᴀᴛᴍᴀ ʟɪꜱᴛᴇʟᴇʀɪ ᴍᴇᴠᴄᴜᴛᴛᴀ ꜱᴏʀᴜɴ ʏᴀꜱᴀᴍᴀᴋᴛᴀᴅɪʀ. "
                    f"ʟᴜᴛꜰᴇɴ ʙᴜɴᴜɴ ʏᴇʀɪɴᴇ ᴛᴇᴋ ᴛᴇᴋ ꜱᴀʀᴋɪʟᴀʀɪ ᴏʏɴᴀᴛᴍᴀʏɪ ᴅᴇɴᴇʏɪɴ.</blockquote>"
                )
                return

            if not tracks:
                await safe_edit(sent, m.lang["playlist_error"])
                return

            file = tracks[0]
            tracks.remove(file)
            file.message_id = sent.id
        else:
            file = await yt.search(url, sent.id, video=video)

        if not file:
            await safe_edit(
                sent,
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )
            return

    elif len(m.command) >= 2:
        query = " ".join(m.command[1:])
        file = await yt.search(query, sent.id, video=video)
        if not file:
            await safe_edit(
                sent,
                m.lang["play_not_found"].format(config.SUPPORT_CHAT)
            )
            return

    if not file:
        return

    # Skip duration check for live streams
    if not file.is_live and file.duration_sec > config.DURATION_LIMIT:
        await safe_edit(
            sent,
            m.lang["play_duration_limit"].format(config.DURATION_LIMIT // 60)
        )
        return

    if await db.is_logger():
        await utils.play_log(m, file.title, file.duration)

    file.user = mention
    if force:
        queue.force_add(chat_id, file)
    else:
        position = queue.add(chat_id, file)  # Returns 0-based index

        if await db.get_call(chat_id):
            # When call is active, position 0 is currently playing
            # So actual waiting position is: position (e.g., 1st waiting = index 1)
            # Display as 1-based for users: index 1 → "1st in queue"
            await safe_edit(
                sent,
                m.lang["play_queued"].format(
                    position,  # Shows waiting position: 1, 2, 3...
                    file.url,
                    file.title,
                    file.duration,
                    m.from_user.mention,
                ),
                reply_markup=buttons.play_queued(
                    chat_id, file.id, m.lang["play_now"]
                ),
            )
            if tracks:
                added = playlist_to_queue(chat_id, tracks)
                await app.send_message(
                    chat_id=m.chat.id,
                    text=m.lang["playlist_queued"].format(len(tracks)) + added,
                )
            return

    if not file.file_path:
        file.file_path = await yt.download(file.id, video=video, is_live=file.is_live)
        if not file.file_path:
         await safe_edit(
                sent,
                "❌ **Medya indirilemedi.**\n\n"
                "**Olası sebepler:**\n"
                "• YouTube bot aktivitesi tespit etti (çerezleri güncelleyin)\n"
                "• Video bölgeye özel veya özel\n"
                "• Yaş kısıtlamalı içerik (çerez gerektirir)\n\n"
                f"**Destek:** {config.SUPPORT_CHAT}"
            )

    # file.video varsa (Telegram dosyaları) onu kullan, yoksa komut video bayrağını kullan
    is_video = file.video if hasattr(file, 'video') and file.video else video
    
    try:
        await tune.play_media(chat_id=chat_id, message=sent, media=file, video=is_video)
    except Exception as e:
        error_msg = str(e)
        if "bot" in error_msg.lower() or "sign in" in error_msg.lower():
            await safe_edit(
                sent,
                "❌ **YouTube bot tespiti tetiklendi.**\n\n"
                "**Çözüm:**\n"
                "• `HasiiMusic/cookies/` klasöründeki YouTube çerezlerini güncelleyin\n"
                "• Tekrar denemeden önce birkaç dakika bekleyin\n"
                "• Kesintisiz müzik için /radio'yu deneyin\n\n"
                f"**Destek:** {config.SUPPORT_CHAT}"
            )
        else:
            await safe_edit(
                sent,
                f"❌ **Oynatma hatası:**\n{error_msg}\n\n"
                f"**Destek:** {config.SUPPORT_CHAT}"
            )
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
                
            )
        return
    if not tracks:
        return
    added = playlist_to_queue(chat_id, tracks)
    await app.send_message(
        chat_id=m.chat.id,
        text=m.lang["playlist_queued"].format(len(tracks)) + added,
    )