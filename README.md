#  G2 Scraper – Motor Resiliente de Extracción de Datos

## Descripción

Este proyecto implementa un **motor de web scraping resiliente** para la extracción de información desde G2.com, diseñado para ejecutar múltiples iteraciones (≥100) manteniendo:

* Alta tasa de éxito
* Integridad de los datos
* Resistencia ante bloqueos y cambios en el DOM

El sistema está preparado para entornos reales donde existen mecanismos anti-bot, latencias variables y contenido dinámico.

---

## Arquitectura

La solución está basada en una combinación de:

* **Clean Architecture**
* Principios inspirados en **DDD (Domain-Driven Design)**
* Aplicación pragmática de principios **SOLID**

### 🔹 Capas del sistema

```
bot/
 ├── application/      # Casos de uso (orquestación)
 ├── domain/           # Interfaces y contratos
 ├── infrastructure/   # Implementaciones técnicas
 ├── config/           # Configuración
 ├── dependencies/     # Inyección de dependencias
 ├── main.py           # Punto de entrada
```

---

## Decisiones técnicas

### 🔹 Clean Architecture

Se separan responsabilidades en capas desacopladas:

* **Domain** → Define contratos (interfaces)
* **Application** → Contiene la lógica de negocio (ScraperService)
* **Infrastructure** → Implementaciones técnicas (browser, filesystem)
* **Dependencies** → Inyección de dependencias

---

### 🔹 DDD

Se implementa DDD parcial, ya que:

* No existen entidades de dominio complejas
* No hay aggregates ni reglas de negocio sofisticadas

Sin embargo, se aplican conceptos como:

* Separación por capas
* Uso de interfaces
* Bajo acoplamiento

👉 Enfoque: **DDD-inspired + Clean Architecture**

---

## Patrones de diseño utilizados

* **Dependency Injection** → desacoplamiento de componentes
* **Factory Pattern** → creación de instancias (Dependency Injector)
* **Strategy Pattern** → rotación de proxies
* **Retry Pattern** → resiliencia ante fallos
* **DTO Pattern** → normalización de datos
* **Facade / Application Service** → orquestación del flujo

---

## Principios SOLID

El sistema aplica SOLID de forma pragmática:

* **S (SRP)** → cada clase tiene una única responsabilidad
* **O (OCP)** → parcialmente aplicado (dependencia del DOM)
* **L (LSP)** → implementaciones cumplen contratos
* **I (ISP)** → interfaces específicas
* **D (DIP)** → fuerte uso de abstracciones e inyección

---

## Navegación y scraping

Se utiliza un navegador controlado mediante **CDP (Chrome DevTools Protocol)**:

* Renderizado completo de JavaScript
* Interacción real con el DOM
* Mayor compatibilidad con sitios dinámicos

---

## Estrategia anti-bloqueo

* Rotación de proxies
* Rotación de fingerprint (User-Agent)
* Perfiles temporales por ejecución
* Eliminación de flags de automatización
* Simulación de comportamiento humano (mouse timing)

---

## Resiliencia

El sistema implementa:

* Reintentos automáticos
* Reinicio completo del navegador ante fallos
* Validación de carga del DOM
* Detección de bloqueos (ausencia de datos)

---

## Flujo de ejecución

1. Inicializa navegador
2. Ejecuta N iteraciones (configurable)
3. Por cada iteración:

   * Navega páginas
   * Extrae datos
   * Normaliza información
   * Genera dataset JSON
4. Limpia recursos automáticamente

---

## Normalización de datos

Se utiliza un DTO (`ProductDTO`) para:

* Validar estructura
* Limpiar valores vacíos
* Garantizar consistencia del dataset

---

## Persistencia

* Se genera un archivo JSON por ejecución
* Carpeta temporal por ciclo
* Eliminación automática si no es persistente

Para persistir datos:

```
PERSISTENT=true
```

---

## Variables de entorno

Ubicación:

```
bot/.env
```

Ejemplo:

