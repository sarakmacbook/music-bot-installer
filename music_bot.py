#!/usr/bin/env python3
"""Telegram Music Bot - Download and share music in Telegram"""

import logging
import yt_dlp
import time
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("""
🎵 *Welcome to Telegram Music Bot!* 🎵

I can download music from YouTube and other platforms.

*How to use:*
1️⃣ Send me a YouTube link
2️⃣ I'll download the audio
3️⃣ You'll receive the MP3 file

*Commands:*
/start - Show this message
/help - Show help information
/clear - Clear downloaded files

Just paste a link and I'll do the rest! 🎼
    """, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("""
🎵 *Music Bot Help* 🎵

*Supported Platforms:*
• YouTube, YouTube Music
• SoundCloud, Spotify
• TikTok, Instagram, Twitter/X
• And 100+ more!

*Commands:*
/start - Welcome message
/help - This message
/clear - Delete downloaded files

Just send a link! 📨
    """, parse_mode='Markdown')

async def clear_downloads(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        count = 0
        for file in DOWNLOADS_DIR.glob("*"):
            if file.is_file():
                file.unlink()
                count += 1
        await update.message.reply_text(f"✅ Cleared {count} files!")
    except Exception as e:
        logger.error(f"Error clearing files: {e}")
        await update.message.reply_text("❌ Error clearing files")

async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text("❌ Please send a valid link")
        return
    
    await update.message.chat.send_action(ChatAction.TYPING)
    await update.message.reply_text("⏳ Downloading... Please wait (this may take 1-2 minutes)")
    
    try:
        output_template = str(DOWNLOADS_DIR / "%(title)s.%(ext)s")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_template,
            'quiet': False,
            'socket_timeout': 30,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            },
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android', 'tv'],
                    'player_skip_download_pages': True,
                    'skip_unavailable_videos': True,
                }
            },
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'youtube_include_dash_manifest': False,
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            audio_file = Path(filename).with_suffix('.mp3')
            
            if not audio_file.exists():
                await update.message.reply_text("❌ Download failed - file not created")
                return
            
            file_size = audio_file.stat().st_size
            
            if file_size > MAX_FILE_SIZE:
                audio_file.unlink()
                await update.message.reply_text(f"❌ File too large ({file_size/1024/1024:.1f}MB). Max: 50MB")
                return
            
            await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
            
            with open(audio_file, 'rb') as f:
                await update.message.reply_audio(audio=f, title=audio_file.stem)
            
            logger.info(f"✅ Sent: {audio_file.name}")
            audio_file.unlink()
            
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download Error: {e}")
        error_msg = str(e)[:150]
        
        # Handle specific YouTube blocking errors
        if any(phrase in error_msg for phrase in ["Sign in to confirm", "blocked", "403", "429", "too many requests"]):
            await update.message.reply_text(
                "❌ YouTube is temporarily blocking requests.\n\n"
                "*Solutions to try:*\n"
                "1️⃣ Wait 5-10 minutes and try again\n"
                "2️⃣ Try a different video\n"
                "3️⃣ Use a playlist or channel link instead\n"
                "4️⃣ Check if the video is public/available"
            )
        else:
            await update.message.reply_text(f"❌ Download failed: {error_msg}")
    
    except Exception as e:
        logger.error(f"Error: {e}")
        error_msg = str(e)[:150]
        await update.message.reply_text(f"❌ Error: {error_msg}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    token_file = Path("token.txt")
    
    if not token_file.exists():
        print("❌ token.txt not found! Run the installer first.")
        return
    
    with open(token_file, 'r') as f:
        token = f.read().strip()
    
    if not token:
        print("❌ Token is empty!")
        return
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_downloads))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_music))
    application.add_error_handler(error_handler)
    
    print("🎵 Music Bot is running...")
    print("Press Ctrl+C to stop")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped gracefully")

if __name__ == '__main__':
    main()
