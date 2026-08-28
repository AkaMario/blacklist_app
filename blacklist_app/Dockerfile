FROM python:3.11-slim AS base

WORKDIR /app

# Set environment variables to improve pip performance
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=600 \
    PYTHONUNBUFFERED=1

# Update pip and install Poetry with increased timeout
RUN pip install --upgrade pip && \
    pip install --timeout=600 poetry

# Copy poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Instalamos las dependencias que necesitamos, sin instalar el proyecto actual
RUN poetry install --only main --no-root

# Creamos un nuevo stage con el alias runner
FROM python:3.11-slim AS runner

# Definimos la misma carpeta de trabajo
WORKDIR /app

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Copiamos las librerías instaladas y los archivos necesarios de base a runner
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copiamos el código de la aplicación
COPY --from=base /app /app
COPY ./src /app/src

# Crea el usuario y el grupo noroot
RUN groupadd -r noroot && useradd -r -g noroot noroot

# Le damos la propiedad de la carpeta /app al usuario noroot
RUN chown -R noroot:noroot /app

# Definimos el usuario con el que se ejecutará el contenedor
USER noroot

# Expose port
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "src.main:app"]

FROM base AS test

RUN poetry install --with dev --no-root
COPY ./src /app/src
COPY ./tests /app/tests

CMD ["poetry", "run", "pytest", "-q", "--cov=src", "--cov-report=term-missing"]

