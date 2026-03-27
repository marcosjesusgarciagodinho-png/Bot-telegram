import os
import logging
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from groq import Groq

# Logs
logging.basicConfig(level=logging.INFO)

# Variables de entorno
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
BOT_USERNAME = "operin_bot"

# 🔍 DEBUG (esto es clave ahora)
print("TELEGRAM_TOKEN existe:", bool(TELEGRAM_TOKEN))
print("GROQ_API_KEY existe:", bool(GROQ_API_KEY))
print("BOT_USERNAME:", BOT_USERNAME)

if not TELEGRAM_TOKEN:
    raise ValueError("❌ Falta TELEGRAM_TOKEN en Railway")

if not GROQ_API_KEY:
    raise ValueError("❌ Falta GROQ_API_KEY en Railway")

# Cliente IA
cliente_ia = Groq(api_key=GROQ_API_KEY)

# Memoria
historiales = {}

# Clave conversación
def clave_conversacion(update: Update):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == ChatType.PRIVATE:
        return f"privado:{user.id}"
    else:
        return f"grupo:{chat.id}:{user.id}"

# Decide si responde en grupo
def debe_responder_en_grupo(update: Update):
    mensaje = update.effective_message
    if not mensaje or not mensaje.text:
        return False

    texto = mensaje.text.lower()

    # Si responde a un mensaje del bot
    if mensaje.reply_to_message and mensaje.reply_to_message.from_user:
        if mensaje.reply_to_message.from_user.username == BOT_USERNAME:
            return True

    # Si menciona al bot
    if f"@{BOT_USERNAME.lower()}" in texto:
        return True

    return False

# Función principal
async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.effective_message
    chat = update.effective_chat

    if not mensaje or not mensaje.text:
        return

    # En grupos solo responde si le llaman
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if not debe_responder_en_grupo(update):
            return

    usuario_id = clave_conversacion(update)

    mensaje_usuario = mensaje.text.replace(f"@{BOT_USERNAME}", "").strip()

    if usuario_id not in historiales:
        historiales[usuario_id] = []

    historiales[usuario_id].append({
        "role": "user",
        "content": mensaje_usuario
    })

    # Limitar memoria
    historiales[usuario_id] = historiales[usuario_id][-10:]

    respuesta = cliente_ia.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente útil de una fábrica. Respondes siempre en español, de forma clara, breve y práctica."
            }
        ] + historiales[usuario_id]
    )

    texto_respuesta = respuesta.choices[0].message.content

    historiales[usuario_id].append({
        "role": "assistant",
        "content": texto_respuesta
    })

    await mensaje.reply_text(texto_respuesta)

# Arranque
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, responder))

print("🤖 Bot arrancado correctamente...")
app.run_polling()
