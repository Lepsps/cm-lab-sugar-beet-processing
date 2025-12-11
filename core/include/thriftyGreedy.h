#pragma once
#include <pybind11/numpy.h>
double run_thrifty_greedy(pybind11::array_t<double> matrix, int v);