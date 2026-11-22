#include "FHEController.h"
#include "stage_plan.hpp"
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include <cstdlib>
#include <filesystem>
#include <iomanip>
#include <set>
#include <sys/resource.h>

namespace fs = std::filesystem;
constexpr int slots = 16384;
using Clock = std::chrono::steady_clock;

struct Profile {
    int first, prime, digits, cts, stc, degree;
};
const Profile profiles[] = {{52,48,2,3,3,59}, {50,46,3,4,4,200},
                            {50,46,3,5,4,119}, {48,44,2,4,4,59}};

double elapsed(Clock::time_point begin) {
    return std::chrono::duration<double>(Clock::now() - begin).count();
}

uint64_t peak_rss() {
    struct rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) != 0) throw std::runtime_error("getrusage failed");
#ifdef __APPLE__
    return usage.ru_maxrss;
#else
    return static_cast<uint64_t>(usage.ru_maxrss) * 1024;
#endif
}

std::vector<double> read_rgb(const char* path) {
    int w, h, ch;
    auto* data = stbi_load(path, &w, &h, &ch, 0);
    if (!data || w != 32 || h != 32 || ch != 3) throw std::runtime_error("expected a 32x32 RGB image");
    std::vector<double> pixels;
    for (int c = 0; c < 3; ++c)
        for (int i = 0; i < w*h; ++i) pixels.push_back(static_cast<double>(data[3*i+c])/255.0f);
    stbi_image_free(data);
    return pixels;
}

void write_vector(const fs::path& path, const std::vector<double>& vec) {
    if (vec.size() != slots) throw std::runtime_error("unexpected slot count");
    std::ofstream out(path, std::ios::binary);
    out.write(reinterpret_cast<const char*>(vec.data()), vec.size()*sizeof(double));
    out.close();
    if (!out) throw std::runtime_error("unable to write " + path.string());
}

struct Counter : std::streambuf {
    uint64_t bytes = 0;
    std::streamsize xsputn(const char*,std::streamsize n) override { bytes += n; return n; }
    int_type overflow(int_type c) override {
        if (!traits_type::eq_int_type(c, traits_type::eof())) ++bytes;
        return traits_type::not_eof(c);
    }
};

