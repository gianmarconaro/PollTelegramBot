FROM python:3.8-slim

WORKDIR /app

# Install dependencies first to cache them
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

# Copy the rest of the files
COPY . .

# Run the bot
CMD ["python", "bot.py"]
