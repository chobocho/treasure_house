// 슬라이드 p11-v10-ns-global — global using 의 자리, C# 10.0
#if !BAD
global using System;                        // compilation unit level
#endif
namespace Shop;
#if BAD
global using System;                        // inside namespace Shop
#endif

class App
{
    static void Main() => Console.WriteLine(typeof(App).FullName);
}
