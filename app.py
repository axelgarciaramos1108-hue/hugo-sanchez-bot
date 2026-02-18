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
DENTRO_MATERIA = 2
AGREGAR_TAREA = 3


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
    keyboard = [["📚 Escuela"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Bienvenido. Elige una opción:",
        reply_markup=reply_markup,
    )
    return MENU


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    telegram_id = update.effective_user.id
    user_id = crear_usuario_si_no_existe(telegram_id)

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

    # 🔥 Si selecciona una materia
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM materias WHERE user_id = %s AND nombre = %s",
        (user_id, texto),
    )
    materia = cur.fetchone()
    cur.close()
    conn.close()

    if materia:
        context.user_data["materia_id"] = materia[0]
        context.user_data["materia_nombre"] = texto

        keyboard = [
            ["➕ Agregar tarea"],
            ["📋 Ver tareas"],
            ["🔙 Volver a materias"],
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text(
            f"Materia: {texto}",
            reply_markup=reply_markup,
        )
        return DENTRO_MATERIA

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


async def dentro_materia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    materia_id = context.user_data.get("materia_id")
    materia_nombre = context.user_data.get("materia_nombre")

    if texto == "➕ Agregar tarea":
        await update.message.reply_text("Escribe la tarea:")
        return AGREGAR_TAREA

    if texto == "📋 Ver tareas":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT descripcion FROM tareas WHERE materia_id = %s",
            (materia_id,),
        )
        tareas = cur.fetchall()
        cur.close()
        conn.close()

        if not tareas:
            await update.message.reply_text("No hay tareas registradas.")
            return DENTRO_MATERIA

        lista = "\n".join([f"• {t[0]}" for t in tareas])
        await update.message.reply_text(f"Tareas de {materia_nombre}:\n\n{lista}")
        return DENTRO_MATERIA

    if texto == "🔙 Volver a materias":
        return await menu(update, context)

    await update.message.reply_text("Opción no válida.")
    return DENTRO_MATERIA


async def guardar_tarea(update: Update, context: ContextTypes.DEFAULT_TYPE):
    descripcion = update.message.text
    materia_id = context.user_data.get("materia_id")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tareas (materia_id, descripcion) VALUES (%s, %s)",
        (materia_id, descripcion),
    )
    conn.commit()
    cur.close()
    conn.close()

    await update.message.reply_text("Tarea agregada correctamente.")
    return DENTRO_MATERIA


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            AGREGAR_MATERIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_materia)
            ],
            DENTRO_MATERIA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, dentro_materia)
            ],
            AGREGAR_TAREA: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, guardar_tarea)
            ],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)

    print("Bot iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