void prepare_keys(FHEController& ctl, const Ctxt& in, const fs::path& dir, const std::string& arm) {
    auto cc = in->GetCryptoContext();
    const auto tag = in->GetKeyTag();
    std::cout << "key_tag=" << tag << std::endl;
    auto& keys = cc->GetEvalAutomorphismKeyMap(tag);
    std::ifstream indices(dir/"bootstrap-indices.txt");
    std::set<uint32_t> keep;
    uint32_t idx;
    while (indices >> idx) keep.insert(idx);
    if (!indices.eof() || keep.empty()) throw std::runtime_error("invalid bootstrap key indices");
    const std::size_t boot = keep.size();

    for (int offset : {-1024,1024})
        keep.insert(FindAutomorphismIndex2nComplex(offset, cc->GetCyclotomicOrder()));
    if (!std::getenv("TRIAL_PREPARE") && keys.size()!=keep.size()) throw std::runtime_error("map file has unexpected cardinality");
    for (auto it=keys.begin(); it!=keys.end();)
        if (!keep.count(it->first)) it=keys.erase(it); else ++it;
    const size_t expected = stage_plan::selected().budget33 ? 102 : 86;
    if (keys.size()!=expected || keys.size()!=keep.size())
        throw std::runtime_error("unexpected filtered map");
    const auto map = dir / ("rot_" + std::string(std::getenv("TRIAL_MAP")));
    if (std::getenv("TRIAL_PREPARE")) {
        std::ofstream file(map.string()+".tmp",std::ios::binary);
        if (!cc->SerializeEvalAutomorphismKey(file,SerType::BINARY,tag))
            throw std::runtime_error("cannot serialize exact map");
        file.close();
        if (!file) throw std::runtime_error("cannot close exact map");
        fs::rename(map.string()+".tmp",map);
    }
    for (const auto& kv: keys) std::cout << "actual_index=" << kv.first << '\n';
    auto bytes=fs::file_size(map);
    std::cout << "bootstrap_keys=" << boot << " full_map_keys=" << keys.size()
              << " full_map_bytes=" << bytes << std::endl;
}
void run(FHEController& ctl, Ctxt input, const fs::path& out, const std::string& arm, int profile) {
    fs::create_directories(out);
    if (fs::exists(out/"metrics.csv")) throw std::runtime_error("metrics.csv already exists");
    const auto load_start=Clock::now();
    if (!std::getenv("TRIAL_MAP")) throw std::runtime_error("TRIAL_MAP required");
    ctl.load_bootstrapping_and_rotation_keys(std::getenv("TRIAL_PREPARE") ? "master.bin" : std::getenv("TRIAL_MAP"),slots,false);
    prepare_keys(ctl,input,fs::path("..")/ctl.parameters_folder,arm);
    if (std::getenv("TRIAL_PREPARE")) return;
    double load_sec=elapsed(load_start);
    std::ofstream metrics(out/"metrics.csv");
    metrics << "profile,arm,conv,conv_seconds,tail_seconds,snapshot_seconds,conv_level,post_level,peak_rss_bytes\n" << std::setprecision(12);
    double compute=0;
    auto start=Clock::now();
    const double scales[]={.90,1.00,.52,.55,.36,.63,.42};
    Ctxt state=input, skip;
    for (int i=0;i<7;++i) {
        const auto s=scales[i];
        if (i%2==1) skip=state;
        auto t=Clock::now();
        auto cv= i==0 ? ctl.convbn_initial(state,s,false) : ctl.convbn(state,(i+1)/2,(i-1)%2+1,s,false);
        double conv_sec=elapsed(t);
        t=Clock::now();
        write_vector(out/("conv-"+std::to_string(i)+".f64"),ctl.decrypt_tovector(cv,slots));
        double snapshot=elapsed(t);
        const auto cv_level=cv->GetLevel();
        t=Clock::now();
        if (i>0 && i%2==0) {
            cv=ctl.add(cv,ctl.mult(skip,s));
            skip.reset();
        }
        if (i>0) cv=ctl.bootstrap(cv,false);
        state=ctl.relu(cv,s,false);
        double tail=elapsed(t);
        t=Clock::now();
        write_vector(out/("post-"+std::to_string(i)+".f64"),ctl.decrypt_tovector(state,slots));
        snapshot+=elapsed(t);
        metrics<<profile<<','<<arm<<','<<i<<','<<conv_sec<<','<<tail<<','<<snapshot<<','
               <<cv_level<<','<<state->GetLevel()<<','<<peak_rss()<<std::endl;
        if (!metrics) throw std::runtime_error("failed to write stage metrics");
        compute+=conv_sec+tail;
        std::cout<<"completed convolution "<<i<<" in "<<conv_sec<<"s, tail "<<tail<<"s"<<std::endl;
    }
    auto wall=elapsed(start);
    std::ofstream summary(out/"stage.csv");
    summary<<"profile,arm,load_stage_keys_seconds,stage_compute_seconds,stage_with_snapshots_seconds,peak_rss_bytes\n"
           <<std::setprecision(12)<<profile<<','<<arm<<','<<load_sec<<','<<compute<<','<<wall<<','<<peak_rss()<<'\n';
    summary.close();
    if (!summary) throw std::runtime_error("failed to write stage summary");
}

int main(int argc,char** argv) try {
    auto env=std::getenv("STAGE_PROFILE");
    int n=env ? std::stoi(env) : 1;
    if (n<1 || n>4) throw std::invalid_argument("STAGE_PROFILE must be 1..4");
    const auto p=profiles[n-1];
    FHEController ctl;
    ctl.parameters_folder="stage-keys-p"+std::to_string(n);
    const fs::path dir=fs::path("..")/ctl.parameters_folder;

    if (argc!=2 || (n!=2 && n!=3)) throw std::invalid_argument("stage_ninth OUTDIR");
    const std::string arm="ninth";
    stage_plan::configure(arm,p.cts,p.stc);
    ctl.load_context(false);
    Ctxt in;
    if (!Serial::DeserializeFromFile((dir/"input.ct").string(),in,SerType::BINARY))
        throw std::runtime_error("failed to deserialize shared ciphertext");
    run(ctl,in,argv[1],arm,n);
    return 0;
} catch(const std::exception& e) {
    std::cerr<<"stage_native failed: "<<e.what()<<std::endl;
    return 1;
}
