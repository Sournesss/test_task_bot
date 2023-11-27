# Импорт необходимых библиотек
from aiogram import Bot, Dispatcher, executor, types
import requests
from functools import lru_cache
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ParseMode

# Токен Telegram бота
API_TOKEN = "YOUR_TELEGRAM_BOT_API_TOKEN"

# Функция для кэшированного получения данных из API
@lru_cache(maxsize=100)
def get_data():
    token = "UokPEWhb7Gjf2hrqjRv_FlHOzWPSViPG"
    url = "https://api.simplify-bots.com/items/routes_level_up_bot?limit=-1"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json().get("data")
    else:
        print("Ошибка при выполнении запроса:", response.status_code)
        data = []
    return data
# Похожая функция для получения данных о товарах
@lru_cache(maxsize=100)
def _get_items():
    data = {}
    token = "UokPEWhb7Gjf2hrqjRv_FlHOzWPSViPG"
    url = "https://api.simplify-bots.com/items/routes_level_up_bot?limit=-1"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        for item in response.json().get('data'):
            data.update({item.get('id'):{'photo':item.get("photo"),'block_text':item.get('block_text'),'note':item.get('note'),'type':item.get('type')}})
    else:
        print("Ошибка при выполнении запроса:", response.status_code)
    return data

# Функция для извлечения информации из полученных данных
def get_info(data):
    try:
        datas = data.split("_")
        if len(datas) == 2:
            items = _get_items()
            data_type, item_id = datas
            return data_type,item_id,items.get(item_id).get('photo'),items.get(item_id).get('block_text'),items.get(item_id).get('note'),items.get(item_id).get('type')
        else:
            return datas
    except Exception as e:
        print(e)


# Инициализация хранилища и бота
storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Обработчик команды "/start" и "/help"
@dp.message_handler(commands=["start", "help"])
@dp.callback_query_handler(lambda c: c.data == "menu")
async def start(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['items'] = []
    reply_markup = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton("Магазин", callback_data="shop_5"),
        types.InlineKeyboardButton("Корзина", callback_data="cart_0"),
        types.InlineKeyboardButton("F.A.Q.", callback_data="faq_0"),
        types.InlineKeyboardButton("Поддержка", callback_data="support_0"),
        types.InlineKeyboardButton("Кабинет", callback_data="profile_0"),
        types.InlineKeyboardButton("Отзывы", callback_data="reviews_0"),
    ]
    reply_markup.add(*buttons)
    photo = "https://api.simplify-bots.com/assets/957fff76-288d-4f40-9f56-694b9b8c2fe6.png"
    if isinstance(message,types.Message):
        await bot.send_photo(chat_id=message.from_user.id,photo=photo,caption="Привет! Я бот, который поможет тебе с навигацией.",reply_markup=reply_markup)
    else:
        await bot.edit_message_media(media=types.InputMediaPhoto(photo),chat_id=message.from_user.id, message_id=message.message.message_id)
        await bot.edit_message_reply_markup(chat_id=message.from_user.id,message_id=message.message.message_id, reply_markup=reply_markup)



# Обработчик кнопки "Назад" в меню бота
@dp.callback_query_handler(lambda c: c.data == "back")
async def back(callback_query: types.CallbackQuery, state: FSMContext):
    try:
        async with state.proxy() as data:
            if len(data['items']) > 1:
                element = data['items'][-2]
                data['items'] = data['items'][:-2]
            elif data['items']:
                element = data['items'][0]
                data['items'].clear()
            await memu(callback_query, state, element)
    except UnboundLocalError:
        await callback_query.answer("Для выхода в Меню используйте кнопку 'Меню'", show_alert=True)


# Обработчик для меню и подменю бота
@dp.callback_query_handler(lambda c: "_" in c.data)
async def memu(callback_query: types.CallbackQuery, state: FSMContext,item_id=None):

    # buttons_with_coords = {}  # словарь для кнопок с координатами
    # buttons_without_coords = []
    await bot.answer_callback_query(callback_query.id)
    if not item_id:
        data_type, item_id, photo, block_text, note,button_type = get_info(callback_query.data)
    else:
        data_type, item_id, photo, block_text, note, button_type = get_info(f'shop_{item_id}')
    async with state.proxy() as data:
        data['items'].append(item_id)
    items_data = get_data()
    next_items = [item for item in items_data if item.get("last_block") == str(item_id)]
    reply_markup = types.InlineKeyboardMarkup()
    for item in next_items:
        item_button_text = item.get("button_text")
        next_item_id = item.get("id", "")
        # row = item.get('row',None)
        # column = item.get('column', None)
        callback_data = f"{data_type}_{next_item_id}"
        button = types.InlineKeyboardButton(item_button_text, callback_data=callback_data)
        reply_markup.add(button)
        # if row is not None and column is not None:
        #     if row not in buttons_with_coords:
        #         buttons_with_coords[row] = {}
        #     buttons_with_coords[row][column] = button
        # reply_markup = types.InlineKeyboardMarkup()

        #
        # # Добавление кнопок с координатами
        # for row in sorted(buttons_with_coords):
        #     row_buttons = [buttons_with_coords[row][col] for col in sorted(buttons_with_coords[row])]
        #     reply_markup.row(*row_buttons)
        #
        # # Добавление кнопок без координат
        # for button in buttons_without_coords:
        #   reply_markup.add(button)

    if note and button_type == 'product':
        reply_markup.add(types.InlineKeyboardButton(note, callback_data="buy"))
    if item_id != '5':
        reply_markup.add(types.InlineKeyboardButton("Назад", callback_data="back"))
    reply_markup.add(types.InlineKeyboardButton("Меню", callback_data="menu"))
    if photo:
        await bot.edit_message_media(media=types.InputMediaPhoto(f'https://api.simplify-bots.com/assets/{photo}.png'),chat_id=callback_query.from_user.id,message_id=callback_query.message.message_id)
    if block_text:
        await bot.edit_message_caption(chat_id=callback_query.from_user.id,message_id=callback_query.message.message_id,caption=block_text.replace("%0a", "\n"),reply_markup=reply_markup,parse_mode=ParseMode.HTML)
    else:
        await bot.edit_message_reply_markup(chat_id=callback_query.from_user.id,message_id=callback_query.message.message_id,reply_markup=reply_markup)

# Обработчик для покупки товара
@dp.callback_query_handler(lambda c: c.data == "buy")
async def buy(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    # Создаем новую клавиатуру с кнопками "Назад" и "Меню"
    inline_kb = types.InlineKeyboardMarkup()
    inline_kb.add(types.InlineKeyboardButton('Назад', callback_data='back'))
    inline_kb.add(types.InlineKeyboardButton('Меню', callback_data='menu'))

    # Обновляем только текст сообщения
    await bot.edit_message_caption(chat_id=callback_query.from_user.id,
                                   message_id=callback_query.message.message_id,
                                   caption='Товар куплен',
                                   reply_markup=inline_kb,
                                   parse_mode=ParseMode.HTML)

# Основная функция для запуска бота
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
