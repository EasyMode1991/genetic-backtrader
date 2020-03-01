FROM python

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD python run_example.py