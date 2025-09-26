import random
from database import SessionLocal, engine
from models import Base, Productor

Base.metadata.create_all(bind=engine)

db = SessionLocal()

N = 10
productores = []
for i in range(1, N + 1):
    productores.append(
        Productor(
            nombre=f"Finca {i}",
            produccion=random.uniform(500, 5000),
            area=random.uniform(10, 200),
            costos=random.uniform(100, 3000)
        )
    )

db.add_all(productores)
db.commit()
db.close()

print(f"Insertados {N} productores en la base de datos")
