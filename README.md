# 🎵 Telegram Music Bot - One Click Installer

**The easiest way to set up a Telegram music bot in seconds!**

Zero configuration needed - just run one command and you're done!

> **Fork Notes:** This is an enhanced version with improved error handling, disk space management, and better YouTube blocking recovery.

---

## ⚡ Quick Start (2 Steps)

### Step 1: Clone this fork
```bash
git clone https://github.com/sarakmacbook/music-bot-installer.git
cd music-bot-installer
```

### Step 2: Run the installer
```bash
python3 install.py
```

That's it! The installer will:
- ✅ Check your system
- ✅ Ask for your bot token (from @BotFather)
- ✅ Install all dependencies
- ✅ Create the bot

Then run:
```bash
python3 music_bot.py
```

---

## 🤖 Get Your Bot Token (1 minute)

1. Open **Telegram** → Search for **@BotFather**
2. Send `/newbot`
3. Choose a name and username
4. **Copy the token** it gives you
5. Paste it into the installer

That's it! 🎉

---

## 📋 What You Need

- **Python 3.8+** (usually pre-installed)
- **FFmpeg** (for audio conversion)
- **Internet connection**
- **~200MB disk space** (minimum)

### Install FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
```bash
choco install ffmpeg
```

Or download from [ffmpeg.org](https://ffmpeg.org/download.html)

---

## 🎼 How to Use

Once the bot is running (`python3 music_bot.py`):

1. **Open your bot in Telegram**
2. **Send a music link:**
   ```
   https://www.youtube.com/watch?v=...
   https://soundcloud.com/...
   https://spotify.com/track/...
   ```
3. **Wait for download**
4. **Get your MP3** 🎵

### Bot Commands

- `/start` - Welcome & instructions
- `/help` - Supported platforms
- `/clear` - Delete downloaded files

---

## ✨ Features

🚀 **One-Click Setup** - Fully automated installation  
🎼 **Multi-Platform** - YouTube, SoundCloud, Spotify, TikTok, and 100+ more  
🛡️ **Secure** - Token safely stored, automatic cleanup  
📱 **User-Friendly** - Simple commands, no configuration  
⚡ **Fast** - Instant downloads  
🔧 **Robust** - Enhanced error handling and recovery  

---

## 🆕 What's New in This Fork

This version includes several improvements over the original:

### 🐛 Bug Fixes
- ✅ Fixed YouTube blocking errors with automatic retry logic
- ✅ Fixed I/O errors [Errno 5] with disk space checks
- ✅ Improved error messages and user guidance
- ✅ Better handling of network timeouts

### 🚀 Enhancements
- 📊 Pre-download disk space verification (minimum 200MB required)
- 🧹 Automatic cleanup of temporary/incomplete files
- 🔁 Improved retry logic for failed downloads
- 📝 More detailed error messages with solutions
- 🛡️ Better file integrity checks
- ⏱️ Increased socket timeouts for slow connections

### 📋 Better Error Recovery
When errors occur, users now get:
- Specific error types (YouTube blocking, disk full, I/O errors)
- Actionable solutions (wait, clear cache, check permissions)
- Helpful guidance for resolution

---

## 🐛 Troubleshooting

### "Python not found"
- Install from [python.org](https://www.python.org/downloads/)
- On Ubuntu: `sudo apt-get install python3 python3-pip`

### "FFmpeg not found"
- Run `python3 install.py` again and follow FFmpeg instructions
- Or install manually using commands above

### "ModuleNotFoundError"
- Re-run: `python3 install.py`

### Bot won't start
- Check `token.txt` exists and has valid token
- Try: `python3 music_bot.py`

### Download fails / YouTube blocks request
- Wait 5-10 minutes and try again
- Try a different video
- Run `/clear` to free up disk space
- Check your internet connection
- Ensure FFmpeg is installed: `ffmpeg -version`

### "Disk I/O Error" or "No space left"
- Run `/clear` command in bot to delete old files
- Check disk space: `df -h` (Linux/Mac) or `dir` (Windows)
- Ensure write permissions on downloads folder

---

## 📁 What Gets Created

```
music-bot-installer/
├── install.py           ← Main installer (run this!)
├── music_bot.py        ← The bot (run this to start)
├── token.txt           ← Your secret token (auto-created)
├── requirements.txt    ← Dependencies (auto-created)
├── run.sh / run.bat    ← Startup script (auto-created)
├── stop.sh             ← Stop script (auto-created)
├── downloads/          ← Temp folder (auto-created)
└── README.md           ← This file
```

---

## 🎯 Next Steps

1. Run the installer: `python3 install.py`
2. Follow the prompts
3. Start the bot: `python3 music_bot.py`
4. Open Telegram and send links to your bot!

---

## ⚠️ Important

- **Never share token.txt** - it controls your bot
- Respect copyright and platform terms of service
- Downloaded files are automatically deleted after sending
- Telegram has a 50MB file limit per upload
- Keep at least 200MB free disk space for downloads

---

## 📡 System Requirements & Compatibility

- **Linux:** Ubuntu 18.04+, Debian 10+, Fedora, RHEL
- **macOS:** 10.12+ (Intel & Apple Silicon)
- **Windows:** Windows 10/11

Virtual environment support for PEP 668 compliance ✅

---

## 📞 Support & Links

- **Original Repository:** https://github.com/sarakrim/music-bot-installer
- **This Fork:** https://github.com/sarakmacbook/music-bot-installer
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **yt-dlp Documentation:** https://github.com/yt-dlp/yt-dlp
- **Report Issues:** Create an issue on this repository

---

## 🎵 Enjoy!

Your music bot is ready. Download and share your favorite tracks! 🎉

**Made with ❤️ for music lovers**

---

## 📝 License & Credits

- **Based on:** [sarakrim/music-bot-installer](https://github.com/sarakrim/music-bot-installer)
- **Enhanced by:** sarakmacbook
- **Dependencies:** 
  - [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Download audio
  - [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram API
  - [FFmpeg](https://ffmpeg.org/) - Audio conversion
