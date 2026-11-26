audit() = {
  my(k=2^128-255, p=k*2^128+1, w=Mod(3,p)^k);
  my(h=x^9-18*x^6+54*x^3+27, f=x^3-x-1, larger=0);
  if (!isprime(p), error("public modulus is composite"));
  forstep(d=3,252,3, larger += isprime(2^256-d*2^128+1));
  print([p,lift(w),znorder(w,2^128),Vec(lift(polrootsmod(h,p))),Vec(lift(polrootsmod(f,p))),larger]);
};
iferr(audit(),err,print("PARI failed: ",err);quit(1));
quit(0);
