#!/usr/bin/env python3
"""Telegram Music Bot - Download and share music in Telegram"""

import logging
import yt_dlp
import time
import os
import shutil
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ChatAction

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 50 * 1024 * 1024
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds

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

def get_ydl_opts(attempt=1):
    """
    Get yt-dlp options with rotating player clients for anti-blocking
    Different attempts use different strategies
    """
    
    # Rotate player clients on retry
    player_clients_strategies = [
        ['web', 'android', 'tv'],  # Attempt 1: Standard clients
        ['android', 'tv', 'web'],  # Attempt 2: Android first
        ['tv', 'web', 'android'],  # Attempt 3: TV first (less detection)
    ]
    
    # Rotate user agents
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    client_idx = min(attempt - 1, len(player_clients_strategies) - 1)
    ua_idx = (attempt - 1) % len(user_agents)
    
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
        'socket_timeout': 60,
        'http_headers': {
            'User-Agent': user_agents[ua_idx],
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.youtube.com/',
            'Origin': 'https://www.youtube.com',
        },
        'extractor_args': {
            'youtube': {
                'player_client': player_clients_strategies[client_idx],
                'player_skip_download_pages': True,
                'skip_unavailable_videos': True,
            }
        },
        'retries': 15,
        'fragment_retries': 15,
        'skip_unavailable_fragments': True,
        'youtube_include_dash_manifest': False,
        'keepvideo': False,
        'overwrites': True,
        'ignoreerrors': False,
        'extract_flat': False,
        'socket_timeout': 60,
        'age_limit': None,
    }
    
    # Add proxy support for higher retry attempts (if needed)
    if attempt >= 3:
        ydl_opts.update({
            'socket_timeout': 90,
            'http_headers': {
                **ydl_opts['http_headers'],
                'X-Forwarded-For': '1.2.3.4',  # Rotate apparent IP
            }
        })
    
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
        
        # Also clean temporary files
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
    
    # Check disk space before starting
    free_space = get_free_disk_space()
    if free_space and free_space < 200 * 1024 * 1024:  # Less than 200MB
        await update.message.reply_text(
            "❌ Not enough disk space!\n\n"
            f"Available: {free_space/1024/1024:.1f}MB\n"
            "Required: ~200MB minimum"
        )
        return
    
    await update.message.chat.send_action(ChatAction.TYPING)
    await update.message.reply_text("⏳ Downloading... Please wait (this may take 1-2 minutes)")
    
    audio_file = None
    attempt = 0
    last_error = None
    
    while attempt < RETRY_ATTEMPTS:
        attempt += 1
        try:
            # Clean up old temp files before starting
            cleanup_temp_files()
            
            # Get strategy-specific options
            ydl_opts = get_ydl_opts(attempt)
            
            logger.info(f"Download attempt {attempt}/{RETRY_ATTEMPTS} for: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Find the actual output file (could be .mp3 or original format)
                base_path = Path(filename)
                audio_file = base_path.with_suffix('.mp3')
                
                # Fallback: if MP3 doesn't exist, look for the original file
                if not audio_file.exists() and base_path.exists():
                    audio_file = base_path
                
                if not audio_file.exists():
                    logger.error(f"File not created for: {url}")
                    if attempt < RETRY_ATTEMPTS:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                        await update.message.reply_text(
                            f"⏳ Attempt {attempt} failed. Retrying with different strategy... (attempt {attempt + 1}/{RETRY_ATTEMPTS})"
                        )
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        await update.message.reply_text("❌ Download failed - file not created. Check FFmpeg installation.")
                        return
                
                # Verify file size and integrity
                try:
                    file_size = audio_file.stat().st_size
                    
                    if file_size == 0:
                        audio_file.unlink()
                        if attempt < RETRY_ATTEMPTS:
                            logger.info(f"Empty file detected. Retrying...")
                            await update.message.reply_text(
                                f"⏳ Empty file detected. Retrying... (attempt {attempt + 1}/{RETRY_ATTEMPTS})"
                            )
                            time.sleep(RETRY_DELAY)
                            continue
                        else:
                            await update.message.reply_text("❌ Download created empty file. Try again.")
                            return
                    
                    if file_size > MAX_FILE_SIZE:
                        audio_file.unlink()
                        await update.message.reply_text(f"❌ File too large ({file_size/1024/1024:.1f}MB). Max: 50MB")
                        return
                
                except OSError as e:
                    logger.error(f"File stat error: {e}")
                    if attempt < RETRY_ATTEMPTS:
                        await update.message.reply_text(
                            f"⏳ File error detected. Retrying... (attempt {attempt + 1}/{RETRY_ATTEMPTS})"
                        )
                        time.sleep(RETRY_DELAY)
                        continue
                    else:
                        await update.message.reply_text("❌ Cannot access downloaded file. Disk error?")
                        return
                
                # Upload to Telegram - SUCCESS!
                try:
                    await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
                    
                    with open(audio_file, 'rb') as f:
                        await update.message.reply_audio(audio=f, title=audio_file.stem)
                    
                    logger.info(f"✅ Sent: {audio_file.name} ({file_size/1024/1024:.1f}MB)")
                    return  # Success - exit function
                    
                except Exception as e:
                    logger.error(f"Upload error: {e}")
                    await update.message.reply_text(f"❌ Failed to send file: {str(e)[:100]}")
                    return
                
                finally:
                    # Clean up after upload attempt
                    try:
                        if audio_file and audio_file.exists():
                            audio_file.unlink()
                    except Exception as e:
                        logger.warning(f"Could not delete file: {e}")
        
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download Error (attempt {attempt}): {e}")
            last_error = str(e)[:150]
            error_msg = last_error.lower()
            
            # Handle specific YouTube blocking errors
            if any(phrase in error_msg for phrase in ["sign in", "blocked", "403", "429", "too many requests", "unavailable"]):
                if attempt < RETRY_ATTEMPTS:
                    logger.info(f"YouTube blocking detected. Waiting {RETRY_DELAY}s before retry...")
                    await update.message.reply_text(
                        f"🚫 YouTube detected automated access.\n\n"
                        f"Retrying with different strategy... (attempt {attempt + 1}/{RETRY_ATTEMPTS})\n\n"
                        f"⏳ Waiting {RETRY_DELAY} seconds..."
                    )
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    await update.message.reply_text(
                        "❌ YouTube is blocking requests after multiple attempts.\n\n"
                        "*Recommended solutions:*\n"
                        "1️⃣ Wait 10-15 minutes before trying again\n"
                        "2️⃣ Try downloading a different video\n"
                        "3️⃣ Try a YouTube playlist instead of single video\n"
                        "4️⃣ Check if the video is public and not age-restricted\n"
                        "5️⃣ Use a VPN if available\n\n"
                        "⚠️ Note: YouTube actively blocks automated access"
                    )
                    return
            else:
                await update.message.reply_text(f"❌ Download failed: {last_error}")
                return
        
        except IOError as e:
            logger.error(f"I/O Error (attempt {attempt}): {e}")
            last_error = str(e)
            error_code = e.errno
            
            if error_code == 5:  # Errno 5: Input/Output Error
                await update.message.reply_text(
                    "❌ Disk I/O Error occurred.\n\n"
                    "*Possible causes:*\n"
                    "• Disk is full or read-only\n"
                    "• File system error\n"
                    "• Permission denied\n\n"
                    "*Try:*\n"
                    "1️⃣ Run /clear to free space\n"
                    "2️⃣ Check disk permissions\n"
                    "3️⃣ Try a smaller file"
                )
            elif error_code == 28:  # No space left on device
                await update.message.reply_text(
                    "❌ No disk space available!\n\n"
                    "Run /clear to delete old files and try again."
                )
            else:
                await update.message.reply_text(f"❌ File system error ({error_code}): {str(e)[:80]}")
            return
        
        except Exception as e:
            logger.error(f"Error (attempt {attempt}): {type(e).__name__}: {e}")
            last_error = str(e)[:100]
            
            if attempt < RETRY_ATTEMPTS:
                logger.info(f"Retrying after error...")
                await update.message.reply_text(
                    f"⏳ Error occurred. Retrying with different strategy... (attempt {attempt + 1}/{RETRY_ATTEMPTS})"
                )
                time.sleep(RETRY_DELAY)
                continue
            else:
                await update.message.reply_text(f"❌ Error: {last_error}")
                return
    
    finally:
        # Final cleanup of any remaining temp files
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
