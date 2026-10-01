// 슬라이드 p2-v1_2-iterator — 반복기의 finally 와 foreach, C# 2
using System;
using System.Collections;

class App
{
    static IEnumerable Lines()              // a C# 2 iterator
    {
        try
        {
            yield return "line1";
            yield return "line2";
        }
        finally
        {
            Console.WriteLine("  iterator finally (file closed)");
        }
    }

    static void Main()
    {
        foreach (string s in Lines())
        {
            Console.WriteLine("  " + s);
            break;                          // leaves after one line
        }
        Console.WriteLine("after the loop");
    }
}
