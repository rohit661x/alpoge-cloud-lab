#include <seal/seal.h>
#include <array>
#include <iostream>
#include <stdexcept>
#include <vector>

using namespace seal;
using Kernel = std::array<int,9>;
constexpr int width=64, row=width*width, slots=2*row, modulus=65537;
const std::array<Kernel,3> kernels{{
    {2,-3,5,7,11,-13,17,19,23}, {-1,2,3,5,-7,11,13,-17,19},
    {3,1,-2,4,7,5,-1,8,6}
}};

struct Rotator {
    Evaluator &eval;
    const GaloisKeys &keys;
    int calls=0;
    Ciphertext operator()(const Ciphertext &input,int offset) {
        Ciphertext out;
        eval.rotate_rows(input,offset,keys,out);
        ++calls;
        return out;
    }
};

Ciphertext weighted(const std::array<Ciphertext,3> &terms, const Kernel &kernel,
                    int r, Evaluator &eval, BatchEncoder &encoder) {
    Ciphertext sum;
    for (int j=0;j<3;++j) {
        Plaintext scalar;
        std::vector<uint64_t> weights(slots,(kernel[3*r+j]+modulus)%modulus);
        encoder.encode(weights,scalar);
        Ciphertext term;
        eval.multiply_plain(terms[j],scalar,term);
        if (j==0) sum=std::move(term);
        else eval.add_inplace(sum,term);
    }
    return sum;
}

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
        auto residue=[](int64_t n){return static_cast<uint64_t>((n%modulus+modulus)%modulus);};
        if (got[image*row+pos]!=residue(cyclic) ||
            (interior && got[image*row+pos]!=residue(crop))) throw std::logic_error("wrong output");
    }
}

int main() {
    EncryptionParameters parms(scheme_type::bfv);
    parms.set_poly_modulus_degree(slots);
    parms.set_coeff_modulus(CoeffModulus::Create(slots,{60,60,60}));
    parms.set_plain_modulus(modulus);
    SEALContext context(parms,true,sec_level_type::tc128);
    if (!context.parameters_set()) throw std::logic_error(context.parameter_error_message());
    KeyGenerator kg(context);
    Evaluator ev(context);
    Encryptor enc(context,kg.secret_key());
    Decryptor dec(context,kg.secret_key());
    BatchEncoder batch(context);
    std::vector<uint64_t> inputs(slots);
    uint64_t state=20261122;
    for (auto &value:inputs) {
        state=state*6364136223846793005ULL+1;
        value=(state>>32)%modulus;
    }
    Plaintext p;
    batch.encode(inputs,p);
    Ciphertext in;
    enc.encrypt_symmetric(p,in);
    for (int mode=0;mode<3;++mode) {
        const std::vector<int> offsets=mode==0?std::vector<int>{-1,1,-width,width}
                                               :std::vector<int>{-width-1,1,width};
        GaloisKeys keys;
        kg.create_galois_keys(offsets,keys);
        Rotator rot{ev,keys};
        std::array<Ciphertext,3> horizontal;
        std::array<std::array<Ciphertext,3>,3> views;
        if (mode==0) horizontal={rot(in,-1),in,rot(in,1)};
        else if (mode==1) {
            horizontal[0]=rot(in,-width-1);
            horizontal[1]=rot(horizontal[0],1);
            horizontal[2]=rot(horizontal[1],1);
        } else {
            views[0][0]=rot(in,-width-1);
            views[0][1]=rot(views[0][0],1);
            views[0][2]=rot(views[0][1],1);
            views[1][0]=rot(views[0][0],width);
            views[1][1]=in;
            views[1][2]=rot(in,1);
            for (int j=0;j<3;++j) views[2][j]=rot(views[1][j],width);
        }
        int f=0;
        for (auto &kernel:kernels) {
            std::array<Ciphertext,3> sums;
            for (int r=0;r<3;++r) sums[r]=weighted(mode==2?views[r]:horizontal,kernel,r,ev,batch);
            if (mode==0) {
                sums[0]=rot(sums[0],-width);
                sums[2]=rot(sums[2],width);
            } else if (mode==1) {
                sums[2]=rot(sums[2],width);
                ev.add_inplace(sums[2],sums[1]);
                sums[2]=rot(sums[2],width);
            }
            if (mode!=1) ev.add_inplace(sums[0],sums[1]);
            ev.add_inplace(sums[0],sums[2]);
            check(sums[0],kernel,inputs,dec,batch);
            ++f;
            const int expected=mode==2?8:2+mode+2*f;
            if (rot.calls!=expected) throw std::logic_error("wrong call count");
            std::cout<<"mode="<<mode<<" filters="<<f<<" rotations="<<rot.calls
                     <<" cyclic_slots=8192 valid_slots=7688 PASS\n";
        }
    }
}
