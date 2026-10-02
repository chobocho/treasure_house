// 슬라이드 p10-v9-top-ns — 최상위 문과 네임스페이스, C# 9.0
using System;

var ns = typeof(Program).Namespace ?? "(global)";
Console.WriteLine("Program in " + ns);
Console.WriteLine(new Shop.Cart().Describe());

#if !FILESCOPED
namespace Shop
{
    class Cart
    {
        public string Describe() => GetType().FullName;
    }
}
#else
namespace Shop;     // C# 10 file-scoped namespace

class Cart
{
    public string Describe() => GetType().FullName;
}
#endif
