// 슬라이드 p7-v6-immut-rec — 같은 형식을 레코드로, C# 9.0
using System;

sealed record Point(int X, int Y);

class Program
{
    static void Main()
    {
        Point a = new Point(1, 2);
        Point b = a with { X = 5 };
        Console.WriteLine(a + " " + b);
        Console.WriteLine(a.Equals(new Point(1, 2)));
        Console.WriteLine(a == new Point(1, 2));
    }
}
