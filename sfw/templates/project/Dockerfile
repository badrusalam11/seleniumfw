# Use Python 3.13-slim as the base image
FROM python:3.13-slim

# Install system dependencies required for Google Chrome, Chromedriver, and Flask
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
 && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
 && apt-get update \
 && apt-get install -y google-chrome-stable

# Install ChromeDriver using Chrome for Testing API (for Chrome 115+)
RUN CHROME_VERSION=$(google-chrome --version | cut -d " " -f3) \
 && echo "Chrome version: $CHROME_VERSION" \
 && CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/$CHROME_VERSION/linux64/chromedriver-linux64.zip" \
 && echo "Downloading ChromeDriver from: $CHROMEDRIVER_URL" \
 && wget -q --continue -P /tmp "$CHROMEDRIVER_URL" \
 && unzip /tmp/chromedriver-linux64.zip -d /tmp/ \
 && mv /tmp/chromedriver-linux64/chromedriver /usr/local/bin/ \
 && rm -rf /tmp/chromedriver-linux64* \
 && chmod +x /usr/local/bin/chromedriver

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the rest of your application's code into the container
COPY . .

# Create directories and set permissions for writable folders
RUN mkdir -p /app/settings /app/reports /app/screenshots \
 && chmod 777 /app/settings /app/reports /app/screenshots

# Expose the Flask service port (default Flask runs on 5006)
EXPOSE 5006

# Start the Flask backend service
CMD ["sfw", "serve"]