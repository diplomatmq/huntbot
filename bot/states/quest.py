from aiogram.fsm.state import State, StatesGroup


class QuestStates(StatesGroup):
    viewing_quests = State()
    choosing_quest = State()
    confirming_quest = State()
