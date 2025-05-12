from aiogram.fsm.state import StatesGroup, State

class Form(StatesGroup):
    faceit_nick = State()
    faceit_link = State()
    email = State()
