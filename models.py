
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Productor(Base):
    __tablename__ = "productors"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(
        String
        , nullable=True)
    area = Column(
        Float
        , nullable=True)
    
    
    # Relaciones muchos a muchos
    
    
    productoproductores = relationship("ProductoProductores", back_populates="productor")
    
    

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(
        String
        , nullable=True)
    
    
    # Relaciones muchos a muchos
    
    
    productoproductores = relationship("ProductoProductores", back_populates="producto")
    
    



class ProductoProductores(Base):
    __tablename__ = "productoproductores"
    id = Column(Integer, primary_key=True, index=True)
    id_productor = Column(Integer, ForeignKey("productors.id"), nullable=False)
    id_producto = Column(Integer, ForeignKey("productos.id"), nullable=False)
    costos = Column(
        Float
        , nullable=True)
    cantidad = Column(
        Float
        , nullable=True)
    
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    productor = relationship("Productor", back_populates="productoproductores")
    producto = relationship("Producto", back_populates="productoproductores")
