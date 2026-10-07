// 슬라이드 p15-v14-ext-static — 정적 확장 멤버, C# 14
using System;
using System.Collections.Generic;

static class ListExt
{
    extension<T>(List<T>)                  // no receiver name
    {
        public static List<T> Of(params T[] items) => new(items);
        public static int Made => 1;       // static property
#if INST
        public int Count2 => 0;            // instance member: no name
#endif
    }

    extension(int)
    {
        public static int Parse2(string s) => int.Parse(s) * 2;
    }

    extension(Math)                        // a static class
    {
        public static int Twice(int x) => x * 2;
    }
}

class Program
{
    static void Main()
    {
        List<int> xs = List<int>.Of(1, 2, 3);
        Console.WriteLine(xs.Count + " " + List<string>.Made);
        Console.WriteLine(int.Parse2("21") + " " + Math.Twice(4));
        Console.WriteLine(ListExt.Of(4, 5).Count);  // a static call
#if VAR
        Console.WriteLine(xs.Of(1).Count);          // on an instance
#endif
    }
}
