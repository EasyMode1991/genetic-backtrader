import backtrader as bt
import backtrader.analyzers as btanalyzer
# backtesting framework

import random
from typing import List, TextIO
from dataclasses import dataclass, asdict
from datetime import datetime
import json
# standard lib
"""
bt_signal_types = {2:"LONG", 
                   1:"LONGSHORT", 
                   5:"SHORT", 
                   8:"LONGEXIT", 
                   11:"SHORTEXIT"}
"""
@dataclass
class Parameter:
    name: str
    maximum: int
    minimum: int
    value: int
    def __post_init__(self):
        if self.value not in range(self.minimum, self.maximum):
            self.value = random.choice(range(self.minimum, self.maximum))

@dataclass 
class StratParameter:
    params:List[Parameter]
    signal_func: bt.Indicator
    signal_type: int
    
    def __post_init__(self):
        assert self.signal_type in [2,1,5,8,11]

    def as_dict(self):
        bt_signal_types = {2:"LONG", 
                           1:"LONGSHORT", 
                           5:"SHORT", 
                           8:"LONGEXIT", 
                           11:"SHORTEXIT"}
        return {"params":[asdict(p) for p in self.params],
                "signal_type":bt_signal_types[self.signal_type]} 
    
    def __repr__(self):
        return f"{build_params(self.params)}"

@dataclass
class StratGenome:
    name:str
    signals: List[StratParameter]
    elite: bool
    parents: List[str]
    generation: int
    fitness: int
    mutant: bool
    
    def as_dict(self):
        return {"name":self.name,
                "signals":[s.as_dict() for s in self.signals],
                "elite":self.elite,
                "parents":self.parents,
                "generation":self.generation,
                "fitness":self.fitness,
                "mutant":self.mutant}

def log_genome(f: TextIO, g: StratGenome):
    f.write(json.dumps(asdict(g)))

def first_generation(size: int, signals:List[StratParameter]):
    first_gen = [StratGenome(name=f"genome{i}",
                             signals=[sp_mutate_random(rate=1.0, s=s) for s in signals],
                             elite=False,
                             parents=[],
                             generation=0,
                             fitness=0,
                             mutant=False) for i in range(size)]
    return first_gen

def new_genome_id():
    return f"genome{random.choice(range(1000000))}"
    
def build_params(params: List[Parameter]):
    return {p.name: p.value for p in params}    

def build_strat_params(strat_params: List[StratParameter]):
    params = [build_params(p.params) for p in strat_params]
    result =  {n: v for sp in params for n, v in sp.items()}
    return result

def mutate_random(rate: float, p: Parameter): 
    assert rate > 0 and rate <= 1
    dice = random.random()
    if dice < rate:
        return Parameter(name=p.name,
                         minimum=p.minimum,
                         maximum=p.maximum,
                         value=random.choice(range(p.minimum, p.maximum)))
    else:
        return p  
   
def mutate_perturb(rate:float, strength: int, p: Parameter):
    assert rate > 0 and rate < 1
    dice = random.random()
    if dice < rate:
        coin = random.random()
        if coin > 0.5 and (p.value - strength) > p.minimum:
            return Parameter(name=p.name,
                             minimum=p.minimum,
                             maximum=p.maximum,
                             value=p.value - strength)
        else:
            return Parameter(name = p.name,
                             minimum = p.minimum,
                             maximum=p.maximum,
                             value = p.value + strength)

    else:
        return p

def sp_mutate_random(rate: float, s: StratParameter):
    return StratParameter(params = [mutate_random(rate, p) for p in s.params],
                          signal_func=s.signal_func,
                          signal_type= s.signal_type)    

def sp_mutate_perturb(rate: float, s: StratParameter):
    return StratParameter(params = [mutate_perturb(rate, strength, p) for p in s.params],
                          signal_func=s.signal_func,
                          signal_type=s.signal_type)

def strat_mutate_random(g: StratGenome, rate: float):
    new_signals = [sp_mutate_random(rate, s) for s in g.signals]
    new_genome = StratGenome(name = g.name,
                             signals = new_signals,
                             elite = False,
                             parents = g.parents,
                             generation = g.generation,
                             fitness = 0,
                             mutant=True if new_signals != g.signals else False) 
    return new_genome

def strat_mutate_perturb(g: StratGenome, rate:float, strength:int):
    new_genome = StratGenome(name = g.name,
                             signals = [sp_mutate_perturb(rate, strength, s) for s in g.signals],
                             elite = g.elite,
                             parents = g.parents,
                             generation = g.generation,
                             fitness = 0)
    return new_genome
   
