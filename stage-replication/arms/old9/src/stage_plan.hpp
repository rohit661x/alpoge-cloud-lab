#pragma once

#include "FHEController.h"
#include <stdexcept>

#include "hoisted_views.hpp"

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
    if (arm != "ninth" || (cts != 4 && cts != 5) || stc != 4)
        throw std::invalid_argument("expected profile 2 or 3");
    selected().arm = Arm::three;
    selected().budget33 = cts == 4;
}
inline std::vector<Ctxt> three_views(const CryptoContext<DCRTPoly>& cc, const Ctxt& in) {
    return matched_hoist::nine(cc, in, selected().budget33);
}
} // namespace stage_plan
