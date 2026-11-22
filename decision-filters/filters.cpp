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

using Kernel = array<int,9>;
constexpr int width=64;
void check(const Ciphertext &out, const Kernel &kernel, const std::vector<uint64_t> &input,
           Decryptor &dec, BatchEncoder &encoder) {
    Plaintext p;
    dec.decrypt(out,p);
    std::vector<uint64_t> got;
    encoder.decode(p,got);
    for (int image=0;image<2;++image) for (int y=0;y<width;++y) for (int x=0;x<width;++x) {
        int pos=y*width+x;
        int64_t cyclic=0, crop=0;
        bool interior=y>0 && y<width-1 && x>0 && x<width-1;
        for (int dy=-1;dy<=1;++dy) for (int dx=-1;dx<=1;++dx) {
            int w=kernel[3*(dy+1)+dx+1];
            cyclic+=w*static_cast<int64_t>(input[image*row+(pos+dy*width+dx+row)%row]);
            if (interior) crop+=w*static_cast<int64_t>(input[image*row+(y+dy)*width+x+dx]);
        }
        auto residue=[](int64_t n){return static_cast<uint64_t>((n%plain_mod+plain_mod)%plain_mod);};
        if (got[image*row+pos]!=residue(cyclic) ||
            (interior && got[image*row+pos]!=residue(crop))) throw std::logic_error("wrong output");
    }
}

using W = array<Plaintext,9>;
using Refs = array<const Ciphertext*,9>;
Ciphertext reduce(const Refs& terms,const W& w,int first,int last,Evaluator& ev) {
    Ciphertext sum,tmp;
    ev.multiply_plain(*terms[first],w[first],sum);
    for(int j=first+1;j<last;++j) {
        ev.multiply_plain(*terms[j],w[j],tmp);
        ev.add_inplace(sum,tmp);
    }
    return sum;
}
vector<Ciphertext> run(int arm,int f,const Ciphertext& input,const GaloisKeys& keys,
                       const Plan& plan,Evaluator& ev,const array<W,8>& weights) {
    array<Ciphertext,9> storage;
    Refs views{};
    views[4]=&input;
    auto edges=[&](const Ciphertext& src,const vector<int>& steps,const vector<int>& children) {
        if(steps.size()==1) ev.rotate_rows(src,steps.front(),keys,storage[children.front()]);
        else {
            vector<Ciphertext> outputs;
            ev.rotate_rows(src,steps,keys,outputs);
            for(size_t i=0;i<steps.size();++i) storage[children[i]]=std::move(outputs[i]);
        }
        for(int child:children) views[child]=&storage[child];
    };
    for(auto& g:plan.groups) edges(*views[g.parent],g.steps,g.children);
    if(arm<2) {
        int first=arm==0?3:0;
        array<const Ciphertext*,3> seeds{views[first],views[first+1],views[first+2]};
        for(int j=0;j<9;++j) views[j]=seeds[j%3];
    }
    vector<Ciphertext> out;
    out.reserve(f);
    for(int k=0;k<f;++k) {
        if(arm>=2) { out.push_back(reduce(views,weights[k],0,9,ev)); continue; }
        auto a=reduce(views,weights[k],0,3,ev);
        auto b=reduce(views,weights[k],3,6,ev);
        auto c=reduce(views,weights[k],6,9,ev);
        if(arm==0) {
            ev.rotate_rows_inplace(a,-64,keys);
            ev.rotate_rows_inplace(c,64,keys);
            ev.add_inplace(a,b);
        } else {
            ev.rotate_rows_inplace(c,64,keys);
            ev.add_inplace(c,b);
            ev.rotate_rows_inplace(c,64,keys);
        }
        ev.add_inplace(a,c);
        out.push_back(std::move(a));
    }
    return out;
}
int main(int argc,char** argv) {
    if(argc!=2) throw logic_error("process index required");
    int proc=stoi(argv[1]);
    EncryptionParameters parms(scheme_type::bfv);
    parms.set_poly_modulus_degree(slots);
    parms.set_coeff_modulus(CoeffModulus::Create(slots,{60,60,60}));
    parms.set_plain_modulus(plain_mod);
    SEALContext ctx(parms,true,sec_level_type::tc128);
    if(!ctx.parameters_set()) throw logic_error(ctx.parameter_error_message());
    KeyGenerator kg(ctx); Encryptor enc(ctx,kg.secret_key()); Decryptor dec(ctx,kg.secret_key());
    BatchEncoder batch(ctx); Evaluator ev(ctx);
    array<Plan,6> plans;
    plans[0].groups={{4,{3,5},{-1,1}}}; plans[0].keys={-64,-1,1,64};
    plans[1].groups={{4,{0},{-65}},{0,{1},{1}},{1,{2},{1}}}; plans[1].keys={-65,1,64};
    plans[2]=schedule("345141434"); plans[3]=schedule("345444345"); plans[4]=schedule("400044040"); plans[5]=schedule("444444444");
    array<GaloisKeys,6> keys;
    for(int i=0;i<6;++i) kg.create_galois_keys(plans[i].keys,keys[i]);
    array<Kernel,8> kernels;
    array<W,8> weights;
    for(int k=0;k<8;++k) for(int j=0;j<9;++j) {
        int value=(2+(j*7+k*11)%29)*((j+k)%3==0?-1:1);
        kernels[k][j]=value;
        weights[k][j].resize(1);
        weights[k][j][0]=(value+plain_mod)%plain_mod;
    }
    vector<uint64_t> pixels(slots);
    uint64_t state=20261122;
    for(auto& v:pixels) { state=state*6364136223846793005ULL+1; v=(state>>32)%plain_mod; }
    Plaintext p; batch.encode(pixels,p);
    cout<<"process,block,f,position,arm,ms,min_noise\n";
    const array<const char*,6> names{"G4","G3","C3","C4","C6","C8"};
    for(int b=-1;b<6;++b) for(int fi=0;fi<5;++fi) {
        const array<int,5> sizes{1,2,3,4,8};
        int f=sizes[(fi+b+proc+5)%5];
        Ciphertext input; enc.encrypt_symmetric(p,input);
        for(int pos=0;pos<6;++pos) {
            constexpr array<int,6> order{0,1,5,2,4,3};
            int arm=(proc+b+6+order[pos])%6;
            auto start=Clock::now();
            auto out=run(arm,f,input,keys[arm],plans[arm],ev,weights);
            auto ms=elapsed(start);
            int noise=999;
            for(int k=0;k<f;++k) {
                check(out[k],kernels[k],pixels,dec,batch);
                noise=min(noise,dec.invariant_noise_budget(out[k]));
            }
            cout<<proc<<","<<b<<","<<f<<","<<pos<<","<<names[arm]<<","<<ms<<","<<noise<<"\n";
        }
    }
}
