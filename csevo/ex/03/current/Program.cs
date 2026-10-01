// 슬라이드 p3-v2-iterator-current — Current 와 Reset, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Seq()
    {
        yield return 1;
        yield return 2;
    }

    static void Main()
    {
        IEnumerator<int> e = Seq().GetEnumerator();
        Console.WriteLine("before MoveNext: " + e.Current);
        while (e.MoveNext()) { }
        Console.WriteLine("after the end:   " + e.Current);
        try
        {
            e.Reset();
        }
        catch (NotSupportedException ex)
        {
            Console.WriteLine("Reset: " + ex.GetType().Name);
        }
    }
}
