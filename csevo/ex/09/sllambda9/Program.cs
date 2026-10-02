// 슬라이드 p9-v8-sl-later — static 람다, C# 9.0
using System;

class App
{
    static void Main()
    {
        int k = 10;
        Func<int, int> inc = static x => x + 1;     // C# 9
        Console.WriteLine(inc(k));
#if BAD
        Func<int, int> add = static x => x + k;     // captures k
#endif
    }
}
