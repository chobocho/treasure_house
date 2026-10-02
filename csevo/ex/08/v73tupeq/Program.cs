// 슬라이드 p8-v7_3-tupleeq — 튜플의 == 와 !=, C# 7.3
using System;

class App
{
    static void Main()
    {
        var a = (1, "x");
        (int n, string s) b = (1, "x");       // other names
        Console.WriteLine(a == b);            // element-wise
        Console.WriteLine(a != (1, "y"));
        Console.WriteLine((1L, 2) == (1, 2L)); // each pair widened
        var nest = (1, (2, 3));
        Console.WriteLine(nest == (1, (2, 3)));

        (int, int)? none = null;
        (int, int)? some = (1, 2);
        Console.WriteLine(none == null);      // lifted to nullable
        Console.WriteLine(some == (1, 2));
        Console.WriteLine(none == some);
    }
}
