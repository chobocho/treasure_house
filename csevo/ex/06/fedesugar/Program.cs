// 슬라이드 p6-v5-fe-desugar — foreach 를 풀어 쓴 두 꼴, C# 5.0
using System;
using System.Collections.Generic;

class App
{
    static void Show(string tag, List<Func<int>> fs)
    {
        Console.Write(tag);
        foreach (Func<int> f in fs) Console.Write(" " + f());
        Console.WriteLine();
    }

    static void Main()
    {
        int[] items = { 1, 2, 3 };

        // Before C# 5: one variable, declared outside the loop.
        List<Func<int>> old = new List<Func<int>>();
        IEnumerator<int> e = ((IEnumerable<int>)items).GetEnumerator();
        int x;
        while (e.MoveNext())
        {
            x = e.Current;
            old.Add(() => x);
        }
        Show("outside:", old);

        // C# 5: a fresh variable inside the loop body.
        List<Func<int>> now = new List<Func<int>>();
        e = ((IEnumerable<int>)items).GetEnumerator();
        while (e.MoveNext())
        {
            int y = e.Current;
            now.Add(() => y);
        }
        Show("inside: ", now);
    }
}
