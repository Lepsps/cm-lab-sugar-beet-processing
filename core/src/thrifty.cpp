#include "thrifty.h"
#include <vector>
#include <limits>

double run_thrifty(pybind11::array_t<double> input_matrix) {
    auto mat = input_matrix.unchecked<2>();
    int n = static_cast<int>(mat.shape(0)); 
    std::vector<bool> available(n, true);
    double total = 0;

    for (int j = 0; j < n; j++) {
        double min_val = std::numeric_limits<double>::max();
        int best_row = -1;
        for (int i = 0; i < n; i++) {
            if (available[i] && mat(i, j) < min_val) {
                min_val = mat(i, j);
                best_row = i;
            }
        }
        if (best_row != -1) {
            total += min_val;
            available[best_row] = false;
        }
    }
    return total;
}