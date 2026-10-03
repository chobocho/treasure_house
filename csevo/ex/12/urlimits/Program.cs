// 슬라이드 p12-v11-ur-limits — 식 트리와 dynamic 에는 없는 >>>, C# 11.0
using System;
using System.Linq.Expressions;

class App
{
    static void Main()
    {
        Func<int, int> f = v => v >>> 1;           // a delegate: fine
        Console.WriteLine(f(-8));
        Expression<Func<int, int>> ok = v => v >> 1;
        Console.WriteLine(ok);
#if TREE
        Expression<Func<int, int>> e = v => v >>> 1;
#endif
#if DYN
        dynamic d = -8;
        Console.WriteLine(d >>> 1);
#endif
    }
}
