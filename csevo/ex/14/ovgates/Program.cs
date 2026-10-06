// 슬라이드 p14-v13-gates-demo — 몸체 안의 C# 13 기능 넷, C# 13
using System;
using System.Collections.Generic;
using System.Threading;

class Box { public int[] Items = new int[3]; }

class Program
{
    static readonly Lock gate = new();

    static IEnumerable<int> Iter(int[] a)
    {
        ref int first = ref a[0];          // ref local in iterator
        first = 9;
        yield return a[0];
    }

    static void Main()
    {
#if NOESC
        string esc = "\u001b[0m";
#else
        string esc = "\e[0m";               // \e escape
#endif
        var box = new Box { Items = { [^1] = 7 } };   // ^ in init
        lock (gate)                         // Lock object
        {
            Console.WriteLine((int)esc[0] + " " + box.Items[2]);
        }
        foreach (int x in Iter(new int[2])) Console.WriteLine(x);
    }
}
