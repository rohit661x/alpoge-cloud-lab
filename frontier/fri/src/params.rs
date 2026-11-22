//! Same Montgomery base fields as the upstream native field markers, with X^D = 37.
//! Extension generators and two-adic roots are the inverse images of the pinned
//! upstream constants. The fold harness verifies the base-field two-adic generators.
use p3_baby_bear::BabyBearParameters;
use p3_koala_bear::KoalaBearParameters;
use p3_monty_31::{BinomialExtensionData,FieldParameters,MontyField31,MontyParameters,PackedMontyParameters};

macro_rules! base {
    ($name:ident, $native:ty, $g:literal) => {
        #[derive(Clone, Copy, Default, Debug, PartialEq, Eq, Hash)]
        pub struct $name;
        impl MontyParameters for $name {
            const PRIME:u32=<$native>::PRIME;
            const MONTY_BITS:u32=<$native>::MONTY_BITS;
            const MONTY_MU:u32=<$native>::MONTY_MU;
        }
        #[cfg(all(target_arch="aarch64",target_feature="neon"))]
        impl p3_monty_31::MontyParametersNeon for $name {
            const PACKED_P:core::arch::aarch64::uint32x4_t=<$native as p3_monty_31::MontyParametersNeon>::PACKED_P;
            const PACKED_MU:core::arch::aarch64::int32x4_t=<$native as p3_monty_31::MontyParametersNeon>::PACKED_MU;
        }
        #[cfg(all(target_arch="x86_64",target_feature="avx2",not(target_feature="avx512f")))]
        impl p3_monty_31::MontyParametersAVX2 for $name {
            const PACKED_P:core::arch::x86_64::__m256i=<$native as p3_monty_31::MontyParametersAVX2>::PACKED_P;
            const PACKED_MU:core::arch::x86_64::__m256i=<$native as p3_monty_31::MontyParametersAVX2>::PACKED_MU;
        }
        #[cfg(all(target_arch="x86_64",target_feature="avx512f"))]
        impl p3_monty_31::MontyParametersAVX512 for $name {
            const PACKED_P:core::arch::x86_64::__m512i=<$native as p3_monty_31::MontyParametersAVX512>::PACKED_P;
            const PACKED_MU:core::arch::x86_64::__m512i=<$native as p3_monty_31::MontyParametersAVX512>::PACKED_MU;
        }
        impl PackedMontyParameters for $name {}
        impl FieldParameters for $name {
            const MONTY_GEN:MontyField31<Self>=MontyField31::new($g);
            const BENEFITS_FROM_LOCKSTEP_EVALUATION:bool=<$native>::BENEFITS_FROM_LOCKSTEP_EVALUATION;
        }
    }
}
base!(SharedBaby,BabyBearParameters,31);
base!(SharedKoala,KoalaBearParameters,3);
macro_rules! extension {
    ($marker:ty,$d:literal,$root:literal,$gen:expr,$adic:literal,$levels:literal,$roots:expr) => {
        impl BinomialExtensionData<$d> for $marker {
            const W:MontyField31<Self>=MontyField31::new(37);
            const DTH_ROOT:MontyField31<Self>=MontyField31::new($root);
            const EXT_GENERATOR:[MontyField31<Self>;$d]=MontyField31::new_array($gen);
            const EXT_TWO_ADICITY:usize=$adic;
            type ArrayLike=[[MontyField31<Self>;$d];$levels];
            const TWO_ADIC_EXTENSION_GENERATORS:Self::ArrayLike=MontyField31::new_2d_array($roots);
        }
    }
}
extension!(SharedBaby,4,284861408,[8, 0, 0, 670426613],29,2,[[0, 0, 1289925636, 0], [0, 1654133363, 0, 0]]);
extension!(SharedBaby,8,1801542727,[5, 0, 0, 1725761133, 0, 0, 0, 0],30,3,[[0, 0, 0, 0, 723340285, 0, 0, 0], [0, 0, 1624631372, 0, 0, 0, 0, 0], [0, 1970648633, 0, 0, 0, 0, 0, 0]]);
extension!(SharedKoala,4,2113994754,[2, 153715975, 0, 0],26,2,[[0, 0, 1513126184, 0], [0, 0, 0, 511552528]]);
extension!(SharedKoala,8,382534071,[10, 0, 0, 0, 0, 805567327, 0, 0],27,3,[[0, 0, 0, 0, 617580249, 0, 0, 0], [0, 0, 0, 0, 0, 0, 322247458, 0], [0, 0, 0, 419648803, 0, 0, 0, 0]]);
impl p3_monty_31::TwoAdicData for SharedKoala {
    const TWO_ADICITY: usize = 24;

