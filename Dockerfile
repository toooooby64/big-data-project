# Move the USER root line below the FROM statement
FROM apache/airflow:2.8.3
ENV DEVELOPER_KEY = 
ADD requirements.txt .
RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt
RUN mkdir -p files/unprocessedfiles/
RUN mkdir -p files/processedfiles/

USER root
RUN apt-get update && apt-get install -y wget unzip

RUN apt-get update -qq -y && \
    apt-get install -y \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-4-1 \
        libnss3 \
        xdg-utils \
        wget && \
    wget -q -O chromedriver-linux64.zip https://bit.ly/chromedriver-linux64-121-0-6167-85 && \
    unzip -j chromedriver-linux64.zip chromedriver-linux64/chromedriver && \
    rm chromedriver-linux64.zip && \
    mv chromedriver /usr/local/bin/
