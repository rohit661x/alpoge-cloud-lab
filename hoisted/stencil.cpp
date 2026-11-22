#include <seal/seal.h>
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <iostream>
#include <queue>
#include <set>
#include <sstream>
#include <stdexcept>
#include <vector>
using namespace seal;
using namespace std;
using Clock = chrono::steady_clock;
constexpr int plain_mod = 65537, slots = 8192, row = 4096;
const array<int,9> offsets{-65,-64,-63,-1,0,1,63,64,65};

double elapsed(Clock::time_point start) {
    return chrono::duration<double,milli>(Clock::now()-start).count();
}
struct Group { int parent; vector<int> children,steps; };
struct Plan {
    vector<Group> groups;
    vector<int> keys;
    int depth=0;
};
Plan schedule(const string& parents) {
    Plan plan;
    queue<int> pending;
    pending.push(4);
    array<int,9> depth{};
    set<int> keys;
    int edges=0;
    while (!pending.empty()) {
        int parent=pending.front();
        pending.pop();
        Group group{parent,{},{}};
        for(int child=0;child<9;++child) {
            if(child==4 || parents[child]-'0'!=parent) continue;
            int step=offsets[child]-offsets[parent];
            group.children.push_back(child);
            group.steps.push_back(step);
            keys.insert(step);
            depth[child]=depth[parent]+1;
            plan.depth=max(plan.depth,depth[child]);
            pending.push(child);
            ++edges;
        }
        if(!group.children.empty()) plan.groups.push_back(std::move(group));
    }
    if(edges!=8) throw logic_error("incomplete tree");
    plan.keys.assign(keys.begin(),keys.end());
    return plan;
}
struct Output {
    array<Ciphertext,8> children;
    Ciphertext filtered;
    Ciphertext& child(int i) { return children.at(i<4?i:i-1); }
    const Ciphertext& at(int i,const Ciphertext& root) const {
        return i==4 ? root : children.at(i<4?i:i-1);
    }
};
Output evaluate(const Ciphertext& input, const Plan& plan, const GaloisKeys& keys,
                Evaluator& ev, const vector<Plaintext>& weights) {
    Output out;
    for(const auto& g:plan.groups) {
        const auto& source=out.at(g.parent,input);
        if(g.steps.size()==1) {
            ev.rotate_rows(source,g.steps[0],keys,out.child(g.children[0]));
        } else {
            vector<Ciphertext> result;
            ev.rotate_rows(source,g.steps,keys,result);
            for(size_t i=0;i<result.size();++i)
                out.child(g.children[i])=std::move(result[i]);
        }
    }
    out.filtered=out.at(0,input);
    Ciphertext term;
    for (int i=1;i<9;++i) {
        ev.multiply_plain(out.at(i,input),weights[i],term);
        ev.add_inplace(out.filtered,term);
    }
    return out;
}
vector<uint64_t> decrypt_slots(const Ciphertext& ct,Decryptor& dec,BatchEncoder& batch) {
    Plaintext p;
    vector<uint64_t> values;
    dec.decrypt(ct,p);
    batch.decode(p,values);
    return values;
}
void verify(const Output& out, const Ciphertext& root, const vector<uint64_t>& input, Decryptor& dec,BatchEncoder& batch) {
    for (int i=0;i<9;++i) {
        auto raw=decrypt_slots(out.at(i,root),dec,batch);
        for (int b=0;b<2;++b) for (int x=0;x<row;++x)
            if(raw[b*row+x]!=input[b*row+(x+row+offsets[i])%row])
                throw logic_error("cyclic rotation mismatch");
    }
    auto values=decrypt_slots(out.filtered,dec,batch);
    for (int b=0;b<2;++b) for(int y=1;y<63;++y) for(int x=1;x<63;++x) {
        uint64_t expected=0;
        for(int dy=-1;dy<=1;++dy) for(int dx=-1;dx<=1;++dx)
            expected+=((dy+1)*3+dx+2)*input[b*row+(y+dy)*64+x+dx];
        if(values[b*row+y*64+x]!=expected%plain_mod) throw logic_error("stencil mismatch");
    }
}

int main(int argc,char** argv) {
    if(argc!=2) throw logic_error("expected process index");
    int process=stoi(argv[1]);
    EncryptionParameters parms(scheme_type::bfv);
    parms.set_poly_modulus_degree(slots);
    parms.set_coeff_modulus(CoeffModulus::Create(slots,{60,60,60}));
    parms.set_plain_modulus(plain_mod);
    SEALContext context(parms,true,sec_level_type::tc128);
    if(!context.parameters_set()) throw logic_error(context.parameter_error_message());
    const vector<string> parents{"345141434","345444345","400044040","444444444"};
    KeyGenerator kg(context);
    Encryptor enc(context,kg.secret_key());
    Decryptor dec(context,kg.secret_key());
    Evaluator ev(context);
    BatchEncoder batch(context);
    vector<GaloisKeys> gks(4);
    vector<Plan> plans;
    cout<<"process,route,keys,depth,sources,steps,uncompressed_bytes,keygen_ms\n";
    for(int i=0;i<4;++i) {
        plans.push_back(schedule(parents[i]));
        auto start=Clock::now();
        kg.create_galois_keys(plans[i].keys,gks[i]);
        double ms=elapsed(start);
        ostringstream stream(ios::out|ios::binary);
        auto bytes=gks[i].save(stream,compr_mode_type::none);
        if(size_t(bytes)!=stream.str().size()) throw logic_error("serialization size");
        if(gks[i].size()!=plans[i].keys.size()) throw logic_error("key count");
        cout<<process<<","<<i<<","<<gks[i].size()<<","<<plans[i].depth<<","<<plans[i].groups.size()<<",";
        for (int step:plans[i].keys) cout<<step<<" ";
        cout<<","<<bytes<<","<<ms<<"\n";
    }
    vector<Plaintext> weights;
    for(int i=1;i<=9;++i) weights.emplace_back(to_string(i));
    vector<uint64_t> pixels(slots);
    uint32_t state=0x12cd34u;
    for(auto& v:pixels) {
        state=1664525u*state+1013904223u;
        v=state>>16;
    }
    Plaintext p;
    batch.encode(pixels,p);
    const array<array<int,4>,4> orders{{{0,1,3,2},{1,2,0,3},{2,3,1,0},{3,0,2,1}}};
    cout<<"process,block,position,route,time_ms,input_noise_bits,output_noise_bits\n";
    for(int block=-1;block<4;++block) {
        Ciphertext input;
        enc.encrypt_symmetric(p,input);
        int noise=dec.invariant_noise_budget(input);
        int position=0;
        for(int route:orders[(process+block+4)%4]) {
            auto start=Clock::now();
            auto out=evaluate(input,plans[route],gks[route],ev,weights);
            double ms=elapsed(start);
            verify(out,input,pixels,dec,batch);
            cout<<process<<","<<block<<","<<position++<<","<<route<<","<<ms<<","<<noise<<","
                <<dec.invariant_noise_budget(out.filtered)<<"\n";
        }
    }
}
