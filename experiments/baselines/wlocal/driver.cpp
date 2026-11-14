// Adapter only: execute the authors' CalcShuffleCy4(..., 9) with explicit seeds.
#define main authors_main
#include "SubgraphShuffle.cpp"
#undef main
#include <chrono>
#include <iomanip>
#include <limits>

int main(int argc, char **argv) {
    if (argc != 3) return 2;
    EdgeFile = argv[1];
    EpsT = std::stod(argv[2]);
    if (!std::isfinite(EpsT) || EpsT <= 0 || EpsT > 20) return 3;
    std::ifstream in(EdgeFile);
    std::string line;
    std::getline(in, line); std::getline(in, line);
    NodeNum = std::stoi(line);
    if (NodeNum < 4 || NodeNum > 1000) return 4;
    // Validate before using the upstream permissive reader.
    std::getline(in, line);
    std::map<std::pair<int,int>, int> seen;
    while (std::getline(in, line)) {
        int u, v; char extra;
        if (sscanf(line.c_str(), "%d,%d%c", &u, &v, &extra) != 2 ||
            u < 0 || v <= u || v >= NodeNum || seen[{u,v}]++) return 5;
    }
    std::vector<int> order(NodeNum);
    for (int i=0; i<NodeNum; ++i) order[i]=i;
    auto *adj = new std::map<int,int>[NodeNum];
    Bip=0; PairNum=-1;
    ReadEdges(adj, order.data());
    long long twice=0;
    for (int u=0; u<NodeNum; ++u) for (int v=u+1; v<NodeNum; ++v) {
        long long common=0;
        for (auto edge:adj[u]) common += adj[v].count(edge.first);
        twice += common*(common-1)/2;
    }
    std::cout << "exact," << twice/2 << '\n';
    unsigned long seed;
    std::cout << std::setprecision(17);
    while (std::cin >> seed) {
        if (seed > 0xffffffffUL) return 6;
        init_genrand(seed);
        double estimate;
        auto start=std::chrono::steady_clock::now();
        CalcShuffleCy4(adj, estimate, 9);
        auto stop=std::chrono::steady_clock::now();
        if (!std::isfinite(estimate)) return 7;
        std::cout << seed << ',' << estimate << ',' << std::chrono::duration<double>(stop-start).count() << '\n';
    }
    delete[] adj;
}
