// 슬라이드 p15-v14-xm-dup — 같은 수신자의 블록은 한 선언 공간, C# 14
using System;
using System.Collections.Generic;

static class Ext
{
    public static string First(this IList<int> xs) => "this " + xs[0];

    extension(IList<int> xs)               // same receiver type
    {
        public string Last() => "block " + xs[xs.Count - 1];
#if DUP1
        public string First() => "block";  // clashes with 'this'
#endif
    }

    extension(IList<int> ys)               // a second block
    {
        public int Size => ys.Count;
#if DUP2
        public int Last => 0;              // clashes with Last()
#endif
    }
}

class Program
{
    static void Main()
    {
        IList<int> xs = new[] { 1, 2, 3 };
        Console.WriteLine(xs.First() + ", " + xs.Last() + ", "
            + xs.Size);
    }
}
