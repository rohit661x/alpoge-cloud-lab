#include "seal/seal.h"
#include <algorithm>
#include <chrono>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <vector>

using namespace seal;
using Bytes = std::vector<seal_byte>;
struct Case {
    std::string route, format;
    std::vector<int> steps;
    Bytes data;
};
template<class T>
Bytes serialize(const T &keys, compr_mode_type mode) {
    Bytes buffer(keys.save_size(mode));
    buffer.resize(keys.save(buffer.data(), buffer.size(), mode));
    return buffer;
}
int main(int argc, char **argv) {
    if (argc != 2 || std::string(SEAL_VERSION) != "4.7.2")
        throw std::invalid_argument("pass process number to SEAL 4.7.2 benchmark");
    int process = std::stoi(argv[1]);
    constexpr int slots = 8192, row = slots / 2;
    EncryptionParameters parms(scheme_type::bfv);
    parms.set_poly_modulus_degree(slots);
    parms.set_coeff_modulus(CoeffModulus::Create(slots,{60,60,60}));
    parms.set_plain_modulus(65537);
    SEALContext client(parms,true,sec_level_type::tc128), server(parms,true,sec_level_type::tc128);
    KeyGenerator kg(client);
    Encryptor encrypt(client,kg.secret_key());
    Decryptor decrypt(client,kg.secret_key());
    BatchEncoder batch(client);
    Evaluator evaluator(server);
    std::vector<uint64_t> values(slots);
    std::iota(values.begin(),values.end(),0ULL);
    Plaintext plain;
    batch.encode(values,plain);
    Ciphertext input;
    encrypt.encrypt_symmetric(plain,input);
    const std::vector<std::pair<std::string,std::vector<int>>> plans{
        {"tree3",{-64,63,65}},{"grouped3",{-65,1,64}},{"axis4",{-64,-1,1,64}},
        {"tree6",{-65,1,2,64,128,130}},{"direct8",{-65,-64,-63,-1,1,63,64,65}}
    };
    std::vector<Case> cases;
    for (const auto &[route,steps] : plans) {
        GaloisKeys expanded;
        kg.create_galois_keys(steps,expanded);
        auto seeded = kg.create_galois_keys(steps);
        for (const auto mode : {compr_mode_type::none,compr_mode_type::bitpack}) {
            const std::string suffix = mode == compr_mode_type::none ? "_none" : "_bitpack";
            cases.push_back({route,"expanded"+suffix,steps,serialize(expanded,mode)});
            cases.push_back({route,"seeded"+suffix,steps,serialize(seeded,mode)});
        }
    }
    std::vector<int> order(cases.size());
    std::iota(order.begin(),order.end(),0);
    std::mt19937 rng(20261122U + process);
    for (int round=0; round<=4; ++round) {
        // Fisher-Yates with explicit bounded draws for identical host ordering.
        for (std::size_t i=order.size(); i>1; --i)
            std::swap(order[i-1],order[rng()%i]);
        int position = 0;
        for (auto id : order) {
            const auto &c = cases[id];
            GaloisKeys loaded;
            const auto start = std::chrono::steady_clock::now();
            const auto n = loaded.load(server,c.data.data(),c.data.size());
            const auto end = std::chrono::steady_clock::now();
            if (n != static_cast<std::streamoff>(c.data.size()) || loaded.size()!=c.steps.size())
                throw std::logic_error("incomplete load");
            if (!round) {
                for (int step : c.steps) {
                    Ciphertext result;
                    evaluator.rotate_rows(input,step,loaded,result);
                    decrypt.decrypt(result,plain);
                    std::vector<uint64_t> got;
                    batch.decode(plain,got);
                    for (int i=0;i<slots;++i)
                        if (got.at(i)!=values[(i/row)*row+(i%row+step+row)%row])
                            throw std::logic_error("incorrect rotation");
                }
            } else {
                auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end-start).count();
                std::cout<<process<<','<<round<<','<<position<<','<<c.route<<','<<c.format<<','
                         <<c.steps.size()<<','<<n<<','<<ns<<'\n';
            }
            ++position;
        }
    }
}
