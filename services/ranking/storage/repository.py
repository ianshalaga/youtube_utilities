from sqlalchemy.orm import Session
from .models.duel import Duel
from .models.battle import Battle
from .models.round import Round


class RankingRepository:
    def __init__(self, session: Session):
        self.session = session

    def iter_duels_ordered(self):
        return (
            self.session
            .query(Duel)
            .order_by(Duel.event_id, Duel.order_in_event)
            .all()
        )

    def battles_for_duel(self, duel_id: int):
        return (
            self.session
            .query(Battle)
            .filter(Battle.duel_id == duel_id)
            .order_by(Battle.order_in_duel)
            .all()
        )

    def rounds_for_battle(self, battle_id: int):
        return (
            self.session
            .query(Round)
            .filter(Round.battle_id == battle_id)
            .order_by(Round.order_in_battle)
            .all()
        )
