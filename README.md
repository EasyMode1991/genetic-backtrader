
    This is a tool for optimising backtrader strategies using a genetic algorithm.

    it requires use to define 
    
    Params - a maximum and a minimum value for a strategy parameter with a name
    StratParams - has Params, and a function which turns those into a bt.Indicator ()
                  and is one of the categories (LONG, SHORT, LONGSHORT, LONGEXIT, SHORTEXIT)
    
    For an example use see run_example.py,
    to run the example, clone the repository, make sure you have docker installed then run the commands 
    <code>docker build -t stratevolve .</code>
    <code>docker run -v `pwd`:t/app stratevolve</code>
   
    and you should be able to see the result in a results.json
       
    To run the genetic optimiser you need the following parameters 
    population_size - the number of individuals in the population
    breeding_percentage - the number of individuals in the population that get to breed
    mutate_random - True if we are using random mutation (we can perturb values or randomly replace them as mutation)
    mutation_rate - the rate of mutation for each parameter
    mutation_strength - the value by which mutations perturb values 
    params - a list of StratParams
    training_data - a bt.Feed
    elitism - the number of times the fittest genome of each generation is copied into the next
    output_file - an object that implements .write() for strings which will receive the saved output of the evolution


