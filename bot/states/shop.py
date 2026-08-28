from aiogram.fsm.state import State, StatesGroup


class ShopStates(StatesGroup):
    choosing_category = State()
    choosing_item = State()
    confirming_purchase = State()
