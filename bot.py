import asyncio
import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.errors import InviteHashExpired, InviteHashInvalid

# Загружаем переменные окружения из файла .env
load_dotenv(dotenv_path=".env")

# Получаем данные из переменных окружения
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

app = Client("my_account", api_id=api_id, api_hash=api_hash)

# Список для хранения чатов и параметров для каждого чата
user_chats = {}  # {chat_id: {'link': link, 'message': message, 'count': count, 'delay': delay}}

# Переменная для контроля отмены отправки
cancel_sending = False


# Команда для добавления группы по ссылке, сообщения, количества отправок и индивидуальной задержки
async def add_chat_by_link(link, message_text, count, delay):
    try:
        # Присоединяемся к чату по ссылке приглашения
        chat = await app.join_chat(link)
        chat_link = f"https://t.me/{chat.username}" if chat.username else f"Неизвестная группа ({chat.id})"
        user_chats[chat.id] = {'link': chat_link, 'message': message_text, 'count': count, 'delay': delay}
        print(f"Вы присоединились к чату: {chat_link} с сообщением: '{message_text}' (Количество отправок: {count}, Задержка: {delay} секунд)")
    except (InviteHashExpired, InviteHashInvalid):
        print("Ошибка: ссылка приглашения недействительна или срок её действия истёк.")


# Команда для одновременной отправки сообщений в разные чаты с индивидуальной задержкой
async def send_messages_to_groups():
    global cancel_sending  # Используем глобальную переменную

    if not user_chats:
        print("Нет доступных групп для отправки сообщений.")
        return

    cancel_sending = False  # Сброс флага отмены

    # Функция для отправки сообщений с индивидуальной задержкой
    async def send_message(chat_id, chat_info):
        for i in range(chat_info['count']):
            if cancel_sending:
                print("Отправка сообщений была отменена.")
                break

            await asyncio.sleep(chat_info['delay'])
            await app.send_message(chat_id, chat_info['message'])
            print(f"Сообщение {i + 1}/{chat_info['count']} отправлено в группу: {chat_info['link']}")

    # Запускаем отправку сообщений в каждый чат параллельно
    await asyncio.gather(*(send_message(chat_id, chat_info) for chat_id, chat_info in user_chats.items()))

    if not cancel_sending:
        print("Все сообщения успешно отправлены.")


# Команда для просмотра всех добавленных чатов
async def view_groups():
    if not user_chats:
        print("Нет доступных групп.")
    else:
        print("Доступные группы:")
        for chat_id, chat_info in user_chats.items():
            print(f"{chat_id}: Ссылка: {chat_info['link']}, Сообщение: {chat_info['message']}, "
                  f"Количество отправок: {chat_info['count']}, Задержка: {chat_info['delay']} секунд")


# Команда для удаления группы
async def remove_chat():
    if not user_chats:
        print("Нет доступных групп для удаления.")
        return

    await view_groups()
    try:
        chat_id = int(input("Введите ID группы, которую хотите удалить: "))
        if chat_id in user_chats:
            del user_chats[chat_id]
            print("Группа успешно удалена.")
        else:
            print("Ошибка: Группа с таким ID не найдена.")
    except ValueError:
        print("Ошибка: Введите числовой ID группы.")


# Основное меню с командами
async def menu():
    while True:
        print("\n--- Меню ---")
        print("1. Добавить группу по ссылке, задать сообщение, количество отправок и задержку")
        print("2. Отправить сообщения в группы")
        print("3. Посмотреть доступные группы")
        print("4. Удалить группу")
        print("5. Отменить отправку сообщений")
        print("0. Выход")

        choice = input("Выберите команду: ")

        if choice == "1":
            link = input("Введите ссылку приглашения на группу: ")
            message_text = input("Введите текст сообщения для этой группы: ")
            try:
                count = int(input("Введите количество отправок сообщения: "))
                if count <= 0:
                    print("Ошибка: Количество отправок должно быть больше нуля.")
                    continue
                delay = int(input("Введите задержку между отправками сообщений (в секундах): "))
                if delay < 0:
                    print("Ошибка: Задержка не может быть отрицательной.")
                    continue
            except ValueError:
                print("Ошибка: Введите числовое значение.")
                continue
            await add_chat_by_link(link, message_text, count, delay)
        elif choice == "2":
            await send_messages_to_groups()
        elif choice == "3":
            await view_groups()
        elif choice == "4":
            await remove_chat()
        elif choice == "5":
            global cancel_sending
            cancel_sending = True
            print("Процесс отправки сообщений будет остановлен.")
        elif choice == "0":
            print("Выход.")
            break
        else:
            print("Ошибка: некорректная команда.")


if __name__ == "__main__":
    app.start()  # Запускаем клиент для авторизации пользователя
    app.run(menu())  # Запускаем меню
    app.stop()  # Останавливаем клиент
