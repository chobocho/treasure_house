// 슬라이드 p3-v2-iterator-finally — break 해도 finally 는 돈다, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<int> Read()
    {
        Console.WriteLine("open");
        try
        {
            for (int i = 1; i <= 5; i++)
            {
                yield return i;
            }
        }
        finally
        {
            Console.WriteLine("close");
        }
    }

    static void Main()
    {
        foreach (int x in Read())
        {
            Console.WriteLine(x);
            if (x == 2) break;            // foreach calls Dispose
        }
        Console.WriteLine("-- by hand, with Dispose");
        IEnumerator<int> e = Read().GetEnumerator();
        e.MoveNext();
        e.Dispose();                      // runs the finally block
        Console.WriteLine("-- by hand, no Dispose");
        IEnumerator<int> f = Read().GetEnumerator();
        f.MoveNext();
        Console.WriteLine("end of Main");
    }
}
