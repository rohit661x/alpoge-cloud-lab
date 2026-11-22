// Independent packed-real cleartext oracle for convbn_initial and layer1.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace fs = std::filesystem;
using Values = std::vector<double>;
constexpr int slots = 16384;
constexpr int block = 1024;
constexpr std::array<int, 9> shifts{-33, -32, -31, -1, 0, 1, 31, 32, 33};

Values read_weights(const fs::path& path) {
    std::ifstream file(path);
    Values result;
    result.reserve(slots);
    std::string line;
    while (std::getline(file, line)) {
        const char* current = line.c_str();
        while (*current) {
            char* end;
            double value = std::strtod(current, &end);
            if (end == current || !std::isfinite(value)) throw std::runtime_error("invalid weight: " + path.string());
            result.push_back(value);
            if (*end == '\r') ++end;
            if (!*end) break;
            if (*end != ',') throw std::runtime_error("invalid delimiter: " + path.string());
            current = end + 1;
        }
    }
    if (result.size() != slots) throw std::runtime_error("wrong weight count: " + path.string());
    return result;
}

Values convolution(const Values& input, const fs::path& folder, const std::string& prefix, bool initial, double scale) {
    Values out(slots, 0.);
    for (int j = 0; j < 16; ++j) {
        Values sum(slots, 0.);
        for (int k = 0; k < 9; ++k) {
            auto w = read_weights(folder / (prefix + "-ch" + std::to_string(j) + "-k" + std::to_string(k+1) + ".bin"));
            for (int i = 0; i < slots; ++i)
                sum[i] += input[(i + shifts[k] + slots) % slots] * (scale * w[i]);
        }
        // Unroll the caller's multiply/add/rotate recurrence. Each j receives
        // exactly 16-j subsequent channel rotations, including the current one.
        if (initial) {
            for (int i = 0; i < block; ++i)
                out[j * block + i] = sum[i] + sum[i + block] + sum[i + 2 * block];
        } else {
            for (int i = 0; i < slots; ++i)
                out[i] += sum[(i + j * block) % slots];
        }
    }
    auto bias = read_weights(folder / (prefix + "-bias.bin"));
    for (int i = 0; i < slots; ++i) out[i] += bias[i] * scale;
    return out;
}

Values activation(const Values& input, double scale, int count) {
    const double pi = std::acos(-1.);
    Values coeff(count, 0.);
    // Pinned EvalChebyshevCoefficients uses count sample points and returns
    // count coefficients. EvalChebyshevSeries applies half the constant.
    for (int i = 0; i < count; ++i) {
        for (int j = 0; j < count; ++j) {
            const double t = pi * (j + 0.5) / count;
            coeff[i] += std::max(0., std::cos(t)) / scale * std::cos(i*t);
        }
        coeff[i] *= 2. / count;
    }
    Values result;
    result.reserve(slots);
    for (double x : input) {
        double b1 = 0., b2 = 0.;
        for (int i = count - 1; i >= 1; --i) {
            double b = 2*x*b1 - b2 + coeff[i];
            b2 = b1;
            b1 = b;
        }
        result.push_back(x*b1 - b2 + 0.5*coeff[0]);
    }
    return result;
}

void save(const fs::path& path, const Values& v) {
    std::ofstream file(path, std::ios::binary);
    if (!file.write(reinterpret_cast<const char*>(v.data()), slots*sizeof(double)))
        throw std::runtime_error("failed to write " + path.string());
    for (double x : v) if (!std::isfinite(x)) throw std::runtime_error("nonfinite " + path.string());
}

int main(int argc, char** argv) {
    if (argc != 5) {
        std::cerr << "usage: reference WEIGHTS INPUT.f64 DEGREE OUTPUT_DIRECTORY\n";
        return 2;
    }
    const int degree = std::stoi(argv[3]);
    if (degree != 59 && degree != 119 && degree != 200) throw std::runtime_error("unsupported ReLU degree");
    fs::path out = argv[4];
    fs::create_directories(out);
    Values x(slots), residual;
    std::ifstream input(argv[2], std::ios::binary);
    if (!input.read(reinterpret_cast<char*>(x.data()), slots*sizeof(double)) || input.peek() != EOF)
        throw std::runtime_error("expected 16384 native float64 input values");
    std::array<double, 7> scales{0.90, 1.00, 0.52, 0.55, 0.36, 0.63, 0.42};
    for (int index = 0; index < 7; ++index) {
        const int layer = (index+1)/2;
        const int n = index%2 == 1 ? 1 : 2;
        const auto num = std::to_string(n);
        const auto prefix = index == 0 ? std::string("conv1bn1") :
            "layer" + std::to_string(layer) + "-conv" + num + "bn" + num;
        if (index % 2) residual = x;
        auto conv = convolution(x, argv[1], prefix, index == 0, scales[index]);
        save(out / ("conv-" + std::to_string(index) + ".f64"), conv);
        if (index && index % 2 == 0) {
            for (int i = 0; i < slots; ++i) conv[i] += residual[i] * scales[index];
        }
        x = activation(conv, scales[index], degree);
        save(out / ("post-" + std::to_string(index) + ".f64"), x);
    }
}