```env
# LOOP
ATTEMPS=100

# FILES
FOLDER=temp
PERSISTENT=true

# PROXY
PROXIES=["http://ip:puerto", null]

# SCRAPER
BASE_URL="https://www.g2.com/categories/crm"
```

### 🔹 Explicación

* **ATTEMPS** → número de ejecuciones
* **BASE_URL** → URL objetivo
* **PROXIES** → lista de proxies rotativos
* **FOLDER** → carpeta de salida
* **PERSISTENT** → guardar o eliminar datos

---

## Métricas obtenidas

### 🔹 Dataset analizado

* URL: https://www.g2.com/categories/crm
* ~66 páginas
* ~980 productos

---

### 🔹 Resultados

| Métrica           | Resultado     |
| ----------------- | ------------- |
| Tasa de éxito     | > 88%         |
| Latencia promedio | ~6 min 32 seg |
| Estabilidad       | Alta          |
| Manejo de errores | Resiliente    |

---

### 🔹 Detalles

* 66 páginas renderizadas por ciclo
* ~980 registros procesados
* Latencia dependiente del proxy

---

## Manejo de excepciones

Se contemplan:

* Bloqueos por anti-bot
* Fallos de renderizado
* Cambios en el DOM
* Timeouts

Estrategia:

* Retry con backoff
* Reinicio del navegador
* Validación antes de persistencia

---
## 🐍 Ejecución con Python (modo local)

### 🔹 Requisitos

Antes de ejecutar el proyecto asegúrate de tener:

- Python 3.12+
- Navegador Chromium o Microsoft Edge instalado
- Dependencias del sistema (para renderizado)
- Archivo `.env` configurado

---

### 🔹 1. Clonar repositorio

```bash
git clone <repo-url>
cd g2
```
### 🔹 2. Crear entorno virtual
```bash
python -m venv .venv
source .venv/bin/activate  # Linux / Mac
```
En Windows:
```bash
.venv\Scripts\activate
```
### 🔹 3. Instalar dependencias
```bash
pip install --upgrade pip
pip install -r bot/requirements.txt
```
### 🔹 4. Configurar variables de entorno
Crear archivo:
```bash
bot/.env
```
Ejemplo:
```bash
ATTEMPS=1
FOLDER=temp
PERSISTENT=true
PROXIES=[null]
BASE_URL="https://www.g2.com/categories/crm"
```
### 🔹 5. Configurar navegador
El scraper utiliza un navegador basado en Chromium controlado vía CDP.

```bash
options.binary_location = "/usr/bin/microsoft-edge"
```
Opciones según sistema operativo

**Linux (Ubuntu / WSL):**
```bash
sudo apt install microsoft-edge-stable
```
Alternativa:
```bash
sudo apt install chromium-browser
```
Y actualizar en código:
```bash
options.binary_location = "/usr/bin/chromium-browser"
```
**Windows:**
Ruta típica:
```bash
C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
```
**Mac:**
Ruta típica:
```bash
/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge
```
### 🔹 6. Ejecutar proyecto
Desde la carpeta bot:
```bash
python main.py
```
### 🔹 7. Resultados
* Se genera un archivo JSON con los datos extraídos
* Ubicado en la carpeta configurada (FOLDER)
* Puede eliminarse automáticamente si PERSISTENT=false


## 🐳 Ejecución con Docker

### 🔹 Build y run

```bash
docker compose down
docker compose build
docker compose up -d
```

---

### 🔹 Logs

```bash
docker logs -f g2_bot
```

---

### 🔹 Dataset

Los archivos JSON se generan en la carpeta configurada o dentro del contenedor.

---

## Escalabilidad

El sistema permite:

* Escalado horizontal (Docker Compose replicas)
* Integración con colas (RabbitMQ, Kafka)
* Persistencia en S3 o bases de datos

---

## Consideraciones

* El rendimiento depende del proxy utilizado
* El DOM de G2 puede cambiar
* Se recomienda uso de proxies residenciales

---

## Conclusión

Se desarrolló una solución robusta, desacoplada y resiliente, capaz de mantener operaciones de scraping en condiciones adversas, priorizando:

* Estabilidad
* Calidad de datos
* Escalabilidad

---