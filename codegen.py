from textx import metamodel_from_file
from jinja2 import Template

# -------------------------------
# PLANTILLAS JINJA2
# -------------------------------

models_template = """
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

{% for entidad in entidades %}
class {{entidad.name}}(Base):
    __tablename__ = "{{entidad.name.lower()}}s"
    id = Column(Integer, primary_key=True, index=True)
    {% for campo in entidad.campos -%}
    {{campo.name}} = Column(
        {% if campo.tipo == 'string' %}String
        {% elif campo.tipo == 'int' %}Integer
        {% elif campo.tipo == 'float' %}Float
        {% endif %}, nullable=True)
    {% endfor %}
{% endfor %}
"""

database_template = """
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./evergreen.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""

main_template = """
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io

from database import SessionLocal, engine
from models import Base, {{ entidades|map(attribute='name')|join(', ') }}

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

{% for op in operaciones %}
@app.get("/reporte/{{op.name.lower()}}")
def reporte_{{op.name.lower()}}(db: Session = Depends(get_db)):
    productores = db.query(Productor).all()
    data = [
        { {% for campo in op.campos %}"{{campo}}": getattr(p, "{{campo.lower()}}"), {% endfor %} "Nombre": p.nombre }
        for p in productores
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="{{op.name}}")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename={{op.name}}.xlsx"}
    )
{% endfor %}
"""

# -------------------------------
# CARGAR GRAMÁTICA Y MODELO
# -------------------------------

mm = metamodel_from_file("analitica.tx")
model = mm.model_from_file("ejemplo.ana")

# -------------------------------
# GENERAR ARCHIVOS
# -------------------------------

# models.py
with open("models.py", "w") as f:
    f.write(Template(models_template).render(entidades=model.entidades))
print("✅ Generado: models.py")

# database.py
with open("database.py", "w") as f:
    f.write(database_template)
print("✅ Generado: database.py")

# main.py
with open("main.py", "w") as f:
    f.write(Template(main_template).render(entidades=model.entidades, operaciones=model.operaciones))
print("✅ Generado: main.py")
