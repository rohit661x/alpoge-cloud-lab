//! Isomorphisms from F[u]/(u^D-37) to Plonky3's native binomial fields.
//! Arrays use increasing powers of the chosen generator, constant term first.
use p3_baby_bear::BabyBear;
use p3_field::{BasedVectorSpace, PrimeField32};
use p3_field::extension::{BinomialExtensionField, BinomiallyExtendable};
use p3_koala_bear::KoalaBear;

/// The map sends u to T times x^R, where x is the native generator.
pub trait BasisParameters<const D: usize>: PrimeField32 + BinomiallyExtendable<D> {
    const R: usize;
    const T: u32;
}

macro_rules! parameters {
    ($field:ty, $degree:literal, $r:literal, $t:literal) => {
        impl BasisParameters<$degree> for $field {
            const R: usize = $r;
            const T: u32 = $t;
        }
    };
}
parameters!(BabyBear, 4, 3, 58_781_239);
parameters!(BabyBear, 8, 3, 305_087_007);
parameters!(KoalaBear, 4, 1, 168_445_237);
parameters!(KoalaBear, 8, 5, 94_536_886);

/// A permutation and two sets of precomputed base-field scale factors.
pub struct BasisMap<F, const D: usize> {
    native_index: [usize; D],
    forward: [F; D],
    reverse: [F; D],
}

impl<F: BasisParameters<D>, const D: usize> BasisMap<F, D> {
    pub fn new() -> Self {
        let t = F::from_u32(F::T);
        let w = <F as BinomiallyExtendable<D>>::W;
        assert_eq!(t.exp_u64(D as u64) * w.exp_u64(F::R as u64), F::from_u32(37));
        let native_index = core::array::from_fn(|i| (F::R * i) % D);
        let forward = core::array::from_fn(|i| {
            t.exp_u64(i as u64) * w.exp_u64(((F::R * i) / D) as u64)
        });
        let reverse = forward.map(|s| s.inverse());
        Self { native_index, forward, reverse }
    }

    pub fn to_native(&self, shared: &[F; D]) -> BinomialExtensionField<F, D> {
        let mut native = [F::ZERO; D];
        for (i, &a) in shared.iter().enumerate() {
            native[self.native_index[i]] = a * self.forward[i];
        }
        BinomialExtensionField::new(native)
    }

    pub fn to_shared(&self, native: &BinomialExtensionField<F, D>) -> [F; D] {
        let a: &[F] = native.as_basis_coefficients_slice();
        core::array::from_fn(|i| a[self.native_index[i]] * self.reverse[i])
    }
}

impl<F: BasisParameters<D>, const D: usize> Default for BasisMap<F, D> {
    fn default() -> Self { Self::new() }
}
