// 슬라이드 p6-v5-fe-linq — 늦은 실행과 만나는 루프 변수, C# 5.0
using System;
using System.Collections.Generic;
using System.Linq;

class App
{
    static void Main()
    {
        string text = "hello world";
        string drop = "lo";

        // Each pass adds a filter; the filters run only at the end.
        IEnumerable<char> q = text;
        foreach (char c in drop)
            q = q.Where(ch => ch != c);
        Console.WriteLine("foreach:      " + new string(q.ToArray()));

        // The same loop with one shared variable (the pre-C# 5 shape).
        IEnumerable<char> old = text;
        char shared;
        IEnumerator<char> e = drop.GetEnumerator();
        while (e.MoveNext())
        {
            shared = e.Current;
            old = old.Where(ch => ch != shared);
        }
        Console.WriteLine("one variable: " + new string(old.ToArray()));
    }
}
