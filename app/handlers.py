import logging
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup
from sqlalchemy import select

from app.database import async_session_maker
from app.notes.models import Note
from app.states import NoteState
from app.users.models import User

router = Router()
logger = logging.getLogger('handlers')

@router.message(CommandStart())
async def zam_handler(message: Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text='Вывести заметку')],
        [KeyboardButton(text='Создать заметку')],
        [KeyboardButton(text='Посмотреть список юзеров')],
    ])
    await message.answer("Выберите один из вариантов", reply_markup=kb)

@router.message(F.text == 'Посмотреть список юзеров')
async def show_users_handler(message: Message):
    page = 1
    await show_users_page(message, page)


async def show_users_page(message: Message, page: int):
    async with async_session_maker() as session:
        users = await session.execute(select(User).offset((page - 1) * 10).limit(10))
        users = users.scalars().all()

    if not users:
        await message.answer('Пользователи не найдены')
        return

    text = '\n'.join(f'{user.tg_id}. {user.name}' for user in users)
    pagination_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='<<', callback_data=f'prev_user_page:{page}'),
            InlineKeyboardButton(text='>>', callback_data=f'next_user_page:{page}')
        ]
    ])
    await message.answer(f"Пользователи (страница {page})\n{text}", reply_markup=pagination_kb)


@router.message(F.text.regexp(r'^\d+$'))
async def get_user_by_id(message: Message):
    user_id = int(message.text)
    async with async_session_maker() as session:
        user = await session.get(User, user_id)

    if user:
        user_text = f"ID: {user.tg_id}\nИмя: {user.name}\nРоль: {user.role}\nКонтакт: {user.phone or 'Не указан'}"
        user_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Заблокировать", callback_data=f"block_user:{user_id}")],
            [InlineKeyboardButton(text="Сделать Админом", callback_data=f"make_admin:{user_id}")]
        ])
        await message.answer(user_text, reply_markup=user_kb)
    else:
        await message.answer("Пользователь не найден.")

@router.callback_query(F.data.startswith("block_user"))
async def block_user(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if user:
            user.role = "banned"
            await session.commit()
            await callback.message.answer(f"Пользователь {user_id} заблокирован.")
        else:
            await callback.message.answer("Пользователь не найден.")

@router.callback_query(F.data.startswith("make_admin"))
async def make_admin(callback: CallbackQuery):
    user_id = int(callback.data.split(":")[1])
    async with async_session_maker() as session:
        user = await session.get(User, user_id)
        if user:
            user.role = "admin"
            await session.commit()
            await callback.message.answer(f"Пользователь {user_id} теперь Администратор.")
        else:
            await callback.message.answer("Пользователь не найден.")

@router.message(F.text == 'Вывести заметку')
async def show_handler(message: Message):
    page = 1
    await show_notes_page(message, page)

async def show_notes_page(message: Message, page: int):
    notes = await Note.pagginate(limit=10, page=page)
    if not notes:
        await message.answer('Заметок не найдено')
        return

    text = '\n'.join(f'{note.id}. {note.title}' for note in notes)
    pagination_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='<<', callback_data=f'prev_page:{page}'),
            InlineKeyboardButton(text='>>', callback_data=f'next_page:{page}')
        ]
    ])
    await message.answer(f"Заметки (страница {page})\n{text}", reply_markup=pagination_kb)


@router.callback_query(F.data.startswith("prev_page"))
async def prev_page_handler(callback: CallbackQuery):
    current_page = int(callback.data.split(":")[1])
    new_page = max(current_page - 1, 1)
    await show_notes_page(callback.message, new_page)


@router.callback_query(F.data.startswith("next_page"))
async def next_page_handler(callback: CallbackQuery):
    current_page = int(callback.data.split(":")[1])
    new_page = current_page + 1
    await show_notes_page(callback.message, new_page)


@router.message(F.text == 'Создать заметку')
async def create_note(message: Message, state: FSMContext):
    await message.answer('Введите название')
    await state.set_state(NoteState.title)

@router.message(NoteState.title)
async def handle_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer('Введите Описание')
    await state.set_state(NoteState.description)

@router.message(NoteState.description)
async def handle_description(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data['title']
    description = message.text
    note = await Note.create(title=title, content=description)  # Убедитесь, что используется правильное поле content
    await message.answer(f'Заметка "{title}" создана.')
    await state.clear()


@router.message(F.text.regexp(r'\d+'))
async def get_note_by_id(message: Message):
    note_id = int(message.text)
    note = await Note.first(Note.id == note_id)

    if note:
        note_text = f"ID: {note.id}\nНазвание: {note.title}\nОписание: {note.content}\nСтатус: {'Выполнена' if note.status else 'Не выполнена'}"
        note_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Изменить", callback_data=f"edit_note:{note_id}")],
            [InlineKeyboardButton(text="Удалить", callback_data=f"delete_note:{note_id}")],
            [InlineKeyboardButton(text="Изменить статус", callback_data=f"toggle_status:{note_id}")]
        ])
        await message.answer(note_text, reply_markup=note_kb)
    else:
        await message.answer("Заметка не найдена.")


@router.callback_query(F.data.startswith("delete_note"))
async def delete_note(callback: CallbackQuery):
    note_id = int(callback.data.split(":")[1])

    async with async_session_maker() as session:
        note = await Note.first(Note.id == note_id)

        if note:
            await session.delete(note)
            await session.commit()
            await callback.message.answer(f"Заметка {note_id} удалена.")
        else:
            await callback.message.answer("Заметка не найдена.")


@router.callback_query(F.data.startswith("edit_note"))
async def edit_note(callback: CallbackQuery, state: FSMContext):
    note_id = int(callback.data.split(":")[1])
    note = await Note.first(Note.id == note_id)
    if note:
        await state.update_data(note_id=note_id)
        await callback.message.answer(f"Текущее название: {note.title}\nВведите новое название:")
        await state.set_state(NoteState.edit_title)
    else:
        await callback.message.answer("Заметка не найдена.")

@router.message(NoteState.edit_title)
async def edit_note_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer('Введите новое описание:')
    await state.set_state(NoteState.edit_description)


@router.message(NoteState.edit_description)
async def edit_note_description(message: Message, state: FSMContext):
    data = await state.get_data()
    note_id = data['note_id']
    title = data['title']
    description = message.text

    async with async_session_maker() as session:
        note = await Note.first(Note.id == note_id)
        if note:
            note.title = title
            note.content = description
            session.add(note)
            await session.commit()

            await message.answer(f'Заметка "{title}" успешно обновлена.')
        else:
            await message.answer('Ошибка обновления заметки.')

    await state.clear()


@router.callback_query(F.data.startswith("toggle_status"))
async def toggle_status_handler(callback: CallbackQuery):
    note_id = int(callback.data.split(":")[1])

    async with async_session_maker() as session:
        note = await Note.first(Note.id == note_id)

        if note:
            note.status = not note.status
            session.add(note)
            await session.commit()

            new_status = 'Выполнена' if note.status else 'Не выполнена'
            await callback.message.answer(f'Статус заметки изменен на "{new_status}".')
        else:
            await callback.message.answer('Заметка не найдена.')
