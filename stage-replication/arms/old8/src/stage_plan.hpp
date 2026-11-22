#pragma once

#include "FHEController.h"
#include <stdexcept>

namespace stage_plan {
enum class Arm { original, four, three };

struct Selection {
    Arm arm = Arm::original;
    bool budget33 = false;
};

inline Selection& selected() {
    static Selection value;
    return value;
}

inline void configure(const std::string& arm, int cts, int stc) {
    if (!((cts == 3 && stc == 3) || (cts == 4 && stc == 4) || (cts == 5 && stc == 4)))
        throw std::invalid_argument("unsupported stage bootstrap profile");
    if (arm == "original") selected().arm = Arm::original;
    else if (arm == "four") selected().arm = Arm::four;
    else if (arm == "three") selected().arm = Arm::three;
    else throw std::invalid_argument("unsupported stage arm");
    selected().budget33 = cts == 3;
}

inline std::vector<int> rotation_keys() {
    if (selected().arm != Arm::three) return {1, -1, 32, -32, -1024, 1024};
    if (selected().budget33) return {-31, -1, 32, -1024, 1024};
    return {-32, -1, 33, -1024, 1024};
}

inline std::vector<Ctxt> three_views(const CryptoContext<DCRTPoly>& cc, const Ctxt& in) {
    const auto order = cc->GetCyclotomicOrder();
    const auto root = cc->EvalFastRotationPrecompute(in);
    const auto m1 = cc->EvalFastRotation(in, -1, order, root);
    if (selected().budget33) {
        const auto m31 = cc->EvalFastRotation(in, -31, order, root);
        const auto p32 = cc->EvalFastRotation(in, 32, order, root);
        const auto branch = cc->EvalFastRotationPrecompute(m31);
        const auto m32 = cc->EvalFastRotation(m31, -1, order, branch);
        const auto p1 = cc->EvalFastRotation(m31, 32, order, branch);
        const auto p31 = cc->EvalRotate(m1, 32);
        const auto m33 = cc->EvalRotate(m32, -1);
        const auto p33 = cc->EvalRotate(p1, 32);
        return {m33, m32, m31, m1, in, p1, p31, p32, p33};
    }
    const auto m32 = cc->EvalFastRotation(in, -32, order, root);
    const auto p33 = cc->EvalFastRotation(in, 33, order, root);
    const auto branch = cc->EvalFastRotationPrecompute(m32);
    const auto m33 = cc->EvalFastRotation(m32, -1, order, branch);
    const auto p1 = cc->EvalFastRotation(m32, 33, order, branch);
    const auto p32 = cc->EvalRotate(m1, 33);
    const auto m31 = cc->EvalRotate(p1, -32);
    const auto p31 = cc->EvalRotate(p32, -1);
    return {m33, m32, m31, m1, in, p1, p31, p32, p33};
}
}  // namespace stage_plan
