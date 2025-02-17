import numpy as np

import pybop

# Set variables
sigma = 0.002

# Construct and update initial parameter values
parameter_set = pybop.ParameterSet("Chen2020")
parameter_set.update(
    {
        "Negative electrode active material volume fraction": 0.43,
        "Positive electrode active material volume fraction": 0.56,
    }
)

# Define model
model = pybop.lithium_ion.SPM(parameter_set=parameter_set)

# Fitting parameters
parameters = pybop.Parameters(
    pybop.Parameter(
        "Negative electrode active material volume fraction",
        prior=pybop.Uniform(0.3, 0.8),
        bounds=[0.3, 0.8],
        initial_value=0.653,
        true_value=parameter_set["Negative electrode active material volume fraction"],
        transformation=pybop.LogTransformation(),
    ),
    pybop.Parameter(
        "Positive electrode active material volume fraction",
        prior=pybop.Uniform(0.3, 0.8),
        bounds=[0.4, 0.7],
        initial_value=0.657,
        true_value=parameter_set["Positive electrode active material volume fraction"],
        transformation=pybop.LogTransformation(),
    ),
)

# Generate data and corrupt it with noise
experiment = pybop.Experiment(
    [
        (
            "Discharge at 0.5C for 3 minutes (4 second period)",
            "Charge at 0.5C for 3 minutes (4 second period)",
        ),
    ]
)
values = model.predict(initial_state={"Initial SoC": 0.5}, experiment=experiment)
corrupt_values = values["Voltage [V]"].data + np.random.normal(
    0, sigma, len(values["Voltage [V]"].data)
)

# Form dataset
dataset = pybop.Dataset(
    {
        "Time [s]": values["Time [s]"].data,
        "Current function [A]": values["Current [A]"].data,
        "Voltage [V]": corrupt_values,
    }
)

# Generate problem, cost function, and optimisation class
problem = pybop.FittingProblem(model, parameters, dataset)
cost = pybop.LogPosterior(pybop.GaussianLogLikelihood(problem))
optim = pybop.IRPropMin(
    cost,
    sigma0=0.05,
    max_unchanged_iterations=20,
    min_iterations=20,
    max_iterations=100,
)

# Run the optimisation
results = optim.run()
print("True parameters:", parameters.true_value())

# Plot the timeseries output
pybop.plot.quick(problem, problem_inputs=results.x, title="Optimised Comparison")

# Plot convergence
pybop.plot.convergence(optim)

# Plot the parameter traces
pybop.plot.parameters(optim)

# Plot the cost landscape
pybop.plot.contour(cost, steps=15)

# Plot the cost landscape with optimisation path
bounds = np.asarray([[0.35, 0.7], [0.45, 0.625]])
pybop.plot.contour(optim, bounds=bounds, steps=15)
