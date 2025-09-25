from textx import metamodel_from_file
from jinja2 import Template

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
from fastapi import FastAPI, Depends{% if operaciones|selectattr("__class__.__name__","equalto","ReporteProductorPDF")|list %}, Query{% endif %}
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import pandas as pd
import io
{% if operaciones|selectattr("__class__.__name__","equalto","ReporteProductorPDF")|list %}
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
{% endif %}

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
{% if op.__class__.__name__ == "ReporteProductores" %}
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

{% elif op.__class__.__name__ == "ReporteProductorPDF" %}
@app.get("/reporte/{{op.name.lower()}}/pdf")
def reporte_{{op.name.lower()}}(nombre: str = Query(..., description="Nombre del productor"),
                                db: Session = Depends(get_db)):
    productores = db.query(Productor).filter(Productor.nombre == nombre).all()
    if not productores:
        return {"error": f"No se encontró el productor con nombre {nombre}"}

    # Extraer datos
    producciones = [p.produccion for p in productores if p.produccion is not None]
    costos = [p.costos for p in productores if p.costos is not None]

    if not producciones or not costos:
        return {"error": f"No hay datos de producción/costos para {nombre}"}

    # Gráfica Producción vs Costos
    fig, ax = plt.subplots()
    indices = range(len(producciones))

    ax.bar([i - 0.2 for i in indices], producciones, width=0.4, color="blue", label="Producción")
    ax.bar([i + 0.2 for i in indices], costos, width=0.4, color="orange", label="Costos")
    ax.set_title(f"Producción vs Costos - {nombre}")
    ax.set_xlabel("")
    ax.set_ylabel("Valor")
    ax.set_xticks([])   # quitamos los números en el eje X
    ax.legend() 

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png")
    plt.close(fig)
    img_buf.seek(0)

    # PDF
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, f"Reporte Producción vs Costos - {nombre}")
    c.drawImage(ImageReader(img_buf), 50, 400, width=500, height=300)
    c.showPage()
    c.save()
    pdf_buf.seek(0)

    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Reporte_{{op.name}}_{nombre}.pdf"}
    )
{% endif %}
{% endfor %}
"""

mm = metamodel_from_file("analitica.tx")
model = mm.model_from_file("ejemplo.ana")

# models.py
with open("models.py", "w", encoding="utf-8") as f:
    f.write(Template(models_template).render(entidades=model.entidades))
print("Generado: models.py")

# database.py
with open("database.py", "w", encoding="utf-8") as f:
    f.write(database_template)
print("Generado: database.py")

# main.py
with open("main.py", "w", encoding="utf-8") as f:
    f.write(Template(main_template).render(entidades=model.entidades, operaciones=model.operaciones))
print("Generado: main.py")
