import os, re, random
from fastapi import FastAPI, Request, Response, Header
from telegram import Bot, Update
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")  # можно не задавать
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN env")

bot = Bot(BOT_TOKEN)
app = FastAPI()
MENTION = re.compile(r"@[\w_]+")

def extract_participants(msg):
    text = (msg.text or "").strip()
    out = set(MENTION.findall(text))
    for ent in (msg.entities or []):
        if ent.type == "mention":
            out.add(text[ent.offset: ent.offset + ent.length])
        elif ent.type == "text_mention" and ent.user and ent.user.username:
            out.add(f"@{ent.user.username}")
    if msg.reply_to_message and msg.reply_to_message.text:
        out.update(MENTION.findall(msg.reply_to_message.text))
    return list(out)

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/webhook")
async def webhook(request: Request, x_telegram_bot_api_secret_token: str | None = Header(None)):
    if WEBHOOK_SECRET and x_telegram_bot_api_secret_token != WEBHOOK_SECRET:
        return Response("forbidden", 200)

    data = await request.json()
    upd = Update.de_json(data, bot)
    msg = getattr(upd, "message", None)
    if not msg or not msg.text:
        return Response("ok", 200)
    if not msg.text.lower().startswith("/random"):
        return Response("ok", 200)

    ppl = extract_participants(msg)
    if not ppl:
        await bot.send_message(
            msg.chat_id,
            "❌ Укажи участников: <code>/random @user1 @user2 …</code>",
            reply_to_message_id=msg.message_id,
            parse_mode=ParseMode.HTML
        )
        return Response("ok", 200)

    winner = random.choice(ppl)
    await bot.send_message(
        msg.chat_id,
        f"🎲 Случайный выбор: <b>{winner}</b>\nУчастники: {', '.join(ppl)}",
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.HTML
    )
    return Response("ok", 200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
