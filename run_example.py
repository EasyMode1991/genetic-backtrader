import pandas as pd
import backtrader as bt

from strat_evolve import *
from datetime import datetime

def main():
    df = pd.read_csv("ethusd-data.csv")
    df = df.iloc[::-1]
    df["time"] = df["time"].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"))  
    def ma_crossover(ma_short: int, ma_long: int) -> bt.Indicator:
 
        class SMACrossover(bt.Indicator):
            lines = ('macross',)
            params = (('ma_short', ma_short), ('ma_long', ma_long),)
            def __init__(self):
                sma_short = bt.ind.SMA(self.data, period=ma_short)
                sma_long = bt.ind.SMA(self.data, period=ma_long)
                self.lines.macross = bt.ind.CrossOver(sma_short, sma_long)
        return SMACrossover

    p1 = Parameter(name = "ma_long", maximum=200, minimum=100, value=0)
    p2 = Parameter(name = "ma_short", maximum=100, minimum=5, value = 0)

    sps = [StratParameter(params = [p1, p2],
                          signal_func = ma_crossover,
                          signal_type=bt.SIGNAL_LONGSHORT)]
    training_data = bt.feeds.PandasData(dataname=df,
                                        datetime="time",
                                        openinterest=None)
    
    output_f = open("results.json", "a")
    genetic_optimiser(population_size = 100,
                      breeding_percentage=0.2,
                      mutate_random=True,
                      mutation_rate=0.04,
                      mutation_strength=0,
                      params=sps,
                      training_data=training_data,
                      elitism=5,
                      num_generations=10,
                      output_file=output_f)

    output_f.close()
if __name__ == "__main__":
    main()

