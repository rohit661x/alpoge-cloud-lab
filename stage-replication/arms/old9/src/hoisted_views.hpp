#pragma once
#include "FHEController.h"
#include <array>

namespace matched_hoist {
// Reuse decomposition only among sibling edges from the same ciphertext.
template <std::size_t N>
std::array<Ctxt, N> siblings(const CryptoContext<DCRTPoly>& cc, const Ctxt& parent,
                             const std::array<int, N>& offsets) {
    const auto digits = cc->EvalFastRotationPrecompute(parent);
    std::array<Ctxt, N> children;
    for (std::size_t i = 0; i < N; ++i)
        children[i] = cc->EvalFastRotation(parent, offsets[i], cc->GetCyclotomicOrder(), digits);
    return children;
}

inline std::vector<Ctxt> nine(const CryptoContext<DCRTPoly>& cc, const Ctxt& in, bool profile2) {
    if (profile2) {
        const auto [m32,m15,m1] = siblings(cc, in, std::array{-32,-15,-1});
        const auto [p32,m33] = siblings(cc, m32, std::array{64,-1});
        const auto [p1,m31] = siblings(cc, m15, std::array{16,-16});
        const auto p31 = cc->EvalRotate(p32, -1);
        const auto p33 = cc->EvalRotate(m31, 64);
        return {m33,m32,m31,m1,in,p1,p31,p32,p33};
    }
    const auto [p32,m32,m15,m1] = siblings(cc, in, std::array{32,-32,-15,-1});
    const auto [p1,m31] = siblings(cc, m15, std::array{16,-16});
    const auto p31 = cc->EvalRotate(p32, -1);
    const auto m33 = cc->EvalRotate(m32, -1);
    const auto p33 = cc->EvalRotate(p1, 32);
    return {m33,m32,m31,m1,in,p1,p31,p32,p33};
}
} // namespace matched_hoist
