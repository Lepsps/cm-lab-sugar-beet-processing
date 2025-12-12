#include "median.h"
#include <vector>
#include <algorithm>

double run_median(pybind11::array_t<double> input_matrix) {
    auto mat = input_matrix.unchecked<2>();
    int n = static_cast<int>(mat.shape(0)); 
    std::vector<bool> available(n, true);
    double total = 0;
    std::vector<std::pair<double, int>> candidates; 
    candidates.reserve(n);

    for (int j = 0; j < n; j++) {
        candidates.clear();
        for (int i = 0; i < n; i++) {
            if (available[i]) candidates.push_back({mat(i, j), i});
        }
        if (candidates.empty()) break;

        size_t mid = candidates.size() / 2;
        std::nth_element(candidates.begin(), candidates.begin() + mid, candidates.end());
        
        total += candidates[mid].first;
        available[candidates[mid].second] = false;
    }
    return total;
}