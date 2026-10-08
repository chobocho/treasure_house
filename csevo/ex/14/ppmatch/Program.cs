// 슬라이드 p14-v13-pp-match — 두 조각의 시그니처가 어긋나면, C# 13.0
using System;

partial class C
{
    public partial string P { get; private set; }
#if ACC
    public partial string P { get => "p"; set { } }
#else
    public partial string P { get => "p"; private set { } }
#endif
    public partial string Q { get; init; }
#if INIT
    public partial string Q { get => "q"; set { } }
#else
    public partial string Q { get => "q"; init { } }
#endif
    public partial int this[int x] { get; }
#if NAME
    public partial int this[int y] => y * 2;
#else
    public partial int this[int x] => x * 2;
#endif
}

class App
{
    static void Main()
    {
        var c = new C();
        Console.WriteLine(c.P + c.Q + c[x: 21]);
        var ix = typeof(C).GetProperty("Item");
        Console.WriteLine(ix.GetIndexParameters()[0].Name);
    }
}
