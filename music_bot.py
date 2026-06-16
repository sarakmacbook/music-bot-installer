#!/usr/bin/env python3
"""Telegram Music Bot - Download and share music in Telegram"""

import logging
import yt_dlp
import time
import os
import shutil
import subprocess
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024

def get_free_disk_space():
    """Get free disk space in bytes"""
    try:
        stat = shutil.disk_usage(DOWNLOADS_DIR)
        return stat.free
    except Exception as e:
        logger.error(f"Could not check disk space: {e}")
        return None

def cleanup_temp_files():
    """Clean up incomplete/temporary downloads"""
    try:
        temp_patterns = ['*.part', '*.f*', '*.tmp', '*.ytdl']
        for pattern in temp_patterns:
            for file in DOWNLOADS_DIR.glob(pattern):
                try:
                    file.unlink()
                    logger.info(f"Cleaned up: {file.name}")
                except Exception as e:
                    logger.warning(f"Could not remove {file}: {e}")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def get_ydl_opts():
    """Get optimized yt-dlp options to avoid YouTube blocking"""
    
    output_template = str(DOWNLOADS_DIR / "%(title).150s.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
            'nopostoverwrites': False,
        }],
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': False,
        'socket_timeout': 120,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.youtube.com/',
            'Origin': 'https://www.youtube.com',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'tv'],
                'player_skip_download_pages': True,
                'skip_unavailable_videos': True,
                'innertube_client_version': '2.20240101.00.00',
            }
        },
        'retries': 20,
        'fragment_retries': 20,
        'skip_unavailable_fragments': True,
        'youtube_include_dash_manifest': False,
        'youtube_include_hls_manifest': False,
        'keepvideo': False,
        'overwrites': True,
        'ignoreerrors': False,
        'extract_flat': False,
        'age_limit': None,
        'quiet': False,
        'no_warnings': False,
        'progress_hooks': [],
        'http_chunk_size': 10485760,
        'concurrent_fragment_downloads': 4,
        'socket_timeout': 120,
        'connection_timeout': 120,
        'read_timeout': 120,
    }
    
    return ydl_opts

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
                try:
                    file.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"Could not delete {file}: {e}")
        
        cleanup_temp_files()
        await update.message.reply_text(f"✅ Cleared {count} files!")
    except Exception as e:
        logger.error(f"Error clearing files: {e}")
        await update.message.reply_text("❌ Error clearing files")

async def download_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    url = update.message.text.strip()
    
    if not (url.startswith('http://') or url.startswith('https://')):
        await update.message.reply_text("❌ Please send a valid link")
        return
    
    # Check disk space
    free_space = get_free_disk_space()
    if free_space and free_space < 200 * 1024 * 1024:
        await update.message.reply_text(
            "❌ Not enough disk space!\n\n"
            f"Available: {free_space/1024/1024:.1f}MB\n"
            "Required: ~200MB minimum"
        )
        return
    
    await update.message.chat.send_action(ChatAction.TYPING)
    await update.message.reply_text("⏳ Downloading... Please wait (this may take 1-2 minutes)")
    
    audio_file = None
    
    try:
        cleanup_temp_files()
        
        ydl_opts = get_ydl_opts()
        logger.info(f"Starting download for: {url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            base_path = Path(filename)
            audio_file = base_path.with_suffix('.mp3')
            
            if not audio_file.exists() and base_path.exists():
                audio_file = base_path
            
            if not audio_file.exists():
                logger.error(f"File not created for: {url}")
                await update.message.reply_text("❌ Download failed - file not created. Check FFmpeg installation.")
                return
            
            try:
                file_size = audio_file.stat().st_size
                
                if file_size == 0:
                    audio_file.unlink()
                    await update.message.reply_text("❌ Download created empty file. Try again.")
                    return
                
                if file_size > MAX_FILE_SIZE:
                    audio_file.unlink()
                    await update.message.reply_text(f"❌ File too large ({file_size/1024/1024:.1f}MB). Max: 50MB")
                    return
            
            except OSError as e:
                logger.error(f"File stat error: {e}")
                await update.message.reply_text("❌ Cannot access downloaded file. Disk error?")
                return
            
            # Upload to Telegram
            try:
                await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
                
                with open(audio_file, 'rb') as f:
                    await update.message.reply_audio(audio=f, title=audio_file.stem)
                
                logger.info(f"✅ Sent: {audio_file.name} ({file_size/1024/1024:.1f}MB)")
                
            except Exception as e:
                logger.error(f"Upload error: {e}")
                await update.message.reply_text(f"❌ Failed to send file: {str(e)[:100]}")
            
            finally:
                try:
                    if audio_file and audio_file.exists():
                        audio_file.unlink()
                except Exception as e:
                    logger.warning(f"Could not delete file: {e}")
    
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download Error: {e}")
        error_msg = str(e)[:200]
        await update.message.reply_text(f"❌ Download failed:\n{error_msg}")
    
    except IOError as e:
        logger.error(f"I/O Error: {e}")
        error_code = e.errno
        
        if error_code == 5:
            await update.message.reply_text(
                "❌ Disk I/O Error occurred.\n\n"
                "1️⃣ Run /clear to free space\n"
                "2️⃣ Check disk permissions\n"
                "3️⃣ Try a smaller file"
            )
        elif error_code == 28:
            await update.message.reply_text(
                "❌ No disk space available!\n\n"
                "Run /clear to delete old files and try again."
            )
        else:
            await update.message.reply_text(f"❌ File system error ({error_code})")
    
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")
    
    finally:
        cleanup_temp_files()

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
