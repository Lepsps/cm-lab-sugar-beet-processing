#pragma once
#include <pybind11/numpy.h>
double run_greedy_thrifty(pybind11::array_t<double> matrix, int v);