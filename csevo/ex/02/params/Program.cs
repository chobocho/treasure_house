// 슬라이드 p2-v1-params — params 배열, C# 1.0
using System;

class App
{
    static int Sum(params int[] xs)
    {
        int s = 0;
        foreach (int x in xs) s += x;
        Console.Write("(" + xs.Length + " args) ");
        return s;
    }

    static void Main()
    {
        Console.WriteLine(Sum());               // empty array, not null
        Console.WriteLine(Sum(1));
        Console.WriteLine(Sum(1, 2, 3));
        Console.WriteLine(Sum(new int[] { 4, 5 })); // normal form
        Console.WriteLine(String.Concat("a", "b", "c", "d", "e"));
        Console.WriteLine("{0}-{1}-{2}-{3}", 1, 2, 3, 4);
    }
}
