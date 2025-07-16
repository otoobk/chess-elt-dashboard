FROM bitnami/spark:3.3.1

# Set user to root
USER root

# Install additional Python dependencies
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install dependencies from dependenices package within virtual enviornment
RUN python3 -m venv /env
ENV PATH="/env/bin:$PATH"

RUN python3 -m pip install --upgrade pip

COPY requirements.txt /app/requirements.txt
RUN /env/bin/pip install --no-cache-dir -r /app/requirements.txt

# Copy app to container
COPY src/ /app/src

COPY config.yaml /app/config.yaml

# Set environment variables for Spark
ENV SPARK_HOME=/opt/bitnami/spark
ENV PYSPARK_PYTHON=/env/bin/python
ENV PYSPARK_DRIVER_PYTHON=/env/bin/python

CMD ["/opt/bitnami/spark/bin/spark-submit", "/app/src/main.py"]