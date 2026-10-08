import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from dotenv import load_dotenv
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from database.db import (
	create_pool,
	create_request,
	get_user_requests,
	get_user,
	create_user,
	get_all_requests,
	get_requests_by_status,
	update_request_status
)

from keyboards.keyboards import (
	main_keyboard,
	manager_keyboard,
	request_keyboard,
	contact_manager_keyboard,
	reply_to_user_keyboard
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MANAGER_ID = int(os.getenv("MANAGER_ID"))
MANAGER_PHONE = os.getenv("MANAGER_PHONE")

import socket

_original_getaddrinfo = socket.getaddrinfo

def getaddrinfo_ipv4(*args, **kwargs):

	return [
		result
		for result in _original_getaddrinfo(*args, **kwargs)
		if result[0] == socket.AF_INET
	]

socket.getaddrinfo = getaddrinfo_ipv4

bot = Bot(token = BOT_TOKEN)
dp = Dispatcher()

class ApplicationForm(StatesGroup):
	name = State()
	phone = State()
	problem = State()

class ContactManager(StatesGroup):
	message = State()

class ManagerReply(StatesGroup):
	message = State()

async def is_manager(telegram_id):
	pool = dp["pool"]
	user = await get_user(pool, telegram_id)

	return user and user['role'] == 'manager'

@dp.message(CommandStart())
async def start(message: Message):
	pool = dp['pool']
	telegram_id = message.from_user.id
	name = message.from_user.first_name

	user = await get_user(pool, telegram_id)

	if not user:
		await create_user(pool, telegram_id, name)
		user = await get_user(pool, telegram_id)

	if user['role'] == 'manager':
		keyboard = manager_keyboard
	else:
		keyboard = main_keyboard

	await message.answer("Привет! Я помогу оставить заявку 🤖\n\nВыберите действие:", reply_markup=keyboard)

@dp.message(Command("id"))
async def get_id(message: Message):
	await message.answer(f"Ваш Telegram ID: {message.from_user.id}")

@dp.message(F.text == "❌ Отмена")
async def cancel_application(message: Message, state: FSMContext):
	await state.clear()
	await message.answer(
		"Заполнение заявки отменено ❌",
		reply_markup=main_keyboard
	)

@dp.message(F.text == "Мои заявки")
async def my_requests(message: Message):
	pool = dp['pool']
	telegram_id = message.from_user.id

	requests = await get_user_requests(pool, telegram_id)

	if not requests:
		await message.answer("У вас пока нет заявок")
		return

	text = "📝 Ваши заявки:\n\n"

	for request in requests:
		text += (
			f"Заявка №{request['id']}\n"
			f"Проблема: {request['problem']}\n"
			f"Статус: {request['status']}\n"
			f"Дата: {request['created_at']}"
		)

	await message.answer(text)

@dp.message(F.text == "Все заявки")
async def all_requests(message: Message):
	pool = dp['pool']

	if not await is_manager(message.from_user.id):
		await message.answer("У вас нет доступа ❌")
		return

	requests = await get_all_requests(pool)

	if not requests:
		await message.answer("Заявок пока нет")
		return

	for request in requests:
		text = (
			f"Заявка №{request['id']}\n"
			f"👤 Имя: {request['name']}\n"
			f"📞 Телефон: {request['phone']}\n"
			f"📝 Проблема: {request['problem']}\n"
			f"📌 Статус: {request['status']}\n"
			f"🕐 Дата: {request['created_at']}\n"
		)

		await message.answer(text, reply_markup=request_keyboard(request["id"], request['status']))

@dp.callback_query(F.data.startswith("start_"))
async def start_request(callback:CallbackQuery):
	pool = dp['pool']

	if not await is_manager(callback.from_user.id):
		await callback.answer("У вас нет доступа ❌")
		return

	request_id = int(callback.data.split("_")[1])

	await update_request_status(
		pool,
		request_id,
		"IN_PROGRESS"
	)

	await callback.answer("Заявка взята в работу")

	await callback.message.edit_text(
		callback.message.text.replace(
			"New",
			"IN_PROGRESS"
		),
		reply_markup=request_keyboard(request_id, "IN_PROGRESS")
	)

@dp.callback_query(F.data.startswith("done_"))
async def done_request(callback:CallbackQuery):
	pool = dp['pool']

	if not await is_manager(callback.from_user.id):
		await callback.answer("У вас нет доступа ❌")
		return

	request_id = int(callback.data.split("_")[1])

	await update_request_status(
		pool,
		request_id,
		"DONE"
	)

	await callback.answer("Заявка взята в работу")

	await callback.message.edit_text(
		callback.message.text.replace(
			"NEW",
			"DONE"
		).replace(
			"IN_PROGRESS",
			"DONE"
		),
		reply_markup=request_keyboard(request_id, "DONE")
	)


@dp.message(F.text.in_({
	"Новые заявки",
	"В работе",
	"Заверщенные"
}))
async def requests_by_status(message:Message):
	pool = dp["pool"]

	if not await is_manager(message.from_user.id):
		await message.answer("У вас нет доступа ❌")
		return

	if message.text == "Новые заявки":
		status = "New"
	elif message.text == "В работе":
		status = "IN_PROGRESS"
	else:
		status = "DONE"

	requests = await get_requests_by_status(pool, status)

	if not requests:
		await message.answer("Заявок с таким статусом пока нет.")
		return

	for request in requests:
		text = (
			f"Заявка №{request['id']}\n"
			f"👤 Имя: {request['name']}\n"
			f"📞 Телефон: {request['phone']}\n"
			f"📝 Проблема: {request['problem']}\n"
			f"📌 Статус: {request['status']}\n"
			f"🕐 Дата: {request['created_at']}\n"
		)

		await message.answer(text, reply_markup=request_keyboard(request["id"], request['status']))

@dp.message(F.text == "Связаться с менеджером")
async def contact_manager(message:Message):
	await message.answer(
		"Как вы хотите связаться с менеджером?",
		reply_markup=contact_manager_keyboard(MANAGER_PHONE)
	)

@dp.callback_query(F.data == "manager_phone")
async def show_manager_phone(callback: CallbackQuery):
	await callback.message.answer(
		f"Телефон менеджера:\n{MANAGER_PHONE}"
	)
	await callback.answer()

@dp.callback_query(F.data == "write_manager")
async def write_manager(callback:CallbackQuery, state:FSMContext):
	await state.set_state(ContactManager.message)

	await callback.message.answer(
		"Написать сообщение для менеджера 💬"
	)

	await callback.answer()

@dp.message(ContactManager.message)
async def send_message_to_manager(message:Message, state:FSMContext):
	await bot.send_message(
		MANAGER_ID,
		f"💬 Новое сообщение от пользователя\n\n"
		f"👤 {message.from_user.first_name}\n"
		f"🆔 Telegram ID: {message.from_user.id}\n"
		f"Сообщение:\n{message.text}\n",
		reply_markup=reply_to_user_keyboard(message.from_user.id)
	)

@dp.callback_query(F.data.startswith("reply_user_"))
async def reply_to_user(callback:CallbackQuery, state:FSMContext):
	if not await is_manager(callback.from_user.id):
		await callback.answer("У вас нет доступа ❌")
		return

	telegram_id = int(callback.data.split("_")[2])

	await state.update_data(telegram_id=telegram_id)
	await state.set_state(ManagerReply.message)

	await callback.message.answer(
		"Напишите ответ пользователю 💬"
	)

	await callback.answer()

@dp.message(ManagerReply.message)
async def send_reply_to_user(message:Message, state:FSMContext):
	if not await is_manager(message.from_user.id):
		await message.answer("У вас нет доступа ❌")
		return

	data = await state.get_data()
	telegram_id = data['telegram_id']

	await bot.send_message(
		telegram_id,
		f"💬 Ответ менеджера:\n\n{message.text}"
	)

	await message.answer(
		"Ответ отправлен пользователю",
		reply_markup=manager_keyboard
	)

	await state.clear()
	

@dp.message(F.text == "Оставить заявку")
async def start_application(message: Message, state: FSMContext):
	await state.set_state(ApplicationForm.name)
	await message.answer("Как вас зовут?")

@dp.message(ApplicationForm.name)
async def get_name(message: Message, state: FSMContext):
	await state.update_data(name=message.text)
	await state.set_state(ApplicationForm.phone)
	await message.answer("Введите номер телефона:")

@dp.message(ApplicationForm.phone)
async def get_phone(message: Message, state: FSMContext):
	phone = message.text.strip()

	if not phone.startswith("+7") or len(phone) != 12 or not phone[1:].isdigit():
		await message.answer(
			"Неверный формат номера ❌\n"
			"Введите номер в формате:\n"
			"+77001234567"
		)
		return

	await state.update_data(phone=phone)
	await state.set_state(ApplicationForm.problem)
	await message.answer("Опишите вашу проблему:")

@dp.message(ApplicationForm.problem)
async def get_problem(message: Message, state: FSMContext):
	await state.update_data(problem=message.text)

	data = await state.get_data()

	pool = dp['pool']

	telegram_id = message.from_user.id

	await create_request(
		pool,
		telegram_id,
		data['name'],
		data['phone'],
		data['problem']
	)

	await bot.send_message(
		MANAGER_ID,
		f"🔔 Новая заявка!\n\n"
		f"Имя: {data['name']}\n"
		f"Телефон: {data['phone']}\n"
		f"Проблема: {data['problem']}\n"
	)

	await message.answer(
		"Заявка создана и сохранена ✅"
	)

	await state.clear()

async def main():
	pool = await create_pool()
	dp["pool"] = pool
	print("PostgreSQL подключен ✅")
	await dp.start_polling(bot)

if __name__ == "__main__":
	asyncio.run(main())