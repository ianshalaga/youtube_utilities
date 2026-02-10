from enum import Enum


class RoundResultCode(str, Enum):
    """
    Resultado de un round desde el punto de vista de UN jugador.

    Estos valores provienen del dataset histórico y son tratados
    como hechos competitivos primarios.
    """

    # Win / Loss
    W = "W"     # Win
    LB = "LB"   # Loss by Block / normal loss
    LY = "LY"   # Loss by Ring Out / special loss

    # Perfect
    PW = "PW"   # Perfect Win
    PL = "PL"   # Perfect Loss

    # Draw / No result
    D = "D"     # Draw
    ZERO = "0"  # Sin resultado / no contest

    @property
    def is_win(self) -> bool:
        return self in {self.W, self.PW}

    @property
    def is_loss(self) -> bool:
        return self in {self.LB, self.LY, self.PL}

    @property
    def is_draw(self) -> bool:
        return self in {self.D, self.ZERO}
