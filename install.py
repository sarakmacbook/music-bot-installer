#!/usr/bin/env python3
"""
Telegram Music Bot - One Click Installer
Interactive setup script for Linux, macOS, and Windows
Fixes PEP 668 externally-managed-environment error by using virtual environment
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
import shutil

class MusicBotInstaller:
    def __init__(self):
        self.os_type = platform.system()
        self.project_dir = Path.cwd()
        
    def print_header(self):
        """Print installer header"""
        print("\n" + "="*60)
        print("🎵 TELEGRAM MUSIC BOT - ONE CLICK INSTALLER 🎵")
        print("="*60)
        print("Download and share music directly in Telegram!\n")
    
    def check_python(self):
        """Check if Python 3.8+ is installed"""
        print("✓ Checking Python version...")
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required. Please upgrade Python.")
            sys.exit(1)
        print(f"✅ Python {sys.version.split()[0]} found\n")
    
    def check_pip(self):
        """Check if pip is installed"""
        print("✓ Checking pip...")
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ pip not found. Please install pip.")
            sys.exit(1)
        print(f"✅ {result.stdout.strip()}\n")
    
    def get_telegram_token(self):
        """Get Telegram bot token from user"""
        print("="*60)
        print("🔐 TELEGRAM BOT TOKEN SETUP")
        print("="*60)
        print("\nTo create a bot token:")
        print("  1. Open Telegram → Search for @BotFather")
        print("  2. Send: /start → /newbot")
        print("  3. Choose a name and username")
        print("  4. Copy your token (123456:ABC-DEF...)\n")
        
        while True:
            token = input("📌 Paste your Telegram Bot Token: ").strip()
            
            if not token:
                print("❌ Token cannot be empty. Try again.\n")
                continue
            
            # Basic validation
            if ":" in token and len(token.split(":")[0]) >= 5:
                print("✅ Token validated!\n")
                return token
            else:
                print("❌ Invalid format. Should be: 123456:ABC-DEF...\n")
    
    def save_token(self, token):
        """Save token to file securely"""
        token_file = self.project_dir / "token.txt"
        
        with open(token_file, 'w') as f:
            f.write(token)
        
        # Set secure permissions on Unix-like systems
        if self.os_type != "Windows":
            os.chmod(token_file, 0o600)
        
        print(f"✅ Token saved to token.txt (secured)\n")
    
    def check_ffmpeg(self):
        """Check if FFmpeg is installed"""
        print("✓ Checking FFmpeg...")
        result = subprocess.run(["ffmpeg", "-version"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("⚠️  FFmpeg not found (required for audio conversion)\n")
            self.install_ffmpeg_instructions()
            return False
        
        version = result.stdout.split('\n')[0]
        print(f"✅ {version}\n")
        return True
    
    def install_ffmpeg_instructions(self):
        """Print FFmpeg installation instructions"""
        print("📍 Install FFmpeg:")
        
        if self.os_type == "Linux":
            print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
            print("  Fedora/RHEL:   sudo dnf install ffmpeg")
        elif self.os_type == "Darwin":
            print("  macOS: brew install ffmpeg")
        elif self.os_type == "Windows":
            print("  Chocolatey: choco install ffmpeg")
            print("  Or download: https://ffmpeg.org/download.html")
        
        response = input("\n⏳ Press Enter when done, or Ctrl+C to exit: ")
    
    def create_virtual_env(self):
        """Create and activate virtual environment"""
        print("✓ Setting up virtual environment...")
        venv_dir = self.project_dir / "venv"
        
        # Create virtual environment
        result = subprocess.run([sys.executable, "-m", "venv", str(venv_dir)],
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to create virtual environment")
            print(f"Error: {result.stderr}")
            return None
        
        print("✅ Virtual environment created\n")
        return venv_dir
    
    def get_venv_python(self, venv_dir):
        """Get the Python executable in the virtual environment"""
        if self.os_type == "Windows":
            return venv_dir / "Scripts" / "python.exe"
        else:
            return venv_dir / "bin" / "python"
    
    def install_dependencies(self, venv_python=None):
        """Install Python dependencies"""
        print("="*60)
        print("📦 INSTALLING PYTHON DEPENDENCIES")
        print("="*60 + "\n")
        
        requirements_file = self.project_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("Creating requirements.txt...")
            self.create_requirements_file()
        
        print("Installing packages...")
        
        # Use venv python if available, otherwise use system python
        if venv_python:
            python_exe = str(venv_python)
        else:
            python_exe = sys.executable
        
        # Upgrade pip first
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"⚠️  Warning: Could not upgrade pip")
        
        # Install requirements
        result = subprocess.run(
            [python_exe, "-m", "pip", "install", "-r", "requirements.txt"],
            capture_output=False
        )
        
        if result.returncode != 0:
            print("❌ Failed to install dependencies")
            sys.exit(1)
        
        print("\n✅ Dependencies installed!\n")
    
    def create_requirements_file(self):
        """Create requirements.txt if it doesn't exist"""
        requirements = """python-telegram-bot==20.0
yt-dlp==2023.12.30
pydub==0.25.1
requests==2.31.0
"""
        with open(self.project_dir / "requirements.txt", 'w') as f:
            f.write(requirements)
    
    def create_bot_file(self):
        """Create music_bot.py if it doesn't exist"""
        bot_file = self.project_dir / "music_bot.py"
        
        if bot_file.exists():
            print("✓ music_bot.py already exists")
            return
        
        print("✓ Creating music_bot.py...")
        
        bot_code = '''#!/usr/bin/env python3
"""Telegram Music Bot - Download and share music in Telegram"""

import logging
import yt_dlp
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
    await update.message.reply_text("⏳ Downloading... Please wait")
    
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
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            audio_file = Path(filename).with_suffix('.mp3')
            
            if not audio_file.exists():
                await update.message.reply_text("❌ Download failed")
                return
            
            file_size = audio_file.stat().st_size
            
            if file_size > MAX_FILE_SIZE:
                audio_file.unlink()
                await update.message.reply_text(f"❌ File too large ({file_size/1024/1024:.1f}MB)")
                return
            
            await update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
            
            with open(audio_file, 'rb') as f:
                await update.message.reply_audio(audio=f, title=audio_file.stem)
            
            logger.info(f"Sent: {audio_file.name}")
            audio_file.unlink()
            
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

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
    
    application.run_polling()

if __name__ == '__main__':
    main()
'''
        
        with open(bot_file, 'w') as f:
            f.write(bot_code)
        
        if self.os_type != "Windows":
            os.chmod(bot_file, 0o755)
    
    def create_directories(self):
        """Create necessary directories"""
        print("✓ Creating directories...")
        downloads_dir = self.project_dir / "downloads"
        downloads_dir.mkdir(exist_ok=True)
        print("✅ Directories ready\n")
    
    def create_startup_script(self, venv_dir):
        """Create startup script for easy bot launching"""
        if self.os_type == "Windows":
            script_path = self.project_dir / "run.bat"
            script_content = """@echo off
cd /d "%~dp0"
call venv\\Scripts\\activate.bat
python music_bot.py
pause
"""
            with open(script_path, 'w') as f:
                f.write(script_content)
        else:
            script_path = self.project_dir / "run.sh"
            script_content = """#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 music_bot.py
"""
            with open(script_path, 'w') as f:
                f.write(script_content)
            # Set executable permissions AFTER writing the file
            os.chmod(script_path, 0o755)
        
        print(f"✓ Created startup script: {script_path.name}")
        return script_path
    
    def print_completion(self):
        """Print completion message"""
        print("\n" + "="*60)
        print("✅ INSTALLATION COMPLETE!")
        print("="*60)
        print("\n🚀 TO START YOUR BOT:\n")
        
        if self.os_type == "Windows":
            print("   Option 1: Double-click run.bat")
            print("   Option 2: Run in terminal:")
            print("     venv\\Scripts\\activate.bat && python music_bot.py\n")
        else:
            print("   Option 1: ./run.sh")
            print("   Option 2: Run in terminal:")
            print("     source venv/bin/activate && python3 music_bot.py\n")
        
        print("="*60)
        print("📝 IMPORTANT:")
        print("  • Keep token.txt safe - never share it")
        print("  • Bot will run and listen for messages")
        print("  • Press Ctrl+C to stop")
        print("\n📚 COMMANDS:")
        print("  /start - Welcome message")
        print("  /help  - Help & platforms")
        print("  /clear - Delete files")
        print("\n🔗 SUPPORTED:")
        print("  • YouTube, SoundCloud, Spotify")
        print("  • TikTok, Instagram, Twitter/X")
        print("  • And 100+ more platforms!")
        print("\n🎵 Happy listening!")
        print("="*60 + "\n")
    
    def run(self):
        """Run the complete installation"""
        self.print_header()
        
        # Check system requirements
        self.check_python()
        self.check_pip()
        
        # Get token from user
        token = self.get_telegram_token()
        self.save_token(token)
        
        # Check FFmpeg
        print("="*60)
        print("🔍 CHECKING SYSTEM DEPENDENCIES")
        print("="*60 + "\n")
        ffmpeg_ok = self.check_ffmpeg()
        
        if not ffmpeg_ok:
            print("⚠️  Continuing without FFmpeg (may cause issues)\n")
        
        # Create virtual environment
        print("="*60)
        print("🐍 SETTING UP PYTHON VIRTUAL ENVIRONMENT")
        print("="*60 + "\n")
        venv_dir = self.create_virtual_env()
        venv_python = self.get_venv_python(venv_dir) if venv_dir else None
        
        # Create bot files
        self.create_bot_file()
        self.create_directories()
        
        # Install dependencies in virtual environment
        self.install_dependencies(venv_python)
        
        # Create startup script
        print("="*60)
        print("📝 CREATING STARTUP SCRIPT")
        print("="*60 + "\n")
        if venv_dir:
            try:
                self.create_startup_script(venv_dir)
                print("✅ Startup script created successfully\n")
            except Exception as e:
                print(f"⚠️  Warning: Could not create startup script: {e}\n")
        
        # Show completion message
        self.print_completion()


if __name__ == "__main__":
    installer = MusicBotInstaller()
    try:
        installer.run()
    except KeyboardInterrupt:
        print("\n\n❌ Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
