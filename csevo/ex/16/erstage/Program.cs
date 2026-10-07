// 슬라이드 p16-eras-stage — 선언의 오류가 본문 게이트를 가린다, C# 3.0
using System;

class Program
{
#if DECL
    int P { get; set; }                  // a declaration: auto-property
#endif

    static void Main()
    {
        var n = 1;                       // a body: var
        Func<int, int> f = x => x + n;   // a body: lambda
        Console.WriteLine(f(41));
    }
}
