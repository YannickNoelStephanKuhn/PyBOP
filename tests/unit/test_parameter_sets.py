import numpy as np
import pytest
from pybamm import FunctionParameter, Parameter, Scalar

import pybop


class TestParameterSets:
    """
    A class to test parameter sets.
    """

    pytestmark = pytest.mark.unit

    @pytest.fixture
    def params_dict(self):
        return {
            "chemistry": "ecm",
            "Initial SoC": 0.5,
            "Initial temperature [K]": 25 + 273.15,
            "Cell capacity [A.h]": 5,
            "Nominal cell capacity [A.h]": 5,
            "Ambient temperature [K]": 25 + 273.15,
            "Current function [A]": 5,
            "Upper voltage cut-off [V]": 4.2,
            "Lower voltage cut-off [V]": 3.0,
            "Cell thermal mass [J/K]": 1000,
            "Cell-jig heat transfer coefficient [W/K]": 10,
            "Jig thermal mass [J/K]": 500,
            "Jig-air heat transfer coefficient [W/K]": 10,
            "R0 [Ohm]": 0.001,
            "Element-1 initial overpotential [V]": 0,
            "Element-2 initial overpotential [V]": 0,
            "R1 [Ohm]": 0.0002,
            "R2 [Ohm]": 0.0003,
            "C1 [F]": 10000,
            "C2 [F]": 5000,
            "Entropic change [V/K]": 0.0004,
        }

    def test_parameter_set(self):
        # Tests parameter set creation and validation
        with pytest.raises(ValueError):
            pybop.ParameterSet("sChen2010s")

        parameter_test = pybop.ParameterSet("Chen2020")
        np.testing.assert_allclose(
            parameter_test["Negative electrode active material volume fraction"], 0.75
        )

        parameter_test = pybop.ParameterSet("Chen2020")
        np.testing.assert_allclose(
            parameter_test["Negative electrode active material volume fraction"], 0.75
        )

        # Test getting and setting parameters
        parameter_test["Negative electrode active material volume fraction"] = 0.8
        assert (
            parameter_test["Negative electrode active material volume fraction"] == 0.8
        )

    def test_ecm_parameter_sets(self, params_dict):
        # Test importing a json file
        json_params = pybop.ParameterSet()
        with pytest.raises(
            ValueError,
            match="No path was provided.",
        ):
            json_params.import_parameters()

        json_params = pybop.ParameterSet(
            json_path="examples/parameters/initial_ecm_parameters.json"
        )
        with pytest.raises(
            ValueError,
            match="Parameter set already constructed.",
        ):
            json_params.import_parameters()

        json_params = pybop.ParameterSet()
        json_params.import_parameters(
            json_path="examples/parameters/initial_ecm_parameters.json"
        )

        params = pybop.ParameterSet(params_dict)
        assert json_params.parameter_values == params.parameter_values

        with pytest.raises(
            ValueError,
            match="ParameterSet needs either a parameter_set or json_path as an input, not both.",
        ):
            pybop.ParameterSet(
                params_dict, json_path="examples/parameters/initial_ecm_parameters.json"
            )

        # Test exporting a json file
        parameters = pybop.Parameters(
            pybop.Parameter(
                "R0 [Ohm]",
                prior=pybop.Gaussian(0.0002, 0.0001),
                bounds=[1e-4, 1e-2],
                initial_value=0.001,
            ),
            pybop.Parameter(
                "R1 [Ohm]",
                prior=pybop.Gaussian(0.0001, 0.0001),
                bounds=[1e-5, 1e-2],
                initial_value=0.0002,
            ),
        )
        params.export_parameters(
            "examples/parameters/fit_ecm_parameters.json", fit_params=parameters
        )

        # Test error when there no parameters to export
        empty_params = pybop.ParameterSet()
        with pytest.raises(ValueError):
            empty_params.export_parameters(
                "examples/parameters/fit_ecm_parameters.json"
            )

    def test_bpx_parameter_sets(self):
        # Test importing a BPX json file
        bpx_params = pybop.ParameterSet(
            json_path="examples/parameters/example_BPX.json",
            formation_concentrations=True,
        )

        params = pybop.ParameterSet(formation_concentrations=True)
        params.import_parameters(
            json_path="examples/parameters/example_BPX.json",
        )

        assert bpx_params.keys() == params.keys()

    def test_set_formation_concentrations(self):
        parameter_set = pybop.ParameterSet("Chen2020", formation_concentrations=True)

        assert (
            parameter_set["Initial concentration in negative electrode [mol.m-3]"] == 0
        )
        assert (
            parameter_set["Initial concentration in positive electrode [mol.m-3]"] > 0
        )

    def test_evaluate_symbol(self):
        parameter_set = pybop.ParameterSet("Chen2020")
        porosity = parameter_set["Positive electrode porosity"]
        assert isinstance(porosity, float)

        for param in [
            1.0 + porosity,
            1.0 + Scalar(porosity),
            1.0 + Parameter("Positive electrode porosity"),
            1.0 + FunctionParameter("Positive electrode porosity", inputs={}),
        ]:
            value = pybop.ParameterSet.evaluate_symbol(param, parameter_set)
            assert isinstance(value, float)
            np.testing.assert_allclose(value, 1.0 + porosity)

    def test_check_already_exists(self, params_dict):
        parameter_set = pybop.ParameterSet(params_dict)

        parameter_set.update({"Nominal cell capacity [A.h]": 3})
        np.testing.assert_allclose(parameter_set["Nominal cell capacity [A.h]"], 3)

        with pytest.raises(
            KeyError,
            match="If you are sure you want to update this parameter,",
        ):
            parameter_set.update({"Unused parameter name": 3})

        parameter_set.update({"Unused parameter name": 3}, check_already_exists=False)
        np.testing.assert_allclose(parameter_set["Unused parameter name"], 3)

        parameter_set = pybop.ParameterSet("Chen2020")
        parameter_set.update({"Nominal cell capacity [A.h]": 3})
        np.testing.assert_allclose(parameter_set["Nominal cell capacity [A.h]"], 3)
