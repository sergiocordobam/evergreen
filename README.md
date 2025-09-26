# EverGreen Analytics

Sistema de análisis para la gestión agrícola inteligente

## Módulo Analítica (ANA) - Implementado con TextX
TextX es un framework de metamodelado desarrollado en Python que permite
definir lenguajes específicos de dominio (DSLs) y utilizarlos para crear modelos que
luego se transforman en código ejecutable o aplicaciones.
## Requisitos

- Python 3.10+
- Node.js 18+
- pip
- npm

## Instalación

### Backend (FastAPI)
1. Instala las dependencias de Python:
   ```bash
   pip install -r requirements.txt
   ```
2. Inicia el servidor backend:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend (Next.js)
   Primero busca la ruta del Front de esta manera:
   ```bash
   cd .\front\
   ```
1. Instala las dependencias de Node:
   ```bash
   npm install
   ```
3. Inicia el servidor frontend:
   ```bash
   npm run dev
   ```

## Estructura del proyecto

```
.
├── main.py                # Backend FastAPI principal
├── requirements.txt       # Dependencias Python
├── front/                 # Carpeta del frontend Next.js
│   ├── app/               # Código fuente del frontend
│   ├── package.json       # Dependencias Node
│   └── ...
└── ...
```

## Notas
- El backend corre por defecto en `http://localhost:8000`
- El frontend corre por defecto en `http://localhost:3000`
- Asegúrate de que ambos servidores estén activos para el funcionamiento completo.

## Contacto

Para dudas o soporte, abre un issue en este repositorio.
