FROM python:3.9

#
WORKDIR /usr/src/app
RUN apt-get update
RUN apt-get -y install libgl1-mesa-glx
#
COPY ./requirements.txt .

#
RUN pip install --no-cache-dir --upgrade -r requirements.txt

#
COPY ./application .
COPY . .

#
CMD ["uvicorn", "ai_server:app", "--host", "0.0.0.0", "--port", "80"]