# Sistema de Análisis de Producción - Evergreen

Este proyecto implementa un sistema de análisis de producción utilizando TextX para modelado de dominio y FastAPI para la implementación de la API REST.

## Modelo de Datos

El sistema está basado en tres tablas principales:

### 1. Productor
- `id`: Identificador único
- `nombre`: Nombre del productor
- `area`: Área de producción

### 2. Producto
- `id`: Identificador único  
- `nombre`: Nombre del producto

### 3. ProductoProductores (Tabla de relación muchos a muchos)
- `id`: Identificador único
- `id_productor`: Clave foránea a la tabla Productor
- `id_producto`: Clave foránea a la tabla Producto
- `costos`: Costos asociados
- `cantidad`: Cantidad producida
- `fecha_registro`: Fecha de registro (automática)

## Historias de Usuario Implementadas

### 1. Reporte Consolidado de Productores
**Como administrador del sistema quiero generar un reporte consolidado con la información de todos los productores acerca de sus costos dada la producción**

- **Endpoint**: `GET /reporte/consolidado`
- **Respuesta**: Archivo Excel con información consolidada
- **Incluye**: Productor, Área, Total Costos, Total Producción, Número de Productos, Costo por Unidad

### 2. Gráfica Histórica de Producción
**Como productor quiero ver una gráfica del histórico de toda mi producción para ver como ha avanzado durante el tiempo**

- **Endpoint**: `GET /grafica/historico/{productor_id}`
- **Respuesta**: JSON con gráfica en base64 y resumen estadístico
- **Incluye**: Gráficas de cantidad y costos a lo largo del tiempo

### 3. Top Productores por Producto
**Cuales son los productores que generan más de x producto**

- **Endpoint**: `GET /reporte/top-productores?producto_id={id}&cantidad_minima={cantidad}`
- **Respuesta**: Lista de productores que superan la cantidad mínima
- **Incluye**: Productor, Área, Producto, Total Cantidad, Total Costos

### 4. Resumen de Costos por Productor
**Como Productor quiero saber el total de los costos agrupados por productos**

- **Endpoint**: `GET /reporte/resumen-costos/{productor_id}`
- **Respuesta**: Resumen de costos agrupado por productos
- **Incluye**: Producto, Total Costos, Total Cantidad, Costo Promedio, Costo por Unidad

## Instalación y Configuración

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Generar código
```bash
python3 codegen.py
```

Esto generará los siguientes archivos:
- `models.py`: Modelos SQLAlchemy
- `database.py`: Configuración de base de datos
- `main.py`: API FastAPI

### 3. Ejecutar la API
```bash
uvicorn main:app --reload
```

La API estará disponible en `http://localhost:8000`

### 4. Documentación interactiva
Visita `http://localhost:8000/docs` para la documentación automática de la API.

## Endpoints Adicionales

### Catálogos
- `GET /catalogo/productores`: Lista todos los productores
- `GET /catalogo/productos`: Lista todos los productos

## Estructura de Archivos

```
evergreen/
├── analitica.tx          # Gramática TextX
├── ejemplo.ana           # Modelo de ejemplo
├── codegen.py           # Generador de código
├── requirements.txt     # Dependencias Python
├── models.py           # Modelos SQLAlchemy (generado)
├── database.py         # Configuración DB (generado)
├── main.py            # API FastAPI (generado)
├── test_api.py        # Script de pruebas
└── README.md          # Este archivo
```

## Tecnologías Utilizadas

- **TextX**: Lenguaje de modelado de dominio específico (DSL)
- **FastAPI**: Framework web moderno para APIs REST
- **SQLAlchemy**: ORM para Python
- **Pandas**: Manipulación de datos
- **Matplotlib**: Generación de gráficas
- **Jinja2**: Motor de plantillas
- **SQLite**: Base de datos (por defecto)

## Ejemplo de Uso

### 1. Probar la API
```bash
python3 test_api.py
```

### 2. Obtener reporte consolidado
```bash
curl -X GET "http://localhost:8000/reporte/consolidado" -o reporte.xlsx
```

### 3. Ver gráfica histórica
```bash
curl -X GET "http://localhost:8000/grafica/historico/1"
```

## Personalización

Para modificar el modelo de datos:

1. Edita `ejemplo.ana` con las nuevas entidades y relaciones
2. Actualiza `analitica.tx` si necesitas nuevos tipos de operaciones
3. Modifica las plantillas en `codegen.py` según tus necesidades
4. Regenera el código con `python3 codegen.py`

## Notas

- La base de datos SQLite se crea automáticamente al ejecutar la API
- Las gráficas se generan como imágenes PNG codificadas en base64
- Los reportes Excel se descargan directamente desde el navegador
- El sistema incluye validación automática de tipos de datos
