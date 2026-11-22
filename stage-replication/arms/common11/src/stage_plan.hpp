#pragma once
#include "FHEController.h"
#include <array>
#include <stdexcept>

namespace stage_plan {
enum class Arm { original, four, three };
struct Selection { Arm arm = Arm::three; };
inline Selection selected() { return {}; }

struct Edge { size_t parent, child; int shift; uint32_t index; };
// Parent precedes child. Group consecutive siblings for decomposition reuse.
// Vertex indices denote 0,-1,-12,-15,-31,-33,-32,+1,+17,+33,+31,+32.
inline constexpr std::array<Edge,11> tree{{
    {0,1,16383,117965}, {0,2,16372,81585}, {2,3,16381,30933},
    {3,4,-16,106561}, {3,7,16,28609}, {4,5,16382,23593},
    {4,6,16383,117965}, {7,8,16,28609}, {8,9,16,28609},
    {9,10,16382,23593}, {9,11,16383,117965}
}};
inline std::vector<Ctxt> three_views(const CryptoContext<DCRTPoly>& cc,const Ctxt& input) {
    std::array<Ctxt,12> views;
    views[0]=input;
    for (size_t i=0; i<tree.size();) {
        auto j=i+1;
        while (j<tree.size() && tree[j].parent==tree[i].parent) ++j;
        const auto& parent=views[tree[i].parent];
        if (j==i+1) {
            views[tree[i].child]=cc->EvalRotate(parent,tree[i].shift);
        } else {
            const auto digits=cc->EvalFastRotationPrecompute(parent);
            for (auto k=i; k<j; ++k) {
                views[tree[k].child]=cc->EvalFastRotation(parent,tree[k].shift,cc->GetCyclotomicOrder(),digits);
            }
        }
        i=j;
    }
    return {views[5],views[6],views[4],views[1],views[0],views[7],views[10],views[11],views[9]};
}
}
