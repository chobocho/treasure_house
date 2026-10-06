// 슬라이드 p13-v12-al-generic — 열린 제네릭 별칭은 없다, C# 12.0
using System;
using IntList = System.Collections.Generic.List<int>;   // closed
using Pairs = System.Collections.Generic.List<(string, int)>;
#if OPEN
using Lst<T> = System.Collections.Generic.List<T>;
#endif
#if UNBOUND
using Lst = System.Collections.Generic.List<>;
#endif

class App
{
    static void Main()
    {
        IntList xs = [1, 2, 3];
        Pairs ps = [("a", 1)];
        Console.WriteLine($"{xs.Count} {ps[0].Item1}");
    }
}
