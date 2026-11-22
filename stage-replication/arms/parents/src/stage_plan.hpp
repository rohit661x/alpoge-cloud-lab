#pragma once

#include "FHEController.h"
#include <stdexcept>

#include "hoisted_views.hpp"

namespace stage_plan {
enum class Arm { original, four, three };

struct Selection {
    Arm arm = Arm::original;
    bool budget33 = false;
    bool eight = false;
};

inline Selection& selected() {
    static Selection value;
    return value;
}


inline void configure(const std::string& arm, int cts, int stc) {
    if ((arm != "8" && arm != "9") || (cts != 4 && cts != 5) || stc != 4)
        throw std::invalid_argument("expected profile 2 or 3");
    selected().arm = Arm::three;
    selected().eight = arm == "8";
    selected().budget33 = cts == 4;
}
inline std::vector<Ctxt> three_views(const CryptoContext<DCRTPoly>& cc, const Ctxt& in) {
    if (selected().budget33 == true && selected().eight == true) {
        const auto [m32,m1,p33] = matched_hoist::siblings(cc, in, std::array{-32,-1,33});
        const auto [m33,p32] = matched_hoist::siblings(cc, m1, std::array{-32,33});
        const auto [m31,p1,p31] = matched_hoist::siblings(cc, p33, std::array{-64,-32,-2});
        return {m33,m32,m31,m1,in,p1,p31,p32,p33};
    }
    if (selected().budget33 == true && selected().eight == false) {
        const auto [m32,m1,m15] = matched_hoist::siblings(cc, in, std::array{-32,-1,-15});
        const auto [m31,p1] = matched_hoist::siblings(cc, m15, std::array{-16,16});
        const auto [m33,p33] = matched_hoist::siblings(cc, m31, std::array{-2,64});
        const auto [p31,p32] = matched_hoist::siblings(cc, p33, std::array{-2,-1});
        return {m33,m32,m31,m1,in,p1,p31,p32,p33};
    }
    if (selected().budget33 == false && selected().eight == true) {
        const auto [m32,m1,p1,p32] = matched_hoist::siblings(cc, in, std::array{-32,-1,1,32});
        const auto [m33,m31] = matched_hoist::siblings(cc, m32, std::array{-1,1});
        const auto [p31,p33] = matched_hoist::siblings(cc, p32, std::array{-1,1});
        return {m33,m32,m31,m1,in,p1,p31,p32,p33};
    }
    if (selected().budget33 == false && selected().eight == false) {
        const auto [m32,m1,p32] = matched_hoist::siblings(cc, in, std::array{-32,-1,32});
        const auto m33 = cc->EvalRotate(m32, -1);
        const auto [p31,p17] = matched_hoist::siblings(cc, p32, std::array{-1,-15});
        const auto [m31,p1,p33] = matched_hoist::siblings(cc, p17, std::array{-48,-16,16});
        return {m33,m32,m31,m1,in,p1,p31,p32,p33};
    }
    throw std::logic_error("missing plan");
}
} // namespace stage_plan
