import os
import psycopg2
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

MENU = 0
AGREGAR_MATERIA = 1


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def crear_usuario_si_no_existe(telegram_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cur.fetchone()

    if user is None:
        cur.execute(
            "INSERT INTO users (telegram_id) VALUES (%s) RETURNING id",
            (telegram_id,),
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    else:
        user_id = user[0]

    cur.close()
    conn.close()
    return user_id


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id
    crear_usuario_si_no_existe(telegram_id)

    keyboard = [["📚 Escuela"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Bienvenido. Elige una opción:",
        reply_markup=reply_markup,
    )

    return MENU


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text

    if texto == "📚 Escuela":
        keyboard = [
            ["➕ Agregar materia"],
            ["📖 Ver materias"],
            ["🔙 Volver"],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Menú Escuela:", reply_markup=reply_markup)
        return MENU

    if texto == "➕ Agregar materia":
        await update.message.reply_text("Escribe el nombre de la materia:")
        return AGREGAR_MATERIA

    if texto == "📖 Ver materias":
        telegram_id = update.effective_user.id
        user_id = crear_usuario_si_no_existe(telegram_id)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT nombre FROM materias WHERE user_id = %s ORDER BY nombre ASC",
            (user_id,),
        )
        materias = cur.fetchall()
        cur.close()
        conn.close()

        if not materias:
            await update.message.reply_text("No tienes materias registradas.")
            return MENU

        keyboard = [[m[0]] for m in materias]
        keyboard.append(["🔙 Volver"])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            "Selecciona una materia:",
            reply_markup=reply_markup,
        )

        return MENU

    if texto == "🔙 Volver":
        return await start(update, context)

    await update.message.reply_text("Opción no válida.")
    return MENU


async def guardar_materia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text
    telegram_id = update.effective_user.id
    user_id = crear_usuario_si_no_existe(telegram_id)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO materias (user_id, nombre) VALUES (%s, %s)",
        (user_id, nombre),
    )
    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text(f"Materia '{nombre}' agregada correctamente.")
    return await start(update, context)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            AGREGAR_MATERIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_materia)
            ],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)

    print("Bot iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
