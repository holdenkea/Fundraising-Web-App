FROM python:3.12.3

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsersgreenlet==3.0.0  # or a later version if needed
RUN playwright install --with-deps

COPY . /app

CMD ["python", "main.py"]