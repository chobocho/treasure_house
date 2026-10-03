// 슬라이드 p11-v10-decon — 분해에서 선언과 대입을 섞기, C# 10.0
using System;

class Pt { public int X { get; set; } }

class App
{
    static (int, string) Next(int n) => (n + 1, "n" + (n + 1));

    static void Main()
    {
        var p = new Pt();
        string[] slots = new string[2];
        // a property, a new local and an array element at once
        (p.X, var label, slots[1]) = (3, "three", "second");
        Console.WriteLine($"{p.X} {label} {slots[1]}");

        // keep one value outside the loop, declare the other inside
        int last = 0;
        for (int k = 0; k < 3; k++)
        {
            (last, string name) = Next(last);
            Console.Write(name + " ");
        }
        Console.WriteLine($"last={last}");

        int i;
        for ((i, var j) = (0, 3); i < j; i++, j--)
            Console.Write($"({i},{j}) ");
        Console.WriteLine();
#if BAD
        foreach ((last, var v) in new[] { (1, 2) }) { }
#endif
    }
}
