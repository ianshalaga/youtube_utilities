from services.ranking.storage.session import engine
from services.ranking.storage.base import Base
import services.ranking.storage.models  # importa todos los modelos


def create_db():
    Base.metadata.create_all(engine)
    print("Base de datos creada correctamente.")


# if __name__ == "__main__":
#     main()
