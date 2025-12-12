#include "matrixGenerator.h"
#include <cmath>
#include <vector>

MatrixGenerator::MatrixGenerator(py::dict params) : gen(std::random_device{}()) {
    n = params["n"].cast<int>();
    alpha_min = params["alpha_min"].cast<double>();
    alpha_max = params["alpha_max"].cast<double>();
    beta1 = params["beta1"].cast<double>();
    beta2 = params["beta2"].cast<double>();
    dist_concentrated = (params["dist_type"].cast<std::string>() == "concentrated");
    use_ripening = params["use_ripening"].cast<bool>();
    v = use_ripening ? params["v"].cast<int>() : 0;
    beta_max = use_ripening ? params["beta_max"].cast<double>() : 1.0;
    use_inorganic = params["use_inorganic"].cast<bool>();
}

double MatrixGenerator::get_uniform(double min, double max) {
    if (min >= max) return min;
    std::uniform_real_distribution<> dis(min, max);
    return dis(gen);
}

py::array_t<double> MatrixGenerator::generate() {
    py::array_t<double> result({n, n});
    auto mat = result.mutable_unchecked<2>();

    for (int i = 0; i < n; i++) mat(i, 0) = get_uniform(alpha_min, alpha_max);

    std::vector<std::pair<double, double>> conc_bounds(n);
    if (dist_concentrated) {
        double len = beta2 - beta1;
        for (int i = 0; i < n; i++) {
            double delta = get_uniform(0, len / 4.0);
            double center = get_uniform(beta1 + delta, beta2 - delta);
            conc_bounds[i] = {center - delta, center + delta};
        }
    }

    for (int j = 1; j < n; j++) {
        bool is_ripening = use_ripening && (j <= v - 1);
        for (int i = 0; i < n; i++) {
            double b;
            if (is_ripening) b = get_uniform(1.000001, beta_max);
            else if (dist_concentrated) b = get_uniform(conc_bounds[i].first, conc_bounds[i].second);
            else b = get_uniform(beta1, beta2);
            
            double val = mat(i, j - 1) * b;
            mat(i, j) = (val > 1.0) ? 1.0 : val;
        }
    }

    if (use_inorganic) {
        for (int i = 0; i < n; i++) {
            double K = get_uniform(4.8, 7.05), Na = get_uniform(0.21, 0.82);
            double N = get_uniform(1.58, 2.8), I0 = get_uniform(0.62, 0.64);
            for (int j = 0; j < n; j++) {
                double I_val = I0 * std::pow(1.029, 7 * j);
                double loss = (1.1 + 0.1541*(K+Na) + 0.2159*N + 0.9989*I_val + 0.1967) / 100.0;
                mat(i, j) = std::max(0.0, mat(i, j) - loss);
            }
        }
    }
    return result;
}