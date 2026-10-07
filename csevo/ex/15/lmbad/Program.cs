// 슬라이드 p15-v14-lm-bad — 여전히 안 되는 꼴, C# 14
using System;

delegate void D(ref int x, int y);
delegate int P(params int[] xs);

class Program
{
    static void Main()
    {
        D ok = (ref x, y) => x += y;
        int n = 1;
        ok(ref n, 2);
        Console.WriteLine(n);
#if PARAMS
        P p = (params xs) => xs.Length;
#endif
#if MIXED
        D m = (ref int x, y) => x += y;
#endif
#if NOPARENS
        Action<int> a = ref x => { };
#endif
#if DEFAULT
        D d = (ref x, y = 1) => x += y;
#endif
    }
}