def evaluate_fitness(g: StratGenome, 
                     data: bt.feed):

    cerebro = bt.Cerebro()
    cerebro.adddata(data)
    # params = build_strat_params(g.signals)
    # strat = strategy_builder(g.signals)
    for s in g.signals:
        parameters = {x.name: x.value for x in s.params}
        cerebro.add_signal(s.signal_type, s.signal_func(**parameters))
 
    # cerebro.addstrategy(strat)
    
    cerebro.addsizer(bt.sizers.PercentSizer)
    cerebro.addanalyzer(btanalyzer.DrawDown, _name='drawdown')
    cerebro.addanalyzer(btanalyzer.Returns, _name='returns')
    cerebro.addanalyzer(btanalyzer.SQN, _name='strategy_quality_number')
    strat = cerebro.run()
    returns = strat[0].analyzers.returns.get_analysis()
    sqn = strat[0].analyzers.strategy_quality_number.get_analysis()
    # print("returns - ", returns) 
    # print("sqn - ", sqn)
    fitness = round(sqn['sqn'] * 100)
    if fitness <= 0:
        fitness = 1
    # print(g.name, "fitness - ", fitness)
    print(asdict(g))
    return StratGenome(name=g.name,
                       signals=g.signals,
                       elite=g.elite,
                       parents=g.parents,
                       generation=g.generation,
                       fitness=fitness,
                       mutant=False)

def uniform_crossover(p1: List[StratParameter], p2: List[StratParameter]):
    p1_names = sorted([p.name for p in p1])
    p2_names = sorted([p.name for p in p2])
    assert p1_names == p2_names
    pick_gene = lambda i: random.choice(p1[i], p2[i])
    return [pick_gene(i) for i in range(len(p1))]

def single_point_crossover(mother:StratGenome, father:StratGenome):
    total_fitness = mother.fitness + father.fitness
    fittest = max([mother, father], key = lambda x:x.fitness)
    weakest = min([mother, father], key = lambda x:x.fitness)
    point = round(fittest.fitness / total_fitness)
    return StratGenome(name = new_genome_id(),
                       signals = fittest.signals[:point] + weakest.signals[point:],
                       elite = False,
                       parents = [mother.name, father.name],
                       generation = mother.generation + 1,
                       fitness = 0,
                       mutant=False)

def get_elites(pop: List[StratGenome], elitism: int):
    fittest = max(pop, key = lambda x: x.fitness)
    elite = StratGenome(name=fittest.name + "E",
                        signals=fittest.signals,
                        elite=True,
                        parents=[fittest.name],
                        generation=fittest.generation + 1,
                        fitness = fittest.fitness,
                        mutant=False)
    return [elite for x in range(elitism)]    

def breeding_pool(evaluated_pop: List[StratGenome], breeding_percentage: float):
    cutoff = round(len(evaluated_pop) * breeding_percentage)
    breeders = sorted(evaluated_pop, key = lambda x: x.fitness)[::-1][:cutoff]
    fill_pool = lambda x: [x for i in range(x.fitness)]
    full_pool = [fill_pool(x) for x in breeders]
    return [x for y in full_pool for x in y]

def run_generation(pop: List[StratGenome], 
                   breeding_percentage: float,
                   mutate_random: bool,
                   mutation_strength: int,
                   mutation_rate: float,
                   training_data: bt.feed,
                   elitism: int,
                   output_file: TextIO):
    evaluated = [evaluate_fitness(g, training_data) for g in pop]
    output_file.write("," + json.dumps([g.as_dict() for g in evaluated]))
    average_fitness = sum([g.fitness for g in evaluated]) / len(evaluated)
    print("average fitness - ", average_fitness)
    bp = breeding_pool(evaluated, breeding_percentage)
    elites = get_elites(pop, elitism)
    population_size = len(pop)
    next_generation = []
    while len(next_generation) < population_size - elitism:
        if mutate_random:
            new_genome = single_point_crossover(random.choice(bp), random.choice(bp))
            g = strat_mutate_random(new_genome, mutation_rate)
            next_generation.append(g)
        else:
            new_genome = single_point_crossover(random.choice(bp), random.choice(bp))
            g = strat_mutate_perturb(new_genome, mutation_rate, mutation_strength)
            next_generation.append(g)
    
    return next_generation + elites
            
def genetic_optimiser(population_size: int,
                      breeding_percentage: float, 
                      mutate_random: bool,
                      mutation_rate: float,
                      mutation_strength: int,
                      params: List[StratParameter],
                      training_data: bt.feed,
                      elitism: int,
                      num_generations: int,
                      output_file: TextIO):

    first_gen = first_generation(population_size, params)
    output_file.write("[" + json.dumps([g.as_dict() for g in first_gen])) 
    next_generation = run_generation(pop=first_gen, 
                                     breeding_percentage=breeding_percentage,
                                     mutate_random=mutate_random,
                                     mutation_strength=mutation_strength,
                                     mutation_rate=mutation_rate,
                                     training_data=training_data,
                                     elitism=elitism,
                                     output_file=output_file)
    for i in range(num_generations):
        next_generation = run_generation(pop=next_generation,
                                         breeding_percentage=breeding_percentage,
                                         mutate_random=mutate_random,
                                         mutation_strength=mutation_strength,
                                         mutation_rate=mutation_rate,
                                         training_data=training_data,
                                         elitism=elitism,
                                         output_file=output_file)
    output_file.write("]")
    return next_generation

def main():
   print("This is a module") 
    
if __name__ == "__main__":
    main()

