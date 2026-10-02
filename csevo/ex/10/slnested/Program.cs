// 슬라이드 p10-v9-sl-nested — static 람다 안의 람다, C# 9.0
using System;

class App
{
    static void Main()
    {
        int outer = 100;
        Func<int, Func<int, int>> make = static k =>
        {
            Func<int, int> add = x => x + k;   // captures k: ok
            return add;
        };
        Console.WriteLine(make(5)(1) + outer);
#if BAD
        Func<int, Func<int>> bad = static k => () => k + outer;
#endif
    }
}
