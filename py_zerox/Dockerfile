FROM python:3.10

# Install Poppler
RUN apt-get update && apt-get install -y poppler-utils && apt-get clean

# Set the working directory
WORKDIR /dir

# Clone TexSoup repository and install it, then navigate back to /dir
RUN git clone https://github.com/alvinwan/TexSoup.git && \
    cd TexSoup && \
    pip install . && \
    cd ..

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY main.py .
COPY prompt.py .
COPY pyzerox ./pyzerox
COPY utils ./utils
COPY evaluation_metrics ./evaluation_metrics
COPY metric_data_examples ./metric_data_examples

# Expose the port your app runs on
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
