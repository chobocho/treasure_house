// 슬라이드 p3-v2-lifted-compare — null 과의 비교, C# 2.0
using System;

class App
{
    static void Main()
    {
        int? n = null;
        int? m = null;
        Console.WriteLine(n < 1);         // False
        Console.WriteLine(n >= 1);        // False as well
        Console.WriteLine(n == m);        // True: both null
        Console.WriteLine(n != 1);        // True
        Console.WriteLine(n <= m);        // False, though n == m
        bool notLess = !(n < 1);
        Console.WriteLine(notLess == (n >= 1));
    }
}
