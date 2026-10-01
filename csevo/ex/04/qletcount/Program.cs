// 슬라이드 p4-v3-query-let-once — let 은 원소마다 한 번, C# 3.0
using System;
using System.Linq;

class Program
{
    static int calls;

    static int Score(string w)
    {
        calls++;
        return w.Length * 10;
    }

    static void Main()
    {
        string[] words = { "melon", "fig", "banana", "kiwi" };

        calls = 0;
        int[] a = (from w in words
                   where Score(w) > 40
                   select Score(w)).ToArray();
        Console.WriteLine(string.Join(" ", a) + "  calls " + calls);

        calls = 0;
        int[] b = (from w in words
                   let s = Score(w)
                   where s > 40
                   select s).ToArray();
        Console.WriteLine(string.Join(" ", b) + "  calls " + calls);
    }
}
