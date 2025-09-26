
from fastapi import FastAPI, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
import io

import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader


from database import SessionLocal, engine
from models import Base, Productor, Producto, ProductoProductor

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/reporte/reporteglobal")
def reporte_reporteglobal(db: Session = Depends(get_db)):

    relaciones = db.query(ProductoProductor, Productor, Producto)                    .join(Productor, ProductoProductor.id_productor == Productor.id)                    .join(Producto, ProductoProductor.id_producto == Producto.id)                    .all()

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
        df.to_excel(writer, index=False, sheet_name="ReporteGlobal")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=ReporteGlobal.xlsx"}
    )




@app.get("/reporte/historico/pdf")
def reporte_historico(nombre: str = Query(..., description="Nombre del productor"),
                                db: Session = Depends(get_db)):
    productor = db.query(Productor).filter(Productor.nombre == nombre).first()
    if not productor:
        return {"error": f"No se encontró el productor con nombre {nombre}"}

    relaciones = db.query(ProductoProductor, Producto)                    .join(Producto, ProductoProductor.id_producto == Producto.id)                    .filter(ProductoProductor.id_productor == productor.id)                    .all()

    if not relaciones:
        return {"error": f"No hay datos de producción/costos para {nombre}"}

    productos = [prod.nombre for _, prod in relaciones]
    cantidades = [rel_pp.cantidad for rel_pp, _ in relaciones]
    costos = [rel_pp.costo for rel_pp, _ in relaciones]

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
        headers={"Content-Disposition": f"attachment; filename=Reporte_Historico_{nombre}.pdf"}
    )




@app.get("/reporte/top3/top3")
def reporte_top3(producto: str = Query(..., description="Nombre del producto"),
                                db: Session = Depends(get_db)):

    prod = db.query(Producto).filter(Producto.nombre == producto).first()
    if not prod:
        return {"error": f"No se encontró el producto {producto}"}

    relaciones = db.query(ProductoProductor, Productor)                    .join(Productor, ProductoProductor.id_productor == Productor.id)                    .filter(ProductoProductor.id_producto == prod.id)                    .order_by(ProductoProductor.cantidad.desc())                    .limit(3)                    .all()

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




@app.get("/reporte/costosagrupados/costos")
def reporte_costosagrupados(nombre: str = Query(..., description="Nombre del productor"),
                                db: Session = Depends(get_db)):

    productor = db.query(Productor).filter(Productor.nombre == nombre).first()
    if not productor:
        return {"error": f"No se encontró el productor con nombre {nombre}"}

    relaciones = db.query(Producto.nombre, func.sum(ProductoProductor.costo).label("total_costo"))                    .join(Producto, Producto.id == ProductoProductor.id_producto)                    .filter(ProductoProductor.id_productor == productor.id)                    .group_by(Producto.nombre)                    .all()

    if not relaciones:
        return {"error": f"No hay datos de costos para {nombre}"}

    data = []
    for producto, total_costo in relaciones:
        data.append({
            "Nombre Productor": productor.nombre,
            "Área": productor.area,
            "Producto": producto,
            "Total Costo": total_costo
        })

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="CostosAgrupados")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=CostosAgrupados_{nombre}.xlsx"}
    )

