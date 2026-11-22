use p3_baby_bear::BabyBear;
use p3_field::BasedVectorSpace;
use p3_koala_bear::KoalaBear;
use plonky3_native::{BasisMap, BasisParameters};
use std::{hint::black_box, io::{self, BufRead}, time::Instant};

const INPUTS: usize = 32_768;

fn word(state: &mut u64) -> u64 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    *state
}

fn native<F: BasisParameters<D>, const D: usize>(
    map: &BasisMap<F, D>, coordinates: &[F; D],
) -> [F; D] {
    map.to_native(coordinates).as_basis_coefficients_slice().try_into().unwrap()
}

fn mix<F: BasisParameters<D>, const D: usize>(lo: &[F; D], hi: &[F; D], r: F) -> [F; D] {
    std::array::from_fn(|i| lo[i] + r * (hi[i] - lo[i]))
}

/// Specializing both versions leaves route dispatch outside every inner loop.
#[inline(never)]
fn evaluate<F: BasisParameters<D>, const D: usize, const EARLY: bool>(
    map: &BasisMap<F, D>, input: &[[F; D]], point: &[F],
    scratch: &mut [[F; D]], output: &mut [[F; D]],
) {
    let first_fold = |pair: &[[F; D]]| {
        if EARLY {
            mix(&native(map, &pair[0]), &native(map, &pair[1]), point[0])
        } else {
            mix(&pair[0], &pair[1], point[0])
        }
    };
    let finish = |x: [F; D]| if EARLY { x } else { native(map, &x) };
    if point.len() == 1 {
        for (dst, pair) in output.iter_mut().zip(input.chunks_exact(2)) {
            *dst = finish(first_fold(pair));
        }
        return;
    }
    for (dst, pair) in scratch.iter_mut().zip(input.chunks_exact(2)) {
        *dst = first_fold(pair);
    }
    let mut active = input.len() / 2;
    for &r in &point[1..point.len() - 1] {
        active /= 2;
        for i in 0..active {
            scratch[i] = mix(&scratch[2 * i], &scratch[2 * i + 1], r);
        }
    }
    for (dst, pair) in output.iter_mut().zip(scratch[..active].chunks_exact(2)) {
        *dst = finish(mix(&pair[0], &pair[1], *point.last().unwrap()));
    }
}

fn experiment<F: BasisParameters<D>, const D: usize>(
    block: usize, name: &str, factor: usize, mut seed: u64, orders: &str,
) {
    assert!(seed != 0 && [2, 8, 128].contains(&factor));
    let map = BasisMap::<F, D>::new();
    let input: Vec<[F; D]> = (0..INPUTS)
        .map(|_| std::array::from_fn(|_| F::from_u64(word(&mut seed)))).collect();
    let point: Vec<F> = (0..factor.ilog2()).map(|_| F::from_u64(word(&mut seed))).collect();
    let weights: Vec<F> = (0..factor).map(|j| point.iter().enumerate()
        .map(|(k, &r)| if (j >> k) & 1 == 1 { r } else { F::ONE - r }).product()).collect();
    let expected: Vec<[F; D]> = input.chunks_exact(factor).map(|cube| {
        let mut total = [F::ZERO; D];
        for (row, &weight) in cube.iter().zip(&weights) {
            let converted = native(&map, row);
            for i in 0..D { total[i] += weight * converted[i]; }
        }
        total
    }).collect();
    let mut scratch = vec![[F::ZERO; D]; INPUTS / 2];
    let mut output = vec![[F::ZERO; D]; expected.len()];
    let mut timed = |early: bool| {
        let start = Instant::now();
        if early {
            evaluate::<F, D, true>(&map, &input, &point, &mut scratch, &mut output);
        } else {
            evaluate::<F, D, false>(&map, &input, &point, &mut scratch, &mut output);
        }
        black_box(&output);
        let ns = start.elapsed().as_nanos();
        assert_eq!(output, expected);
        ns
    };
    timed(true);
    timed(false);
    for (pair, first) in orders.chars().enumerate() {
        let (early_ns, late_ns) = match first {
            'E' => (timed(true), timed(false)),
            'L' => { let late = timed(false); (timed(true), late) }
            _ => panic!("unexpected route order"),
        };
        println!("{block},{name},{D},{factor},{pair},{first},{early_ns},{late_ns}");
    }
}

fn main() {
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let cols: Vec<_> = line.split_whitespace().collect();
        let block = cols[0].parse().unwrap();
        let field = cols[1];
        let factor = cols[3].parse().unwrap();
        let seed = cols[4].parse().unwrap();
        let orders = cols[5];
        match (field, cols[2]) {
            ("BabyBear", "4") => experiment::<BabyBear, 4>(block, field, factor, seed, orders),
            ("BabyBear", "8") => experiment::<BabyBear, 8>(block, field, factor, seed, orders),
            ("KoalaBear", "4") => experiment::<KoalaBear, 4>(block, field, factor, seed, orders),
            ("KoalaBear", "8") => experiment::<KoalaBear, 8>(block, field, factor, seed, orders),
            _ => panic!("unexpected field or degree"),
        }
    }
}
