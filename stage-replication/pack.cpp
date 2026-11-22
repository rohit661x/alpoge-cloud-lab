#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#include <vector>
#include <fstream>
int main(int argc,char** argv) {
  int w,h,c;
  auto raw = stbi_load(argv[1],&w,&h,&c,0);
  if (!raw||w!=32||h!=32||c!=3) return 1;
  std::vector<double> values(16384);
  for(int i=0;i<1024;++i) for(int ch=0;ch<3;++ch) values[ch*1024+i]=double(raw[i*3+ch])/255.f;
  std::ofstream out(argv[2],std::ios::binary);
  out.write(reinterpret_cast<const char*>(values.data()),values.size()*sizeof(double));
  stbi_image_free(raw);
}
