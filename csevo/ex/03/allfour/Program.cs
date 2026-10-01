// 슬라이드 p3-v2-gates — C# 2.0 기능 넷을 한 파일에, C# 2.0
using System;
using System.Collections;
using System.Collections.Generic;

class App
{
    static IEnumerable Evens(int n)       // iterator
    {
        for (int i = 0; i < n; i += 2) yield return i;
    }

    static void Main()
    {
        List<int> xs = new List<int>();   // generics
        foreach (int x in Evens(5)) xs.Add(x);
        int? last = null;                 // nullable value type
        if (xs.Count > 0) last = xs[xs.Count - 1];
        int zero = default(int);          // default operator
        Console.WriteLine(xs.Count + " " + last + " " + zero);
    }
}
