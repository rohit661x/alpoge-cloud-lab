//! Scalar multilinear folding with a common base-field evaluation point.
use p3_baby_bear::BabyBear;
use p3_koala_bear::KoalaBear;
use p3_field::{BasedVectorSpace};
use p3_field::extension::BinomialExtensionField;
use plonky3_native::{BasisMap, BasisParameters};
use std::{hint::black_box, time::Instant};

fn next_word(state: &mut u64) -> u64 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    *state
}

fn mix<F: BasisParameters<D>,const D:usize>(l:&[F;D],h:&[F;D],r:F)->[F;D]{
    core::array::from_fn(|i|l[i]+r*(h[i]-l[i]))
}

fn fold<F:BasisParameters<D>,const D:usize>(mut v:Vec<[F;D]>,point:&[F])->Vec<[F;D]> {
    for &r in point {
        for i in 0..v.len()/2 {
            v[i]=mix(&v[2*i],&v[2*i+1],r);
        }
        v.truncate(v.len()/2);
    }
    v
}

fn native<F:BasisParameters<D>,const D:usize>(map:&BasisMap<F,D>,x:&[F;D])->[F;D] {
    map.to_native(x).as_basis_coefficients_slice().try_into().unwrap()
}

fn run<F:BasisParameters<D>,const D:usize>(name:&str,seed:u64,n:usize,m:usize) {
    let mut state=seed;
    let map=BasisMap::<F,D>::new();
    let shared: Vec<[F;D]>=(0..n).map(|_|core::array::from_fn(|_|F::from_u64(next_word(&mut state)))).collect();
    let resident:Vec<_>=shared.iter().map(|x|native(&map,x)).collect();
    let rounds=(n/m).ilog2() as usize;
    let point:Vec<_>=(0..rounds).map(|_|F::from_u64(next_word(&mut state))).collect();
    assert!(point.iter().all(|r| *r!=F::ZERO && *r!=F::ONE));
    // Independent Lagrange sum on each Boolean cube, using extension values.
    let weights:Vec<_>=(0..n/m).map(|j|point.iter().enumerate().map(|(k,&r)|if (j>>k)&1==1 {r} else {F::ONE-r}).product::<F>()).collect();
    let oracle:Vec<[F;D]>=resident.chunks_exact(n/m).map(|chunk|{
        let y:BinomialExtensionField<F,D>=chunk.iter().zip(&weights).map(|(x,&w)|BinomialExtensionField::new(*x)*w).sum();
        y.as_basis_coefficients_slice().try_into().unwrap()
    }).collect();
    let route=|id|{
        match id {
            0=>fold(resident.clone(),&point),
            1=>fold(shared.iter().map(|x|native(&map,x)).collect(),&point),
            2=>{let out=fold(shared.clone(),&point);out.iter().map(|x|native(&map,x)).collect()},
            3=>{let first=shared.chunks_exact(2).map(|p|mix(&native(&map,&p[0]),&native(&map,&p[1]),point[0])).collect();fold(first,&point[1..])},
            4=>{let first=shared.chunks_exact(2).map(|p|mix(&p[0],&p[1],point[0])).collect();let out=fold(first,&point[1..]);out.iter().map(|x|native(&map,x)).collect()},
            5=>{let first=resident.chunks_exact(2).map(|p|mix(&p[0],&p[1],point[0])).collect();fold(first,&point[1..])},
            _=>unreachable!()
        }
    };
    for id in 0..6 {assert_eq!(route(id),oracle);}
    for sample in 0..6 {
        for j in 0..6 {
            let id=(j+sample+(seed%6) as usize)%6;
            let start=Instant::now();
            let out=black_box(route(black_box(id)));
            let ns=start.elapsed().as_nanos();
            assert_eq!(out,oracle);
            println!("{seed},{name},{D},{n},{m},{sample},{id},{ns}");
        }
    }
}

fn main() {
    let seed:u64=std::env::args().nth(1).unwrap().parse().unwrap();
    assert!(seed>0);
    println!("seed,field,degree,inputs,outputs,sample,mode,ns");
    for n in [4096,65536] {for m in [1,n/16] {
        run::<BabyBear,4>("BabyBear",seed,n,m);
        run::<BabyBear,8>("BabyBear",seed,n,m);
        run::<KoalaBear,4>("KoalaBear",seed,n,m);
        run::<KoalaBear,8>("KoalaBear",seed,n,m);
    }}
}
