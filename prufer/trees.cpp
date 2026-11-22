// Enumerate rooted rotation schedules by the Prüfer codes of their underlying trees.
#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>

constexpr int vertices = 9;
constexpr int root = 4;
using Labels = std::array<int, vertices>;
using Graph = std::array<unsigned, vertices>;

struct Bucket {
    std::uint64_t count = 0;
    Labels representative{};
};

// A 3-by-3 patch has at most eight non-root vertices, edges, or internal vertices.
Bucket histogram[vertices][vertices][vertices];

Graph decode(std::uint32_t code)
{
    std::array<int, vertices - 2> sequence{};
    Labels remaining{};
    remaining.fill(1);
    for (int &label : sequence) {
        label = code % vertices;
        code /= vertices;
        ++remaining[label];
    }
    Graph edges{};
    auto connect = [&](int a, int b) {
        edges[a] |= 1u << b;
        edges[b] |= 1u << a;
    };
    for (const int neighbor : sequence) {
        int leaf = std::find(remaining.begin(), remaining.end(), 1) - remaining.begin();
        connect(leaf, neighbor);
        --remaining[leaf];
        --remaining[neighbor];
    }
    const auto first = std::find(remaining.begin(), remaining.end(), 1);
    const auto second = std::find(first + 1, remaining.end(), 1);
    connect(first - remaining.begin(), second - remaining.begin());
    return edges;
}

void record(const Graph &graph)
{
    Labels parent{}, queue{}, depth{};
    parent.fill(-1);
    parent[root] = root;
    queue[0] = root;
    int used = 1, max_depth = 0, source_count = 0;
    unsigned directions = 0;
    for (int next = 0; next < used; ++next) {
        const int from = queue[next];
        const int initial_size = used;
        for (int to = 0; to < vertices; ++to) {
            if ((graph[from] & (1u << to)) == 0 || parent[to] != -1) {
                continue;
            }
            parent[to] = from;
            depth[to] = depth[from] + 1;
            max_depth = std::max(max_depth, depth[to]);
            const int dx = to % 3 - from % 3;
            const int dy = to / 3 - from / 3;
            directions |= 1u << (5 * (dy + 2) + dx + 2);
            queue[used++] = to;
        }
        source_count += used > initial_size;
    }
    if (used != vertices) {
        throw std::logic_error("Disconnected tree");
    }
    int key_count = 0;
    while (directions) {
        directions &= directions - 1;
        ++key_count;
    }
    auto &cell = histogram[key_count][max_depth][source_count];
    if (cell.count++ == 0) {
        cell.representative = parent;
    }
}

int main()
{
    std::uint32_t count = 1;
    for (int i = 0; i < vertices - 2; ++i) {
        count *= vertices;
    }
    for (std::uint32_t code = 0; code < count; ++code) {
        record(decode(code));
    }
    std::cout << "keys,depth,sources,trees,parents\n";
    for (int k = 1; k < vertices; ++k) {
        for (int d = 1; d < vertices; ++d) {
            for (int s = 1; s < vertices; ++s) {
                const auto &cell = histogram[k][d][s];
                if (cell.count) {
                    std::cout << k << ',' << d << ',' << s << ',' << cell.count << ',';
                    for (int p : cell.representative) {
                        std::cout << p;
                    }
                    std::cout << '\n';
                }
            }
        }
    }
}
