// 슬라이드 p11-v10-ns-il — 같은 형식, 두 가지 네임스페이스 꼴, C# 10.0
#if FS
namespace Shop;
#else
namespace Shop {
#endif

class Cart
{
    int count;
    public int Add(int n) => count += n;
}

#if !FS
}
#endif
