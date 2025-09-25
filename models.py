
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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
    
    

class Producto(Base):
    __tablename__ = "productos"
    id = Column(Integer, primary_key=True, index=True)
    
    nombre = Column(
        String
        , nullable=True)
    
    

class ProductoProductor(Base):
    __tablename__ = "productoproductors"
    id = Column(Integer, primary_key=True, index=True)
    
    id_producto = Column(Integer, ForeignKey("productos.id"))
    producto = relationship("Producto", back_populates="productores")
    
    
    id_productor = Column(Integer, ForeignKey("productors.id"))
    productor = relationship("Productor", back_populates="productos")
    
    
    costo = Column(
        Float
        , nullable=True)
    
    
    cantidad = Column(
        Float
        , nullable=True)
    
    


# Relaciones inversas
Productor.productos = relationship("ProductoProductor", back_populates="productor")
Producto.productores = relationship("ProductoProductor", back_populates="producto")