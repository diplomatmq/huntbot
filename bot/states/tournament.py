from aiogram.fsm.state import State, StatesGroup


class TournamentStates(StatesGroup):
    name = State()
    starts_at = State()
    ends_at = State()
    winners_count = State()
    metric = State()
    confirmation = State()
