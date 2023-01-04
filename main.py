import datetime
import logging
import time

from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, \
	ReplyKeyboardRemove
from aiogram.utils import executor

import keyboards
from keyboards import MainKeyboards, OtherKeyboards, generateFilterKeyboard
import config


# задаем уровень логов
from dbhelper import SQLighter

logging.basicConfig(level=logging.INFO)

# инициализируем бота
storage = MemoryStorage()
bot = Bot(token=config.API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# инициализируем соединение с БД
db = SQLighter('db.db')


# Обработчики
@dp.message_handler(commands=['start', 'help'])
async def process_start_command(message: types.Message):
	if message.chat.id >= 0:
		if (db.user_ex(message.from_user.id) == True):
			if message.chat.id in config.admins:
				await message.answer(config.start_text, reply_markup=MainKeyboards.admin_kb)
				await message.answer(config.main_text, reply_markup=MainKeyboards.admin_kb)
			else:
				await message.answer(config.start_text, reply_markup=MainKeyboards.user_kb)
				await message.answer(config.main_text, reply_markup=MainKeyboards.inline_user_kb)
		else:
			db.newUser(message.from_user.id)
			await message.answer(config.rules, reply_markup=MainKeyboards.user_kb)
			await message.answer(config.start_text, reply_markup=MainKeyboards.user_kb)
			await message.answer(config.main_text, reply_markup=MainKeyboards.inline_user_kb)
	else:
		await message.answer("Я запускаюсь только в личном чате", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler()
async def echo_message(message: types.Message, state: FSMContext):
	if message.text == '💎 Главное меню':
		await message.answer(config.main_text, reply_markup=MainKeyboards.inline_user_kb)
	if message.text == "🌝 Здесь может быть реклама 🌝":
		await message.answer("Какой то рекламный текст.\nЕсли что писать сюда: @KevinMertence")
	if message.text == "📝 Правила":
		await message.answer(config.rules, reply_markup=OtherKeyboards.inline_close_kb)

	# ADMINS

	if message.text == "💌 Сделать рассылку" and message.from_user.id in config.admins:
		await state.set_state('send_all')
		await message.answer("\nБот использует HTML теги для форматирования текста.\n" \
							 "Пример: <b>текст</b> даст вам *текст*\n\n" \
							 "Введите сообщение:", parse_mode="Markdown", reply_markup=OtherKeyboards.inline_cancel_kb)
	if message.text == "📊 Посмотреть статистику" and message.from_user.id in config.admins:
		stats_data = await db.get_data_stats()
		await message.answer(config.stats_text.format(users=stats_data['users'],
													  qty_logs=stats_data['qty_logs'],
													  paid=stats_data['paid'],
													  best_user=stats_data['best_user']), parse_mode="HTML")


@dp.message_handler(state='send_all')
async def send_all(message, state: FSMContext):
	buttons = [
	    types.InlineKeyboardButton(text="💌 Отправить", callback_data="send"),
	    types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
	]

	answer = types.InlineKeyboardMarkup(row_width=2)
	answer.add(*buttons)
	await state.update_data(msg_send_text=message.text)

	await message.answer(message.text, reply_markup=answer, parse_mode="HTML")

@dp.message_handler(content_types=['photo'], state='send_all')
async def send_all(message: types.Message, state: FSMContext):
	buttons = [
	    types.InlineKeyboardButton(text="💌 Отправить", callback_data="send"),
	    types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"),
	]

	answer = types.InlineKeyboardMarkup(row_width=2)
	answer.add(*buttons)
	photo_id = message.photo[0].file_id
	await state.update_data(msg_send_text=message.caption)
	await state.update_data(photo_id=photo_id)
	await bot.send_photo(message.chat.id, photo=photo_id, caption=message.caption, reply_markup=answer, parse_mode="HTML")



@dp.callback_query_handler(lambda call: call.data == "send", state='send_all')
async def send_all(call: types.CallbackQuery, state: FSMContext):
	try:
		photo_id = (await state.get_data())['photo_id']
		cg = 0
		cn = 0
		await bot.send_message(call.message.chat.id, "✅ Рассылка запущена!")

		for user in db.getAllUsersID():
			try:
				await bot.send_photo(user, photo=photo_id, caption=(await state.get_data())['msg_send_text'], parse_mode="HTML")
				cg += 1

			except Exception as e:
				cn += 1

		await bot.send_message(call.message.chat.id, config.send_to_all[0] + str(cg) + config.send_to_all[1] + str(cn))
		await call.message.delete()
	except:
		cg = 0
		cn = 0
		await bot.send_message(call.message.chat.id, "✅ Рассылка запущена!")
		for user in db.getAllUsersID():
			try:
				await bot.send_message(user, (await state.get_data())['msg_send_text'], parse_mode="HTML")
				cg += 1
			except Exception as e:
				cn += 1

		await bot.send_message(call.message.chat.id, config.send_to_all[0] + str(cg) + config.send_to_all[1] + str(cn))
		await call.message.delete()
	await state.finish()

# Инлайн обработка
class sendStates(StatesGroup):
	getFilter = State()
	waitlogs = State()

@dp.callback_query_handler(lambda call: call.data == 'back', state='*')
@dp.callback_query_handler(lambda call: call.data == 'back', state='wait_logs')
@dp.callback_query_handler(lambda call: call.data == 'back', state='get_filter')
@dp.callback_query_handler(lambda call: call.data == 'back')
async def back(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.edit_text(config.main_text, reply_markup=MainKeyboards.inline_user_kb, parse_mode="HTML")
	await state.finish()

@dp.callback_query_handler(lambda call: call.data == 'cancel', state='*')
@dp.callback_query_handler(lambda call: call.data == 'cancel', state='send_all')
@dp.callback_query_handler(lambda call: call.data == 'cancel', state='wait_logs')
@dp.callback_query_handler(lambda call: call.data == 'cancel', state='get_filter')
@dp.callback_query_handler(lambda call: call.data == 'cancel')
async def back(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete_reply_markup()
	await callback_query.message.edit_text("Отменено", parse_mode="HTML")
	await state.finish()

@dp.callback_query_handler(lambda call: call.data == 'close', state='*')
@dp.callback_query_handler(lambda call: call.data == 'close', state='wait_logs')
@dp.callback_query_handler(lambda call: call.data == 'close', state='get_filter')
@dp.callback_query_handler(lambda call: call.data == 'close')
async def back(callback_query: types.CallbackQuery, state: FSMContext):
	await callback_query.message.delete()
	await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'delete_buttons', state='*')
@dp.callback_query_handler(lambda call: call.data == 'delete_buttons', state='wait_logs')
@dp.callback_query_handler(lambda call: call.data == 'delete_buttons', state='get_filter')
@dp.callback_query_handler(lambda call: call.data == 'delete_buttons')
async def delete_buttons(callback_query: types.CallbackQuery, state: FSMContext):
	if not bool(callback_query.message.text):
		await callback_query.message.delete_reply_markup()
		await callback_query.message.edit_caption(callback_query.message.caption+"\nПроверен", parse_mode="HTML")
	else:
		await callback_query.message.delete_reply_markup()
		await callback_query.message.edit_text(callback_query.message.text + "\nПроверен", parse_mode="HTML")
	await state.finish()

# Отправка логов
@dp.callback_query_handler(lambda call: call.data == 'send_logs' )
async def back(callback_query: types.CallbackQuery, state: FSMContext):
	await state.update_data(services_list=await config.get_all_services())
	await callback_query.message.edit_text("Выберите сервисы, которые вы хотите чтоб мы отработали:", parse_mode="HTML", reply_markup=await generateFilterKeyboard(config.services))
	await state.set_state('get_filter')

@dp.callback_query_handler(text_startswith="service:", state='get_filter')
async def gg(call: types.CallbackQuery, state: FSMContext):
	service_taped = call.data.split(':')[1]
	user_data = (await state.get_data())['services_list']

	if user_data[service_taped]:
		user_data[service_taped] = 0
	else:
		user_data[service_taped] = 1

	await state.update_data(services_list=user_data)

	await call.message.edit_text("Выберите сервисы, которые мы отработали:", parse_mode="HTML", reply_markup=await generateFilterKeyboard(user_data))



@dp.callback_query_handler(lambda call: call.data == 'next', state='get_filter')
async def next(callback_query: types.CallbackQuery, state: FSMContext):
	if not bool(sum((await state.get_data())['services_list'].values())):
		await callback_query.answer(text='Выберите хотябы один сервис!')
	else:
		await callback_query.message.edit_text("🗂 Отправьте архив в бота, так же можно отправить ссылку на файлообменник.", parse_mode="HTML", reply_markup=OtherKeyboards.inline_back_kb)
		await state.set_state('wait_logs')

@dp.message_handler(content_types=['document'], state='wait_logs')
async def scan_message(message: types.Message, state: FSMContext):
	user_id = message.from_user.id
	payment = 0
	date = datetime.datetime.today()
	logs_id = await db.getLastLogs() + 1
	services = (await state.get_data())['services_list']
	text = f'<b>ID-{logs_id}\n' \
		   f'Логи пользователя @{message.from_user.username}\n' \
		   f'Дата отправки: {datetime.datetime.now()}\n</b>\n'
	for i in services:
		if services[i] == 0:
			text += f"❌ {i}\n"
		else:
			text += f"✅ {i}\n"
	await bot.send_document(chat_id=config.chat_id, document=message.document.file_id,
							caption=text, reply_markup=OtherKeyboards.inline_checklog_kb, parse_mode="HTML")
	await db.addLogs(user_id, payment, date)
	await db.addOneLog(user_id)
	await message.reply(f"Логи <b>№{logs_id}</b> были успешно отправлены!\n"
						f"Скоро ваши логи проверят и начислят вам баланс деньги.", parse_mode="HTML",
						reply_markup=OtherKeyboards.inline_back_kb)
	await state.finish()


@dp.message_handler(state='wait_logs')
async def echo_message(message: types.Message, state: FSMContext):
	if "http://" in message.text or "https://" in message.text:
		user_id = message.from_user.id
		payment = 0
		date = datetime.datetime.today()
		logs_id = await db.getLastLogs() + 1
		services = (await state.get_data())['services_list']
		text = f'<b>ID-{logs_id}\n' \
			   f'{message.text}\n' \
			   f'Логи пользователя @{message.from_user.username}\n' \
			   f'Дата отправки: {datetime.datetime.now()}\n</b>\n'
		for i in services:
			if services[i] == 0:
				text += f"❌ {i}\n"
			else:
				text += f"✅ {i}\n"
		await bot.send_message(chat_id=config.chat_id, text=text,
		reply_markup = OtherKeyboards.inline_checklog_kb, parse_mode = "HTML")

		await db.addLogs(user_id, payment, date)
		await db.addOneLog(user_id)
		await message.reply(f"Логи <b>№{logs_id}</b> были успешно отправлены!\n"
							f"Скоро ваши логи проверят и начислят вам баланс деньги.", parse_mode="HTML",
							reply_markup=OtherKeyboards.inline_back_kb)
	else:
		await message.reply("Неправильно введена ссылка на файлообменник.\nПопробуйте еще раз.", parse_mode="HTML",
							reply_markup=OtherKeyboards.inline_back_kb)
	await state.finish()



# Логи проверены
@dp.callback_query_handler(lambda call: call.data == 'add_balance', state='*')
async def have_balance(callback_query: types.CallbackQuery, state: FSMContext):
	if not bool(callback_query.message.text):
		logs_id = callback_query.message.caption.split()[0].split('-')[1]
	else:
		logs_id = callback_query.message.text.split()[0].split('-')[1]
	await state.update_data(logs_id=logs_id)
	await state.update_data(message_id=callback_query.message.message_id)
	await callback_query.message.reply(text="Отправьте сколько баланса начислить пользователю:", reply_markup=OtherKeyboards.inline_cancel_kb)
	await state.set_state("wait_for_balance")

@dp.message_handler(state='wait_for_balance')
async def echo_message(message: types.Message, state: FSMContext):
	howmany = int(message.text)
	logs_id = (await state.get_data())['logs_id']
	used_id = await db.get_logs_user_id(logs_id)
	await db.editBalance(used_id, howmany)
	await db.updateLogs(logs_id, howmany, 1)
	await bot.send_message(used_id, text = f"Ваши логи №{logs_id} успешно проверены.\n"
										   f"Вам начисленно: {howmany} руб.")
	await message.reply("Баланс добавлен пользователю.")
	await state.finish()

@dp.callback_query_handler(lambda call: call.data == 'break_logs', state='*')
async def havent_balance(callback_query: types.CallbackQuery, state: FSMContext):
	if not bool(callback_query.message.text):
		logs_id = callback_query.message.caption.split()[0].split('-')[1]
	else:
		logs_id = callback_query.message.text.split()[0].split('-')[1]
	used_id = await db.get_logs_user_id(logs_id)

	await bot.send_message(used_id, text=f"Ваши логи №{logs_id} были отклонены.\n")
	await callback_query.message.delete_reply_markup()


# Профиль
@dp.callback_query_handler(lambda call: call.data == 'profile')
async def back(callback_query: types.CallbackQuery, state: FSMContext):
	user_info = db.getProfileinfo(callback_query.from_user.id)
	await callback_query.message.edit_text(f"<b>👩🏻‍🚀 Профиль {'@'+callback_query.from_user.username}\n"
										   f"🆔 ID: {user_info[0][1]}\n"
										   f"--------------\n"
										   f"💵 Баланс: {user_info[0][2]} руб.\n"
										   f"💰 Сумма выплат: {user_info[0][3]} руб.\n"
										   f"📤 Всего логов отправлено: {user_info[0][4]} шт.\n"
										   f"</b>", parse_mode="HTML", reply_markup=OtherKeyboards.inline_profile)
	await state.finish()

@dp.callback_query_handler(lambda call: call.data == 'withdraw_button')
async def back(callback_query: types.CallbackQuery, state: FSMContext):
	user_info = db.getProfileinfo(callback_query.from_user.id)[0]
	if user_info[2] < 100:
		await callback_query.message.edit_text("Вывод от 100 рублей.", reply_markup=OtherKeyboards.inline_back_kb)
	else:
		await callback_query.message.answer("Введите реквизиты для вывода:\n"
									"Вывод осуществляется на LOLZ и Криптовалюты.", reply_markup=OtherKeyboards.inline_cancel_kb)
		await state.set_state('wait_for_req')

@dp.message_handler(state='wait_for_req')
async def echo_message(message: types.Message, state: FSMContext):
	user_info = db.getProfileinfo(message.from_user.id)[0]

	inline_withdraw = InlineKeyboardMarkup(resize_keyboard=True)
	inline_withdraw.add(InlineKeyboardButton('✅ Подтвердить вывод', callback_data=f'successwithdraw:{message.from_user.id}:{user_info[2]}'))
	inline_withdraw.add(InlineKeyboardButton('❌ Отклонить вывод', callback_data=f'cancelwithdraw:{message.from_user.id}:{user_info[2]}'))

	await bot.send_message(config.chat_id, f'‼️ Заявка на вывод @{message.from_user.id}:\n'
										   f'💰 Сумма: {user_info[2]} руб.\n'
										   f'📜 Реквизиты: {message.text}',
						   reply_markup=inline_withdraw)
	await db.editOnlyBalance(message.from_user.id, user_info[2] * -1)

	await message.answer(f'✅ Заявка на вывод подана.\n'
						 f'💰 Сумма: {user_info[2]} руб.\n'
						 f'📜 Реквизиты: {message.text}')

	await state.finish()

@dp.callback_query_handler(text_startswith="successwithdraw:")
async def gg(call: types.CallbackQuery, state: FSMContext):
	data = call.data.split(':')
	await bot.send_message(data[1], f'✅ Ваша заявка на вывод {data[2]} руб. успешно выполнена.\n'
									f'😘 Спасибо что пользуетесь нашим ботом!')
	await call.message.delete_reply_markup()
	await call.message.edit_text(call.message.text + '\n✅ Выполнена')
	await state.finish()

@dp.callback_query_handler(text_startswith="cancelwithdraw:")
async def gg(call: types.CallbackQuery, state: FSMContext):
	data = call.data.split(':')
	await bot.send_message(data[1], f'❌ Ваша заявка на вывод {data[2]} руб. отклонена.\n'
									f'💰 Ваш баланс восстановлен.')
	await db.editOnlyBalance(data[1], data[2])
	await call.message.delete_reply_markup()
	await call.message.edit_text(call.message.text + '\n❌ Отклонена')
	await state.finish()

# История
@dp.callback_query_handler(lambda call: call.data == 'history_logs')
async def history_logs(callback_query: types.CallbackQuery, state: FSMContext):
	history = await db.get_user_sent_logs(callback_query.from_user.id)

	await callback_query.message.edit_text(f"🗂 Ваши последние 10 отправленных логов:", parse_mode="HTML", reply_markup=await keyboards.generateHistory(history))

	await state.finish()

# Поддержка
@dp.callback_query_handler(lambda call: call.data == 'help')
async def history_logs(callback_query: types.CallbackQuery, state: FSMContext):
	history = await db.get_user_sent_logs(callback_query.from_user.id)

	await callback_query.message.edit_text(config.help_text, parse_mode="HTML", reply_markup=OtherKeyboards.inline_back_kb)

	await state.finish()

if __name__ == '__main__':
	executor.start_polling(dp)