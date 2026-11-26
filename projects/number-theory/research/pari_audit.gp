\\ Independent PARI/GP computations for the exact certificates and prime census.
\\ Output is newline-delimited JSON (header, one record per prime, trailer).
degrees(poly, p) = Vec(factormod(poly, p, 1)[,1]);

audit(bound) = {
  my(f=x^3-x-1, h=x^9-18*x^6+54*x^3+27, q=x^3-6*x-3);
  my(pg=2^64-2^32+1, pc=2^255-19, n=pg^2+pg+1);
  my(a=ffgen(Mod(1,pg)*f,'a), z=vecsort(Vec(lift(polrootsmod(f,pc)))));
  my(id=polgalois(h), idrad=polgalois(subst(f,x,x^3)));
  if (!isprime(pg) || !isprime(pc), error("field primality"));
  if (#z != 3 || fforder(a,n) != n, error("Goldilocks order or split root count"));
  print("[\"metadata\",", [id[1],id[3],idrad[1],poldisc(f),poldisc(q),n,z,vector(#z,i,znorder(Mod(z[i],pc)))], "]");
  forprime(p=2,bound,
    if(p!=3 && p!=23, print([p,degrees(f,p),degrees(q,p),degrees(h,p)]))
  );
  print("[\"complete\",",bound,"]");
};
iferr(audit(1000000), err, print("PARI error: ",err);quit(1));
quit(0);
