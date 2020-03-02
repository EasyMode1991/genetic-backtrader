FROM python

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install -e /strat_evolve/. 

CMD python run_example.py
