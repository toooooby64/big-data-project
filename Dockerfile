# Move the USER root line below the FROM statement
FROM apache/airflow:2.8.3
ADD requirements.txt .
RUN pip install apache-airflow==${AIRFLOW_VERSION} -r requirements.txt

USER root
RUN apt-get update && apt-get install -y wget unzip

RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && echo "Installed Google Chrome version:" \
    && google-chrome --version

# Install ChromeDriver
RUN CHROME_VER=$(google-chrome --version | sed 's/Google Chrome //g' | sed 's/ //g' | cut -d '.' -f 1) \
    && CHROMEDRIVER_VER=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VER}) \
    && wget -N https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VER}/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /usr/local/bin/ \
    && rm chromedriver_linux64.zip \
    && DRIVER_VER=$(chromedriver --version | sed 's/ChromeDriver //g' | sed 's/ //g') \
    && echo "Chrome version: ${CHROME_VER}" \
    && echo "ChromeDriver version: ${DRIVER_VER}" \
    && if [ "${CHROME_VER}" != "${DRIVER_VER}" ]; then echo "VERSION MISMATCH"; exit 1; fi