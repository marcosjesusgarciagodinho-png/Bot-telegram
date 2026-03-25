import os
import logging
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_USERNAME = "operin_bot"

cliente_ia = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO)

historiales = {}

def clave_conversacion(update: Update):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == ChatType.PRIVATE:
        return f"privado:{user.id}"
    else:
        return f"grupo:{chat.id}:{user.id}"

def debe_responder_en_grupo(update: Update):
    mensaje = update.effective_message
    if not mensaje or not mensaje.text:
        return False

    texto = mensaje.text.lower()

    if mensaje.reply_to_message and mensaje.reply_to_message.from_user:
        if mensaje.reply_to_message.from_user.username == BOT_USERNAME:
            return True

    if f"@{BOT_USERNAME.lower()}" in texto:
        return True

    return False

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.effective_message
    chat = update.effective_chat

    if not mensaje or not mensaje.text:
        return

    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if not debe_responder_en_grupo(update):
            return

    usuario_id = clave_conversacion(update)
    mensaje_usuario = mensaje.text.strip().replace(f"@{BOT_USERNAME}", "").strip()

    if usuario_id not in historiales:
        historiales[usuario_id] = []

    historiales[usuario_id].append({
        "role": "user",
        "content": mensaje_usuario
    })

    historiales[usuario_id] = historiales[usuario_id][-10:]

    respuesta = cliente_ia.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente útil de una fábrica. Respondes siempre en español, claro y práctico."
            }
        ] + historiales[usuario_id]
    )

    texto_respuesta = respuesta.choices[0].message.content

    historiales[usuario_id].append({
        "role": "assistant",
        "content": texto_respuesta
    })

    await mensaje.reply_text(texto_respuesta)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
app.run_polling(drop_pending_updates=True)
