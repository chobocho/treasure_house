// 슬라이드 p9-v8-ro-auto — 속성과 접근자의 readonly, C# 8.0
using System;

struct S
{
    int m;
    public int Auto { get; set; }                  // getter is readonly
    public int Manual { get => m; set => m = value; }
    public int Mixed { readonly get => m; set => m = value; }

    public readonly int Sum() => Auto + Mixed;     // no copy, no warn
#if WARN
    public readonly int Bad() => Manual;           // copy: warning
#endif
#if BAD
    public int P6 { readonly get; }
    public readonly int P7 { get; set; }
    public int P8 { get; readonly set; }
#endif
}

class App
{
    static void Main()
    {
        var s = new S { Auto = 1, Mixed = 2, Manual = 3 };
        Console.WriteLine(s.Sum() + " " + s.Manual);
    }
}
