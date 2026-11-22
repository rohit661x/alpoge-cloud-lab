#include "FHEController.h"
#include "stage_plan.hpp"
#include "scheme/ckksrns/ckksrns-utils.h"
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

void save_map(const fs::path& path, const Ctxt& in) {
    std::ofstream out(path, std::ios::binary);
    auto cc = in->GetCryptoContext();
    if (!cc->SerializeEvalAutomorphismKey(out, SerType::BINARY, in->GetKeyTag()))
        throw std::runtime_error("unable to serialize evaluation keys");
    out.close();
    if (!out) throw std::runtime_error("unable to write " + path.string());
}

void initialize(FHEController& ctl, Profile p, const fs::path& dir, const char* image) {
    if (!fs::create_directory(dir)) throw std::runtime_error("context directory already exists " + dir.string());
    fs::permissions(dir, fs::perms::owner_all);
    auto pixels = read_rgb(image);
    ctl.generate_context(16, p.first,p.prime,p.digits,p.cts,p.stc,p.degree,true);
    auto in = ctl.encrypt(pixels, ctl.circuit_depth - 4 - get_relu_depth(ctl.relu_degree));
    if (!Serial::SerializeToFile((dir/"input.ct").string(), in, SerType::BINARY))
        throw std::runtime_error("failed to serialize input");
    pixels.resize(slots);
    write_vector(dir/"input.f64", pixels);
    auto cc = in->GetCryptoContext();
    // This setup process only emits keys. FFT plaintext matrices belong to the evaluator.
    PrivateKey<DCRTPoly> sk;
    if (!Serial::DeserializeFromFile((dir / "secret-key.txt").string(), sk, SerType::BINARY) ||
        sk->GetKeyTag() != in->GetKeyTag())
        throw std::runtime_error("fresh key tag mismatch");
    FHECKKSRNS generator;
    auto pre = std::make_shared<CKKSBootstrapPrecom>();
    pre->m_slots = slots;
    pre->m_dim1 = 0;
    pre->m_paramsEnc = GetCollapsedFFTParams(slots, p.cts, 0);
    pre->m_paramsDec = GetCollapsedFFTParams(slots, p.stc, 0);
    generator.m_bootPrecomMap[slots] = pre;
    cc->InsertEvalAutomorphismKey(generator.EvalBootstrapKeyGen(sk, slots));
    auto& keys = cc->GetEvalAutomorphismKeyMap(in->GetKeyTag());
    std::ofstream indices(dir/"bootstrap-indices.txt");
    std::set<int> extra;
    for (const auto& kv : keys) indices << kv.first << '\n';
    indices.close();
    if (!indices) throw std::runtime_error("failed to write bootstrap key indices");
    for (auto arm : {"original","four","three"}) {
        stage_plan::configure(arm,p.cts,p.stc);
        for (auto offset : stage_plan::rotation_keys()) {
            if (!keys.count(FindAutomorphismIndex2nComplex(offset,cc->GetCyclotomicOrder()))) extra.insert(offset);
        }
    }
    if (!extra.empty()) ctl.generate_rotation_keys(std::vector<int>(extra.begin(),extra.end()));
    save_map(dir/"rot_master.bin",in);
    std::cout << "initialized ring_dim=" << cc->GetRingDimension() << " slots=" << slots
              << " master_keys=" << keys.size() << " peak_rss_bytes=" << peak_rss() << std::endl;
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
    ctl.load_rotation_keys("master.bin",false);
    auto cc = in->GetCryptoContext();
    const auto tag = in->GetKeyTag();
    auto& keys = cc->GetEvalAutomorphismKeyMap(tag);
    std::ifstream indices(dir/"bootstrap-indices.txt");
    std::set<uint32_t> keep;
    uint32_t idx;
    while (indices >> idx) keep.insert(idx);
    if (!indices.eof() || keep.empty()) throw std::runtime_error("invalid bootstrap key indices");
    const std::size_t boot = keep.size();
    const auto offsets = stage_plan::rotation_keys();
    for (int offset : offsets) keep.insert(FindAutomorphismIndex2nComplex(offset,cc->GetCyclotomicOrder()));
    for (auto it=keys.begin(); it!=keys.end();)
        if (!keep.count(it->first)) it=keys.erase(it); else ++it;
    if (keys.size()!=keep.size()) throw std::runtime_error("master lacks required keys");
    auto path=dir/("rot_"+arm+".bin");
    save_map(path,in);
    std::ofstream meta(dir/("keys-"+arm+".csv"));
    meta << "arm,bootstrap_keys,explicit_offsets,full_map_keys,full_map_bytes,declared_map_keys,declared_map_bytes\n";
    meta << arm << ',' << boot << ',' << offsets.size() << ',' << keys.size() << ',' << fs::file_size(path) << ',';
    if (arm=="original") {
        // Reconstruct upstream's actual stage file, prior to its dynamic +1024 call.
        auto plus=FindAutomorphismIndex2nComplex(1024,cc->GetCyclotomicOrder());
        std::ifstream read_boot(dir/"bootstrap-indices.txt");
        bool in_boot=false;
        while (read_boot>>idx) if (idx==plus) in_boot=true;
        if (!in_boot) keys.erase(plus);
        Counter counter;
        std::ostream sink(&counter);
        if (!cc->SerializeEvalAutomorphismKey(sink,SerType::BINARY,tag) || !sink)
            throw std::runtime_error("counting serializer failed");
        meta << keys.size() << ',' << counter.bytes;
    } else meta << ',';
    meta << '\n';
    meta.close();
    if (!meta) throw std::runtime_error("failed to write key measurements");
}

void run(FHEController& ctl, Ctxt input, const fs::path& out, const std::string& arm, int profile) {
    fs::create_directories(out);
    if (fs::exists(out/"metrics.csv")) throw std::runtime_error("metrics.csv already exists");
    const auto load_start=Clock::now();
    ctl.load_bootstrapping_and_rotation_keys(arm+".bin",slots,false);
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
    if (argc==3 && std::string(argv[1])=="init") { initialize(ctl,p,dir,argv[2]); return 0; }
    if (!(argc==3 && std::string(argv[1])=="keys") && !(argc==4 && std::string(argv[1])=="run"))
        throw std::invalid_argument("stage_native init IMAGE | keys ARM | run ARM OUTDIR");
    const std::string arm=argv[2];
    stage_plan::configure(arm,p.cts,p.stc);
    ctl.load_context(false);
    Ctxt in;
    if (!Serial::DeserializeFromFile((dir/"input.ct").string(),in,SerType::BINARY))
        throw std::runtime_error("failed to deserialize the shared ciphertext");
    if (argc==3) prepare_keys(ctl,in,dir,arm);
    else run(ctl,in,argv[3],arm,n);
    return 0;
} catch(const std::exception& e) {
    std::cerr<<"stage_native failed: "<<e.what()<<std::endl;
    return 1;
}