    type ArrayLike = &'static [MontyField31<SharedKoala>];

    const TWO_ADIC_GENERATORS: Self::ArrayLike = &MontyField31::<SharedKoala>::new_array([
        0x1, 0x7f000000, 0x7e010002, 0x6832fe4a, 0x8dbd69c, 0xa28f031, 0x5c4a5b99, 0x29b75a80,
        0x17668b8a, 0x27ad539b, 0x334d48c7, 0x7744959c, 0x768fc6fa, 0x303964b2, 0x3e687d4d,
        0x45a60e61, 0x6e2f4d7a, 0x163bd499, 0x6c4a8a45, 0x143ef899, 0x514ddcad, 0x484ef19b,
        0x205d63c3, 0x68e7dd49, 0x6ac49f88,
    ]);

    const ROOTS_8: Self::ArrayLike =
        &MontyField31::<SharedKoala>::new_array([0x1, 0x6832fe4a, 0x7e010002, 0x174e3650]);
    const INV_ROOTS_8: Self::ArrayLike =
        &MontyField31::<SharedKoala>::new_array([0x1, 0x67b1c9b1, 0xfeffff, 0x16cd01b7]);

    const ROOTS_16: Self::ArrayLike = &MontyField31::<SharedKoala>::new_array([
        0x1, 0x8dbd69c, 0x6832fe4a, 0x27ae21e2, 0x7e010002, 0x3a89a025, 0x174e3650, 0x27dfce22,
    ]);
    const INV_ROOTS_16: Self::ArrayLike = &MontyField31::<SharedKoala>::new_array([
        0x1, 0x572031df, 0x67b1c9b1, 0x44765fdc, 0xfeffff, 0x5751de1f, 0x16cd01b7, 0x76242965,
    ]);
}
impl p3_monty_31::TwoAdicData for SharedBaby {
    const TWO_ADICITY: usize = 27;

    type ArrayLike = &'static [MontyField31<SharedBaby>];

    const TWO_ADIC_GENERATORS: Self::ArrayLike = &MontyField31::<SharedBaby>::new_array([
        0x1, 0x78000000, 0x67055c21, 0x5ee99486, 0xbb4c4e4, 0x2d4cc4da, 0x669d6090, 0x17b56c64,
        0x67456167, 0x688442f9, 0x145e952d, 0x4fe61226, 0x4c734715, 0x11c33e2a, 0x62c3d2b1,
        0x77cad399, 0x54c131f4, 0x4cabd6a6, 0x5cf5713f, 0x3e9430e8, 0xba067a3, 0x18adc27d,
        0x21fd55bc, 0x4b859b3d, 0x3bd57996, 0x4483d85a, 0x3a26eef8, 0x1a427a41,
    ]);

    const ROOTS_8: Self::ArrayLike = &MontyField31::<SharedBaby>::new_array([0x1, 0x5ee99486, 0x67055c21, 0xc9ea3ba]);
    const INV_ROOTS_8: Self::ArrayLike =
        &MontyField31::<SharedBaby>::new_array([0x1, 0x6b615c47, 0x10faa3e0, 0x19166b7b]);

    const ROOTS_16: Self::ArrayLike = &MontyField31::<SharedBaby>::new_array([
        0x1, 0xbb4c4e4, 0x5ee99486, 0x4b49e08, 0x67055c21, 0x5376917a, 0xc9ea3ba, 0x563112a7,
    ]);
    const INV_ROOTS_16: Self::ArrayLike = &MontyField31::<SharedBaby>::new_array([
        0x1, 0x21ceed5a, 0x6b615c47, 0x24896e87, 0x10faa3e0, 0x734b61f9, 0x19166b7b, 0x6c4b3b1d,
    ]);
}
