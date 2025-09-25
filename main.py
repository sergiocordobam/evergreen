
from fastapi import FastAPI, Depends, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import pandas as pd
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import base64

from database import SessionLocal, engine
from models import Base, Productor, Producto, ProductoProductores

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Análisis de Producción", version="1.0.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Reporte consolidado de productores con costos y producción
@app.get("/reporte/consolidado")
def reporte_consolidado(db: Session = Depends(get_db)):
    '''Como administrador del sistema quiero generar un reporte consolidado con la información de todos los productores acerca de sus costos dada la producción'''
    
    query = db.query(
        Productor.nombre.label('Productor'),
        Productor.area.label('Area'),
        func.sum(ProductoProductores.costos).label('Total_Costos'),
        func.sum(ProductoProductores.cantidad).label('Total_Produccion'),
        func.count(ProductoProductores.id).label('Num_Productos')
    ).join(ProductoProductores, Productor.id == ProductoProductores.id_productor)     .group_by(Productor.id, Productor.nombre, Productor.area)     .all()
    
    data = [
        {
            "Productor": row.Productor,
            "Area": row.Area,
            "Total_Costos": row.Total_Costos,
            "Total_Produccion": row.Total_Produccion,
            "Num_Productos": row.Num_Productos,
            "Costo_por_Unidad": row.Total_Costos / row.Total_Produccion if row.Total_Produccion > 0 else 0
        }
        for row in query
    ]
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Reporte_Consolidado")
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reporte_consolidado.xlsx"}
    )

# 2. Gráfica del histórico de producción de un productor
@app.get("/grafica/historico/{productor_id}")
def grafica_historico_produccion(productor_id: int, db: Session = Depends(get_db)):
    '''Como productor quiero ver una gráfica del histórico de toda mi producción para ver como ha avanzado durante el tiempo'''
    
    # Obtener datos históricos del productor
    query = db.query(
        ProductoProductores.fecha_registro,
        Producto.nombre.label('producto'),
        ProductoProductores.cantidad,
        ProductoProductores.costos
    ).join(Producto, ProductoProductores.id_producto == Producto.id)     .filter(ProductoProductores.id_productor == productor_id)     .order_by(ProductoProductores.fecha_registro)     .all()
    
    if not query:
        return JSONResponse({"error": "No se encontraron datos para el productor especificado"})
    
    # Crear gráfica
    plt.figure(figsize=(12, 8))
    
    # Agrupar por fecha y sumar cantidades
    df = pd.DataFrame([(row.fecha_registro, row.cantidad, row.costos) for row in query], 
                     columns=['fecha', 'cantidad', 'costos'])
    df_daily = df.groupby(df['fecha'].dt.date).agg({
        'cantidad': 'sum',
        'costos': 'sum'
    }).reset_index()
    
    plt.subplot(2, 1, 1)
    plt.plot(df_daily['fecha'], df_daily['cantidad'], marker='o', linewidth=2, markersize=6)
    plt.title('Histórico de Producción por Cantidad')
    plt.xlabel('Fecha')
    plt.ylabel('Cantidad Total')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    plt.subplot(2, 1, 2)
    plt.plot(df_daily['fecha'], df_daily['costos'], marker='s', color='red', linewidth=2, markersize=6)
    plt.title('Histórico de Costos')
    plt.xlabel('Fecha')
    plt.ylabel('Costos Total')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Convertir gráfica a base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return JSONResponse({
        "productor_id": productor_id,
        "grafica": f"data:image/png;base64,{image_base64}",
        "resumen": {
            "total_cantidad": df['cantidad'].sum(),
            "total_costos": df['costos'].sum(),
            "promedio_costo_por_unidad": df['costos'].sum() / df['cantidad'].sum() if df['cantidad'].sum() > 0 else 0
        }
    })

# 3. Top productores de un producto específico
@app.get("/reporte/top-productores")
def top_productores(producto_id: int, cantidad_minima: float = Query(100), db: Session = Depends(get_db)):
    '''Cuales son los productores que generan más de x producto'''
    
    query = db.query(
        Productor.nombre.label('Productor'),
        Productor.area.label('Area'),
        Producto.nombre.label('Producto'),
        func.sum(ProductoProductores.cantidad).label('Total_Cantidad'),
        func.sum(ProductoProductores.costos).label('Total_Costos')
    ).join(ProductoProductores, Productor.id == ProductoProductores.id_productor)     .join(Producto, ProductoProductores.id_producto == Producto.id)     .filter(Producto.id == producto_id)     .group_by(Productor.id, Productor.nombre, Productor.area, Producto.nombre)     .having(func.sum(ProductoProductores.cantidad) >= cantidad_minima)     .order_by(desc(func.sum(ProductoProductores.cantidad)))     .all()
    
    data = [
        {
            "Productor": row.Productor,
            "Area": row.Area,
            "Producto": row.Producto,
            "Total_Cantidad": row.Total_Cantidad,
            "Total_Costos": row.Total_Costos,
            "Costo_por_Unidad": row.Total_Costos / row.Total_Cantidad if row.Total_Cantidad > 0 else 0
        }
        for row in query
    ]
    
    return JSONResponse({
        "producto_id": producto_id,
        "cantidad_minima": cantidad_minima,
        "total_productores": len(data),
        "productores": data
    })

# 4. Resumen de costos agrupados por productos para un productor
@app.get("/reporte/resumen-costos/{productor_id}")
def resumen_costos_productor(productor_id: int, db: Session = Depends(get_db)):
    '''Como Productor quiero saber el total de los costos agrupados por productos'''
    
    query = db.query(
        Producto.nombre.label('Producto'),
        func.sum(ProductoProductores.costos).label('Total_Costos'),
        func.sum(ProductoProductores.cantidad).label('Total_Cantidad'),
        func.count(ProductoProductores.id).label('Num_Registros'),
        func.avg(ProductoProductores.costos).label('Costo_Promedio')
    ).join(ProductoProductores, Producto.id == ProductoProductores.id_producto)     .filter(ProductoProductores.id_productor == productor_id)     .group_by(Producto.id, Producto.nombre)     .order_by(desc(func.sum(ProductoProductores.costos)))     .all()
    
    data = [
        {
            "Producto": row.Producto,
            "Total_Costos": row.Total_Costos,
            "Total_Cantidad": row.Total_Cantidad,
            "Num_Registros": row.Num_Registros,
            "Costo_Promedio": row.Costo_Promedio,
            "Costo_por_Unidad": row.Total_Costos / row.Total_Cantidad if row.Total_Cantidad > 0 else 0
        }
        for row in query
    ]
    
    total_general = sum(item["Total_Costos"] for item in data)
    
    return JSONResponse({
        "productor_id": productor_id,
        "total_costos_general": total_general,
        "num_productos": len(data),
        "resumen_por_producto": data
    })

# Endpoint adicional para obtener lista de productores y productos
@app.get("/catalogo/productores")
def get_productores(db: Session = Depends(get_db)):
    productores = db.query(Productor).all()
    return [{"id": p.id, "nombre": p.nombre, "area": p.area} for p in productores]

@app.get("/catalogo/productos")
def get_productos(db: Session = Depends(get_db)):
    productos = db.query(Producto).all()
    return [{"id": p.id, "nombre": p.nombre} for p in productos]