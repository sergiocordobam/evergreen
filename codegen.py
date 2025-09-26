from textx import metamodel_from_file
from jinja2 import Template

models_template = """
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

{% for entidad in entidades %}
class {{entidad.name}}(Base):
    __tablename__ = "{{entidad.name.lower()}}s"
    id = Column(Integer, primary_key=True, index=True)
    {% for campo in entidad.campos -%}
    {% if campo.name == 'id_productor' %}
    id_productor = Column(Integer, ForeignKey("productors.id"))
    productor = relationship("Productor", back_populates="productos")
    {% elif campo.name == 'id_producto' %}
    id_producto = Column(Integer, ForeignKey("productos.id"))
    producto = relationship("Producto", back_populates="productores")
    {% else %}
    {{campo.name}} = Column(
        {% if campo.tipo == 'string' %}String
        {% elif campo.tipo == 'int' %}Integer
        {% elif campo.tipo == 'float' %}Float
        {% endif %}, nullable=True)
    {% endif %}
    {% endfor %}
{% endfor %}

# Relaciones inversas
Productor.productos = relationship("ProductoProductor", back_populates="productor")
Producto.productores = relationship("ProductoProductor", back_populates="producto")
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
    # JOIN explícito: trae (ProductoProductor, Productor, Producto)
    relaciones = db.query(ProductoProductor, Productor, Producto) \
                   .join(Productor, ProductoProductor.id_productor == Productor.id) \
                   .join(Producto, ProductoProductor.id_producto == Producto.id) \
                   .all()

    data = []
    for rel_pp, prodor, producto in relaciones:
        data.append({
            "Nombre Productor": prodor.nombre,
            "Área": prodor.area,
            "Nombre Producto": producto.nombre,
            "Costo": rel_pp.costo,
            "Cantidad": rel_pp.cantidad
        })

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
    productor = db.query(Productor).filter(Productor.nombre == nombre).first()
    if not productor:
        return {"error": f"No se encontró el productor con nombre {nombre}"}

    relaciones = db.query(ProductoProductor, Producto) \
                   .join(Producto, ProductoProductor.id_producto == Producto.id) \
                   .filter(ProductoProductor.id_productor == productor.id) \
                   .all()

    if not relaciones:
        return {"error": f"No hay datos de producción/costos para {nombre}"}

    # Extraer datos
    productos = [prod.nombre for _, prod in relaciones]
    cantidades = [rel_pp.cantidad for rel_pp, _ in relaciones]
    costos = [rel_pp.costo for rel_pp, _ in relaciones]

    # Gráfica de barras: Cantidad vs Costo por producto
    x = range(len(productos))
    fig, ax = plt.subplots()
    ax.bar([i - 0.2 for i in x], cantidades, width=0.4, color="orange", label="Cantidad")
    ax.bar([i + 0.2 for i in x], costos, width=0.4, color="blue", label="Costo")

    ax.set_title(f"Cantidad vs Costos por producto - {nombre}")
    ax.set_ylabel("Valor")
    ax.set_xticks(x)
    ax.set_xticklabels(productos, rotation=45, ha="right")
    ax.legend()

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format="png", bbox_inches="tight")
    plt.close(fig)
    img_buf.seek(0)

    # PDF
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 750, f"Reporte Cantidad vs Costos - {nombre}")
    c.drawImage(ImageReader(img_buf), 50, 350, width=500, height=350)
    c.showPage()
    c.save()
    pdf_buf.seek(0)

    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Reporte_{{op.name}}_{nombre}.pdf"}
    )

{% elif op.__class__.__name__ == "ReporteTop3" %}
@app.get("/reporte/{{op.name.lower()}}/top3")
def reporte_{{op.name.lower()}}(producto: str = Query(..., description="Nombre del producto"),
                                db: Session = Depends(get_db)):

    # Buscar el producto
    prod = db.query(Producto).filter(Producto.nombre == producto).first()
    if not prod:
        return {"error": f"No se encontró el producto {producto}"}

    # Traer relaciones de este producto
    relaciones = db.query(ProductoProductor, Productor) \
                   .join(Productor, ProductoProductor.id_productor == Productor.id) \
                   .filter(ProductoProductor.id_producto == prod.id) \
                   .order_by(ProductoProductor.cantidad.desc()) \
                   .limit(3) \
                   .all()

    if not relaciones:
        return {"error": f"No hay productores registrados para el producto {producto}"}

    data = []
    for rel_pp, prodor in relaciones:
        data.append({
            "Nombre Productor": prodor.nombre,
            "Área": prodor.area,
            "Producto": producto,
            "Cantidad": rel_pp.cantidad,
            "Costo": rel_pp.costo
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Top3")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Top3_{producto}.xlsx"}
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
