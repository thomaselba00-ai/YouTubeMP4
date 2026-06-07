import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── CONFIG ──────────────────────────────────────────────────────────────────
BOT_TOKEN = "8878916592:AAFcjBPudiW51LSYiWOY1qWoIgb83Jc9FsA"          # @BotFather token
DOWNLOAD_API = "https://api-rebix.vercel.app/api/ytv"
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def is_youtube_url(text: str) -> bool:
    """Return True if the text looks like a YouTube link."""
    return any(
        domain in text
        for domain in ("youtube.com/watch", "youtu.be/", "youtube.com/shorts/")
    )


def fetch_download_info(url: str) -> dict | None:
    """
    Call the download API and return the results dict, or None on failure.
    Expected response shape:
        { "status": true, "results": { "title", "downloadUrl", "size", "duration", "quality" } }
    """
    try:
        resp = requests.get(DOWNLOAD_API, params={"url": url}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") and data.get("results"):
            return data["results"]
    except Exception as exc:
        logger.error("API error: %s", exc)
    return None


# ─── HANDLERS ────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *YouTube Video Downloader Bot*\n\n"
        "Just send me any YouTube link and I'll give you a direct download link!\n\n"
        "Supported formats:\n"
        "• `https://youtu.be/VIDEO_ID`\n"
        "• `https://youtube.com/watch?v=VIDEO_ID`\n"
        "• `https://youtube.com/shorts/VIDEO_ID`",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "1. Copy a YouTube video link\n"
        "2. Paste it here and send\n"
        "3. Tap the *Download* button!\n\n"
        "That's it — no commands needed.",
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text.strip()

    if not is_youtube_url(text):
        await update.message.reply_text(
            "⚠️ That doesn't look like a YouTube link.\n"
            "Please send a valid YouTube URL (e.g. `https://youtu.be/xxxxx`).",
            parse_mode="Markdown",
        )
        return

    # Let the user know we're working on it
    processing_msg = await update.message.reply_text("⏳ Fetching video info…")

    info = fetch_download_info(text)

    if not info:
        await processing_msg.edit_text(
            "❌ Sorry, I couldn't fetch that video.\n"
            "The link may be private, age-restricted, or the service is temporarily down."
        )
        return

    title    = info.get("title",       "Unknown Title")
    size     = info.get("size",        "N/A")
    duration = info.get("duration",    "N/A")
    quality  = info.get("quality",     "N/A")
    dl_url   = info.get("downloadUrl", "")

    caption = (
        f"🎬 *{title}*\n\n"
        f"⏱ Duration : `{duration}`\n"
        f"📦 Size     : `{size}`\n"
        f"🎥 Quality  : `{quality}`\n"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download Video", url=dl_url)],
    ])

    await processing_msg.delete()
    await update.message.reply_text(
        caption,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled error: %s", context.error, exc_info=context.error)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    token = os.getenv("BOT_TOKEN", BOT_TOKEN)
    if token == "YOUR_BOT_TOKEN_HERE":
        raise ValueError(
            "Set your bot token!\n"
            "  Option 1 — edit BOT_TOKEN in the script\n"
            "  Option 2 — export BOT_TOKEN=<token> before running"
        )

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    logger.info("Bot is running…  Press Ctrl-C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
