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
struct Edge { int parent, child, step; };
struct Plan { vector<Edge> edges; int depth=0; };

Plan schedule(const vector<int>& keys) {
    Plan plan;
    array<int,9> depths{};
    depths.fill(-1);
    depths[4]=0;
    queue<int> pending;
    pending.push(4);
    while (!pending.empty()) {
        int parent=pending.front();
        pending.pop();
        for (int step : keys) {
            auto found=find(offsets.begin(),offsets.end(),offsets[parent]+step);
            if (found==offsets.end()) continue;
            int child=int(found-offsets.begin());
            if (depths[child]>=0) continue;
            depths[child]=depths[parent]+1;
            plan.depth=max(plan.depth,depths[child]);
            plan.edges.push_back({parent,child,step});
            pending.push(child);
        }
    }
    if (plan.edges.size()!=8) throw logic_error("disconnected stencil");
    return plan;
}
struct Output { vector<Ciphertext> rotated; Ciphertext filtered; };
Output evaluate(const Ciphertext& input, const Plan& plan, const GaloisKeys& keys,
                bool many, Evaluator& ev, const vector<Plaintext>& weights,
                const vector<int>& direct) {
    Output out;
    out.rotated.resize(9);
    out.rotated[4]=input;
    if (many) {
#ifdef VECTOR_ROTATIONS
        vector<Ciphertext> result;
        ev.rotate_rows(input,direct,keys,result);
        for (int i=0,j=0;i<9;++i)
            if (i!=4) out.rotated[i]=std::move(result[j++]);
#else
        throw logic_error("vector API unavailable");
#endif
    } else {
        for (auto edge:plan.edges)
            ev.rotate_rows(out.rotated[edge.parent],edge.step,keys,out.rotated[edge.child]);
    }
    out.filtered=out.rotated[0];
    Ciphertext term;
    for (int i=1;i<9;++i) {
        ev.multiply_plain(out.rotated[i],weights[i],term);
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
void verify(const Output& out, const vector<uint64_t>& input, Decryptor& dec,BatchEncoder& batch) {
    for (int i=0;i<9;++i) {
        auto raw=decrypt_slots(out.rotated[i],dec,batch);
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
    bool smoke=argc==2 && string(argv[1])=="--smoke";
    EncryptionParameters parms(scheme_type::bfv);
    parms.set_poly_modulus_degree(slots);
    parms.set_coeff_modulus(CoeffModulus::Create(slots,{60,60,60}));
    parms.set_plain_modulus(plain_mod);
    SEALContext context(parms,true,sec_level_type::tc128);
    if(!context.parameters_set()) throw logic_error(context.parameter_error_message());
    vector<int> direct;
    for(int d:offsets) if(d!=0) direct.push_back(d);
    vector<vector<int>> keysets{{1,64,-65},{1,-1,64,-64},direct};
    KeyGenerator kg(context);
    Encryptor enc(context,kg.secret_key());
    Decryptor dec(context,kg.secret_key());
    Evaluator ev(context);
    BatchEncoder batch(context);
    vector<GaloisKeys> gks(3);
    vector<Plan> plans;
    cout<<"keyset,keys,depth,uncompressed_bytes,keygen_ms\n";
    for(int i=0;i<3;++i) {
        plans.push_back(schedule(keysets[i]));
        auto start=Clock::now();
        kg.create_galois_keys(keysets[i],gks[i]);
        double ms=elapsed(start);
        ostringstream stream(ios::out|ios::binary);
        auto bytes=gks[i].save(stream,compr_mode_type::none);
        if(size_t(bytes)!=stream.str().size()) throw logic_error("serialization size");
        cout<<i<<","<<gks[i].size()<<","<<plans[i].depth<<","<<bytes<<","<<ms<<"\n";
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
    cout<<"block,position,route,time_ms,input_noise_bits,output_noise_bits\n";
    for(int block=-1;block<(smoke?0:8);++block) {
        Ciphertext input;
        enc.encrypt_symmetric(p,input);
        int noise=dec.invariant_noise_budget(input);
        int position=0;
        for(int route:orders[(block+4)%4]) {
#ifndef VECTOR_ROTATIONS
            if(route==3) continue;
#endif
            int keyset=min(route,2);
            auto start=Clock::now();
            auto out=evaluate(input,plans[keyset],gks[keyset],route==3,ev,weights,direct);
            double ms=elapsed(start);
            verify(out,pixels,dec,batch);
            cout<<block<<","<<position++<<","<<route<<","<<ms<<","<<noise<<","
                <<dec.invariant_noise_budget(out.filtered)<<"\n";
        }
    }
}
