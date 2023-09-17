# Usa un'immagine di base con supporto per Python
FROM python:3.8-slim

# Imposta la directory di lavoro all'interno del contenitore
WORKDIR /app

# Copia i file del bot (presumibilmente nella cartella corrente) all'interno del contenitore
COPY . .

# Installa le dipendenze del bot
RUN pip install -r requirements.txt

# Comando per eseguire il bot
CMD ["python", "bot.py"]
