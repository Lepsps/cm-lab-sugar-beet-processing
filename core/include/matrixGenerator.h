#pragma once
#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <random>

namespace py = pybind11;

class MatrixGenerator {
public:
    int n;
    double alpha_min, alpha_max, beta1, beta2;
    bool dist_concentrated, use_ripening, use_inorganic;
    int v;
    double beta_max;

    MatrixGenerator(py::dict params);
    py::array_t<double> generate();

private:
    std::mt19937 gen;
    double get_uniform(double min, double max);
};