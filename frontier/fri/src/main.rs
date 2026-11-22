#[allow(dead_code)]
mod params;
use fold_probe::{BasisMap, BasisParameters};
use p3_baby_bear::BabyBear;
use p3_field::{BasedVectorSpace, ExtensionField, PrimeCharacteristicRing, PrimeField32, TwoAdicField, extension::{BinomialExtensionField, BinomiallyExtendable}};
use p3_koala_bear::KoalaBear;
use p3_monty_31::MontyField31;
use p3_fri::{FriFoldingStrategy,TwoAdicFriFolding};
use p3_matrix::dense::RowMajorMatrixView;
use std::{hint::black_box, marker::PhantomData, time::Instant};
type Ext<F,const D:usize> = BinomialExtensionField<F,D>;

fn fold<F:TwoAdicField,E:ExtensionField<F>>(xs:&[E],beta:E,k:usize)->Vec<E> {
    FriFoldingStrategy::<F,E>::fold_matrix(&TwoAdicFriFolding::<(),()>(PhantomData), beta,k,RowMajorMatrixView::new(xs,1<<k))
}
fn chain<F:TwoAdicField,E:ExtensionField<F>>(xs:&[E],betas:&[E],ks:&[usize])->Vec<E> {
    let mut out=fold::<F,_>(xs,betas[0],ks[0]);
    for i in 1..ks.len(){out=fold::<F,_>(&out,betas[i],ks[i]);}
    out
}
struct Rng(u64);
impl Rng {
    fn next(&mut self)->u64{
        self.0=self.0.wrapping_add(0x9e3779b97f4a7c15);
        let mut z=self.0;
        z=(z^(z>>30)).wrapping_mul(0xbf58476d1ce4e5b9);
        z=(z^(z>>27)).wrapping_mul(0x94d049bb133111eb);
        z^(z>>31)
    }
    fn shuffle<T>(&mut self,v:&mut [T]){for i in (1..v.len()).rev(){v.swap(i,self.next() as usize%(i+1));}}
}
fn measure<T>(reps:usize, mut f:impl FnMut()->Vec<T>)->u128{
    let start=Instant::now();
    for _ in 0..reps {drop(black_box(f()));}
    start.elapsed().as_nanos()
}
fn run<S,F,const D:usize>(field:&str,seed:u64,ns:impl Fn(S)->F,ss:impl Fn(F)->S)
where S:TwoAdicField+PrimeField32+BinomiallyExtendable<D>, F:TwoAdicField+BasisParameters<D>
{
    let map=BasisMap::<F,D>::new();
    let native=|v:Ext<S,D>|{
        let a:&[S]=v.as_basis_coefficients_slice();
        map.to_native(&std::array::from_fn(|i|ns(a[i])))
    };
    let shared=|v:Ext<F,D>|Ext::<S,D>::new(map.to_shared(&v).map(&ss));
    let x=Ext::<F,D>::new(std::array::from_fn(|i|if i==1{F::ONE}else{F::ZERO}));
    let image=x.exp_u64(F::R as u64)*F::from_u32(F::T);
    let oracle=|v:Ext<S,D>|{
        let a:&[S]=v.as_basis_coefficients_slice();
        a.iter().rev().fold(Ext::<F,D>::ZERO,|acc,c| acc*image+F::from_u32(c.as_canonical_u32()))
    };
    let mut rng=Rng(seed);
    let mut order=Rng(seed ^ 0xc2b2ae35);
    for k in 0..=S::TWO_ADICITY{assert_eq!(S::two_adic_generator(k).as_canonical_u32(),F::two_adic_generator(k).as_canonical_u32());}
    for n in [4096,65536]{
        let mut draw=||Ext::<S,D>::new(std::array::from_fn(|_|S::from_u64(rng.next()%u64::from(S::ORDER_U32))));
        let xs:Vec<_>=(0..n).map(|_|draw()).collect();
        let betas:Vec<_>=(0..4).map(|_|draw()).collect();
        let xn:Vec<_>=xs.iter().copied().map(oracle).collect();
        let bn:Vec<_>=betas.iter().copied().map(oracle).collect();
        for (&s,&v) in xs.iter().zip(&xn).chain(betas.iter().zip(&bn)){assert_eq!(native(s),v);assert_eq!(shared(v),s);}
        for (schedule,ks) in [("2222",&[1,1,1,1][..]),("44",&[2,2][..]),("242",&[1,2,1][..])]{
            let once=|x:&[Ext<S,D>],b:&[Ext<S,D>],ks:&[usize]|{
                let input:Vec<_>=x.iter().copied().map(native).collect();
                let challenges:Vec<_>=b[..ks.len()].iter().copied().map(native).collect();
                chain::<F,_>(&input,&challenges,ks).into_iter().map(shared).collect::<Vec<_>>()
            };
            let every=|x:&[Ext<S,D>],b:&[Ext<S,D>],ks:&[usize]|{
                let mut out=once(x,&b[..1],&ks[..1]);
                for j in 1..ks.len(){out=once(&out,&b[j..j+1],&ks[j..j+1]);}
                out
            };
            for len in 1..=ks.len(){
                let ref_s=chain::<S,_>(&xs,&betas,&ks[..len]);
                let ref_n=chain::<F,_>(&xn,&bn,&ks[..len]);
                assert_eq!(ref_s.iter().copied().map(oracle).collect::<Vec<_>>(),ref_n);
                assert_eq!(once(&xs,&betas,&ks[..len]),ref_s);
                assert_eq!(every(&xs,&betas,&ks[..len]),ref_s);
            }
            let reps=65536/n;
            let mut orders=Vec::new();
            for _ in 0..2 {
                let mut permutation=[0,1,2,3];
                order.shuffle(&mut permutation);
                let mut block:Vec<_>=(0..4).map(|s|std::array::from_fn::<_,4,_>(|j|permutation[(s+j)%4])).collect();
                order.shuffle(&mut block);
                orders.extend(block);
            }
            orders.insert(0,[0,1,2,3]);
            for (round,methods) in orders.into_iter().enumerate(){
                for (pos,m) in methods.into_iter().enumerate(){
                    let (name,t)=match m {
                        0=>("shared",measure(reps,||chain::<S,_>(black_box(&xs),black_box(&betas),black_box(ks)))),
                        1=>("native",measure(reps,||chain::<F,_>(black_box(&xn),black_box(&bn),black_box(ks)))),
                        2=>("once",measure(reps,||once(black_box(&xs),black_box(&betas),black_box(ks)))),
                        _=>("every",measure(reps,||every(black_box(&xs),black_box(&betas),black_box(ks)))),
                    };
                    if round!=0 {println!("{seed},{field},{D},{n},{schedule},{round},{pos},{name},{reps},{t}");}
                }
            }
        }
    }
}
fn main(){
    let seed=std::env::args().nth(1).expect("supply seed").parse().unwrap();
    println!("seed,field,degree,items,schedule,round,position,method,repeats,total_ns");
    macro_rules! variant {($s:ty,$f:ty,$name:expr,$d:expr)=>{{
        type S=MontyField31<$s>;
        // SAFETY: each marker forwards the upstream PRIME, MONTY_BITS and MONTY_MU.
        // Both concrete MontyField31 types transparently store the same Montgomery residue.
        run::<S,$f,$d>($name,seed,|v| unsafe {std::mem::transmute::<S,$f>(v)},|v| unsafe {std::mem::transmute::<$f,S>(v)});
    }}}
    variant!(params::SharedBaby,BabyBear,"baby",4);
    variant!(params::SharedBaby,BabyBear,"baby",8);
    variant!(params::SharedKoala,KoalaBear,"koala",4);
    variant!(params::SharedKoala,KoalaBear,"koala",8);
}
