// 슬라이드 p14-v13-pm-req — required 멤버가 있는 컬렉션, C# 13
using System;
using System.Collections;
using System.Collections.Generic;

class Tagged : IEnumerable<int>
{
    readonly List<int> items = new();
    public required string Tag;     // the constructor does not set it
    public void Add(int x) => items.Add(x);
    public IEnumerator<int> GetEnumerator() => items.GetEnumerator();
    IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}

class Program
{
#if BAD
    static int Count(params Tagged t) => 0;
#endif
    static void Main()
    {
        var t = new Tagged { Tag = "a" };
        t.Add(1);
        foreach (int x in t) Console.WriteLine(t.Tag + x);
    }
}
