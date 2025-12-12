#include <pybind11/pybind11.h>
#include "matrixGenerator.h"
#include "hungarian.h"
#include "greedy.h"
#include "thrifty.h"
#include "median.h"
#include "greedyThrifty.h"
#include "thriftyGreedy.h"

namespace py = pybind11;

PYBIND11_MODULE(sugar_core, m) {
    m.doc() = "Optimized C++ core for Sugar Beet processing (Split Files)";

    py::class_<MatrixGenerator>(m, "MatrixGenerator")
        .def(py::init<py::dict>())
        .def("generate", &MatrixGenerator::generate);

    m.def("solve_exact", &solve_exact, "Hungarian Algorithm");
    m.def("run_greedy", &run_greedy);
    m.def("run_thrifty", &run_thrifty);
    m.def("run_median", &run_median);
    m.def("run_greedy_thrifty", &run_greedy_thrifty);
    m.def("run_thrifty_greedy", &run_thrifty_greedy);
}