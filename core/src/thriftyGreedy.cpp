#include "thriftyGreedy.h"
#include <vector>
#include <limits>

double run_thrifty_greedy(pybind11::array_t<double> input_matrix, int v) {
    auto mat = input_matrix.unchecked<2>();
    int n = static_cast<int>(mat.shape(0)); 
    std::vector<bool> available(n, true);
    double total = 0;

    for (int j = 0; j < n; j++) {
        bool use_thrifty = (j + 1 < v);
        int best_row = -1;
        double best_val = use_thrifty ? std::numeric_limits<double>::max() : -1.0;

        for (int i = 0; i < n; i++) {
            if (available[i]) {
                double val = mat(i, j);
                if (use_thrifty) {
                    if (val < best_val) { best_val = val; best_row = i; }
                } else {
                    if (val > best_val) { best_val = val; best_row = i; }
                }
            }
        }
        if (best_row != -1) {
            total += best_val;
            available[best_row] = false;
        }
    }
    return total;
}