import os, re, random, asyncio
from fastapi import FastAPI, Request, Response, Header
from telegram import Bot, Update
from telegram.constants import ParseMode

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
if not BOT_TOKEN:
    raise RuntimeError("Set BOT_TOKEN env")

bot = Bot(BOT_TOKEN)
app = FastAPI()
MENTION = re.compile(r"@[\w_]+")

# список фраз для "пролога"
PHRASES = [
    "Запускаю алгоритм случайного выбора… шестерёнки крутятся.",
    "Шепчу имена в шляпу судьбы — сейчас вытяну...",
    "Перемешиваю данные в подпрограмме рандомизации…",
    "Вглядываюсь в хрустальный шар… вижу имя, всплывающее из тумана...",
    "Формирую список участников, запускаю генератор случайных чисел...",
    "Заглядываю в бездну случайности — кто там вспыхнет первым?",
    "Заряд энергии пошёл в контур, искры складываются в результат...",
    "Открываю скрытый регистр случайностей…",
    "Свеча мерцает, а тени шепчут имя победителя...",
    "Подбрасываю кинжал судьбы — куда укажет, того и выберет...",
    "Ветер перемешал имена, осталось выхватить одно из потока...",
    "Инопланетный алгоритм выбора активирован. Контакта ждите через секунду.",
    "Колода карт судьбы раскрыта, рука сама тянется вытянуть одну...",
    "Дым от заклинания окутал список имён, одно начинает проступать яснее...",
    "Система подбрасывает виртуальную монету, результат почти готов...",
    "Хрустальный шар светится всё ярче, очертания становятся заметнее...",
    "Оракул судьбы перелистывает страницы, палец замирает на одной...",
    "Звёздная карта оживает, линии соединяются в фигуру победителя...",
    "Тени в углах комнаты переговариваются и указывают на кого-то...",
    "Принтер выплюнул отчёт, и на последней странице жирным выделено одно имя...",
    "Сигнал отправлен в далёкую галактику, ответ возвращается в виде одного слова...",
    "Черная дыра втянула список имён и выплюнула лишь одно...",
    "Космический шаттл сбросил капсулу, и внутри оказался результат...",
    "Бабушка во дворе перемешала карточки и достала одну из кармана...",
    "Голубь на проводе повернул голову и клюнул в нужное направление...",
    "Чайник закипел, пар нарисовал имя на стекле...",
    "Стул заскрипел так, будто шепнул имя победителя...",
    "Лифт остановился между этажами и высветил буквы на табло..."

]

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

@app.get("/")
async def root():
    return {"ok": True}

async def send_with_delay(chat_id, reply_to_id, ppl):
    await asyncio.sleep(10)  # задержка 10 сек
    winner = random.choice(ppl)
    await bot.send_message(
        chat_id,
        f"🎲 наш прекрасный и очень случайный победитель: {winner}",
        reply_to_message_id=reply_to_id,
        parse_mode=ParseMode.HTML
    )

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

    # первое сообщение (без квадратных скобок)
    intro = random.choice(PHRASES)
    await bot.send_message(
        msg.chat_id,
        f"Информация передана. {intro}",
        reply_to_message_id=msg.message_id,
        parse_mode=ParseMode.HTML
    )

    # второе сообщение с задержкой
    asyncio.create_task(send_with_delay(msg.chat_id, msg.message_id, ppl))

    return Response("ok", 200)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)


