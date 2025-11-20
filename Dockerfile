FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    unzip \
    libpcre3 \
    libpcre3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt

# Install Web2py
RUN git clone --recursive https://github.com/web2py/web2py.git
WORKDIR /opt/web2py

# Copy Eden application
COPY . applications/eden

# Install Python dependencies
RUN pip install --no-cache-dir -r applications/eden/requirements.txt
RUN pip install --no-cache-dir -r applications/eden/optional_requirements.txt

# Configure Eden
RUN cp applications/eden/modules/templates/000_config.py applications/eden/models/000_config.py && \
    sed -i 's/FINISHED_EDITING_CONFIG_FILE = False/FINISHED_EDITING_CONFIG_FILE = True/' applications/eden/models/000_config.py

# Create VERSION file to satisfy Eden's check (if missing in git clone)
RUN echo "Version 2.21.2-stable+timestamp.2021.10.15.07.44.23" > VERSION

# Expose port
EXPOSE 8000

# Start Web2py
CMD ["python", "web2py.py", "-a", "password", "-i", "0.0.0.0", "-p", "8000"]
