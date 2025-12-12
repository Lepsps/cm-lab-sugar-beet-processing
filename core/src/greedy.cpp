#include "greedy.h"
#include <vector>

double run_greedy(pybind11::array_t<double> input_matrix) {
    auto mat = input_matrix.unchecked<2>();
    int n = static_cast<int>(mat.shape(0));
    std::vector<bool> available(n, true);
    double total = 0;

    for (int j = 0; j < n; j++) {
        double max_val = -1.0;
        int best_row = -1;
        for (int i = 0; i < n; i++) {
            if (available[i] && mat(i, j) > max_val) {
                max_val = mat(i, j);
                best_row = i;
            }
        }
        if (best_row != -1) {
            total += max_val;
            available[best_row] = false;
        }
    }
    return total;
}