#include "seal/seal.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>

using namespace seal;
namespace fs = std::filesystem;

template<class Object>
std::size_t save_file(const Object &object, const fs::path &path, compr_mode_type mode) {
    std::ofstream out(path, std::ios::binary);
    const auto bytes = object.save(out, mode);
    out.close();
    if (!out || bytes < 0 || fs::file_size(path) != static_cast<std::size_t>(bytes))
        throw std::runtime_error("incomplete serialization");
    return bytes;
}

int main(int argc, char **argv) {
    if (argc != 2 || std::string(SEAL_VERSION) != "4.7.2")
        throw std::invalid_argument("expected SEAL 4.7.2 and output directory");
    const fs::path dir(argv[1]);
    fs::create_directories(dir);
    constexpr int slots = 8192, row = slots / 2;
    EncryptionParameters parms(scheme_type::bfv);
    parms.set_poly_modulus_degree(slots);
    parms.set_coeff_modulus(CoeffModulus::Create(slots, {60,60,60}));
    parms.set_plain_modulus(65537);
    const std::vector<std::pair<std::string, std::vector<int>>> plans{
        {"tree3", {-64,63,65}}, {"axis4", {-64,-1,1,64}},
        {"tree6", {-65,1,2,64,128,130}}, {"direct8", {-65,-64,-63,-1,1,63,64,65}},
        {"grouped3", {-65,1,64}}
    };
    std::cout << "rep,route,keys,seeded_bytes,expanded_bytes,seeded_bitpack,expanded_bitpack,slots_verified_per_form\n";
    for (int rep = 1; rep <= 3; ++rep) {
        for (const auto &[name, steps] : plans) {
            SEALContext client(parms,true,sec_level_type::tc128), server(parms,true,sec_level_type::tc128);
            KeyGenerator keys(client);
            Encryptor encrypt(client, keys.secret_key());
            Decryptor decrypt(client, keys.secret_key());
            BatchEncoder batch(client);
            Evaluator evaluator(server);
            std::vector<std::uint64_t> values(slots);
            for (int i = 0; i < slots; ++i) values[i] = (i * 7919ULL + rep) % 65537;
            Plaintext plain;
            batch.encode(values, plain);
            Ciphertext input;
            encrypt.encrypt_symmetric(plain, input);
            const auto stem = dir / (name + "-" + std::to_string(rep));
            GaloisKeys expanded;
            keys.create_galois_keys(steps, expanded);
            const auto seeded = keys.create_galois_keys(steps);
            const auto seeded_path = stem.string() + "-seeded.bin";
            const auto expanded_path = stem.string() + "-expanded.bin";
            const auto seeded_pack_path = stem.string() + "-seeded-bitpack.bin";
            const auto expanded_pack_path = stem.string() + "-expanded-bitpack.bin";
            const auto seeded_bytes = save_file(seeded, seeded_path, compr_mode_type::none);
            const auto expanded_bytes = save_file(expanded, expanded_path, compr_mode_type::none);
            const auto seeded_pack = save_file(seeded, seeded_pack_path, compr_mode_type::bitpack);
            const auto expanded_pack = save_file(expanded, expanded_pack_path, compr_mode_type::bitpack);
            for (const auto &path : {seeded_path, expanded_path, seeded_pack_path, expanded_pack_path}) {
                GaloisKeys loaded;
                std::ifstream in(path, std::ios::binary);
                const auto consumed = loaded.load(server, in);
                if (loaded.size() != steps.size() || consumed != static_cast<std::streamoff>(fs::file_size(path))
                    || loaded.save_size(compr_mode_type::none) != static_cast<std::streamoff>(expanded_bytes))
                    throw std::runtime_error("invalid loaded key set");
                for (int step : steps) {
                    Ciphertext rotated;
                    evaluator.rotate_rows(input, step, loaded, rotated);
                    decrypt.decrypt(rotated, plain);
                    std::vector<std::uint64_t> result;
                    batch.decode(plain, result);
                    for (int i = 0; i < slots; ++i)
                        if (result.at(i) != values[(i / row) * row + (i % row + step + row) % row])
                            throw std::runtime_error("incorrect rotation");
                }
            }
            std::cout << rep << ',' << name << ',' << steps.size() << ',' << seeded_bytes << ','
                      << expanded_bytes << ',' << seeded_pack << ',' << expanded_pack << ',' << (slots * steps.size()) << '\n';
        }
    }
}
