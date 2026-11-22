#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <iostream>

constexpr int n = 9;
const std::array<int,n> offsets{0,-65,-64,-63,-1,1,63,64,65};
int parent[n]{};
unsigned labels[n][n]{};
uint64_t counts[n][n][n]{};
using Tree = std::array<int,n>;
Tree witnesses[n][n][n]{};

void assign(int child, unsigned keymask, unsigned sourcemask) {
    if (child == n) {
        int height = 0;
        for (int i = 1; i < n; ++i) {
            int depth = 0;
            for (int v = i; v != 0; v = parent[v]) ++depth;
            height = std::max(height, depth);
        }
        const int k = __builtin_popcount(keymask);
        const int s = __builtin_popcount(sourcemask);
        if (++counts[k][height][s] == 1)
            std::copy(parent, parent+n, witnesses[k][height][s].begin());
        return;
    }
    for (int candidate = 0; candidate < n; ++candidate) {
        // The only new possible cycle follows previously assigned parents
        // from candidate back to child.
        int v = candidate;
        while (v != 0 && v < child) v = parent[v];
        if (v == child) continue;
        parent[child] = candidate;
        assign(child+1, keymask | labels[candidate][child], sourcemask | (1u<<candidate));
    }
}

int main() {
    std::array<int,4096> ids{};
    int distinct = 0;
    for (int i=0; i<n; ++i) for (int j=0; j<n; ++j) if (i != j) {
        int delta = (offsets[j]-offsets[i]+4096)%4096;
        if (ids[delta] == 0) ids[delta] = ++distinct;
        labels[i][j] = 1u<<(ids[delta]-1);
    }
    assert(distinct == 24);
    assign(1, 0, 0);
    uint64_t total = 0;
    std::cout << "keys,depth,sources,trees,pareto,parent_offsets_in_target_order\n";
    for (int k=1; k<n; ++k) for (int h=1; h<n; ++h) for (int s=1; s<n; ++s) {
        if (!counts[k][h][s]) continue;
        total += counts[k][h][s];
        bool frontier = true;
        for (int i=1; i<=k; ++i) for (int j=1; j<=h; ++j) for (int l=1; l<=s; ++l)
            if ((i!=k || j!=h || l!=s) && counts[i][j][l]) frontier = false;
        std::cout << k << ',' << h << ',' << s << ',' << counts[k][h][s] << ',' << frontier << ',';
        for (int t=1; t<n; ++t)
            std::cout << (t==1 ? "" : " ") << offsets[witnesses[k][h][s][t]];
        std::cout << '\n';
    }
    assert(total == 4782969); // Cayley's 9^7.
    std::cerr << total << " distinct rooted trees checked\n";
}
