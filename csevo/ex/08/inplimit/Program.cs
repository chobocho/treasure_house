// 슬라이드 p8-v7_2-in-limit — in 을 쓸 수 없는 곳, C# 7.2
using System;
using System.Collections.Generic;

class App
{
    static Func<int> Capture(in int x)
    {
        return () => x;                 // a lambda would outlive x
    }

    static IEnumerable<int> Iter(in int x)
    {
        yield return x;                 // an iterator
    }

    static void Main() { }
}
