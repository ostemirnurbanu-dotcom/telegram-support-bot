from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_keyboard = ReplyKeyboardMarkup(
	keyboard=[
		[
			KeyboardButton(text="Оставить заявку")
		],
		[
			KeyboardButton(text="Мои заявки"),
			KeyboardButton(text="Связаться с менеджером")
		],
		[
			KeyboardButton(text="❌ Отмена")
		],
	],
	resize_keyboard=True
)

manager_keyboard = ReplyKeyboardMarkup(
	keyboard=[
		[
			KeyboardButton(text="Все заявки")
		],
		[
			KeyboardButton(text="Новые заявки")
		],
		[
			KeyboardButton(text="В работе"),
			KeyboardButton(text="Заверщенные")
		]
	],
	resize_keyboard=True
)

def request_keyboard(request_id, status):
	if status == 'New':
		return InlineKeyboardMarkup (
				inline_keyboard=[
					[
						InlineKeyboardButton(
							text="🔄 Взять в работу",
							callback_data=f"start_{request_id}"
						)
					],
					[
						InlineKeyboardButton(
							text="Завершить",
							callback_data=f"done_{request_id}"
						)
					]
				]
			)

	if status == 'IN_PROGRESS':
		return InlineKeyboardMarkup (
				inline_keyboard=[
					[
						InlineKeyboardButton(
							text="Завершить",
							callback_data=f"done_{request_id}"
						)
					]
				]
			)

	return None

def contact_manager_keyboard(manager_phone):
	return InlineKeyboardMarkup(
		inline_keyboard=[
			[
				InlineKeyboardButton(
					text="📞 Позвонить",
					callback_data="manager_phone"
				)
			],
			[
				InlineKeyboardButton(
					text="💬 Написать",
					callback_data=f"write_manager"
				)
			]
		]
	)

def reply_to_user_keyboard(telegram_id):
	return InlineKeyboardMarkup(
		inline_keyboard=[
			[
				InlineKeyboardButton(
					text="Ответить",
					callback_data=f"reply_user_{telegram_id}"
				)
			]
		]
	)