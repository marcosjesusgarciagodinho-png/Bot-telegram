import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

cliente_ia = Groq(api_key=GROQ_API_KEY)

logging.basicConfig(level=logging.INFO)

historiales = {}

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usuario_id = update.message.from_user.id
    mensaje_usuario = update.message.text

    if usuario_id not in historiales:
        historiales[usuario_id] = []

    historiales[usuario_id].append({
        "role": "user",
        "content": mensaje_usuario
    })

    respuesta = cliente_ia.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente útil del equipo de trabajo. Respondes siempre en español, de forma clara y concisa."
            }
        ] + historiales[usuario_id]
    )

    texto_respuesta = respuesta.choices[0].message.content

    historiales[usuario_id].append({
        "role": "assistant",
        "content": texto_respuesta
    })

    await update.message.reply_text(texto_respuesta)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))
app.run_polling()
