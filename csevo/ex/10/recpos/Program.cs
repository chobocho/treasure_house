// 슬라이드 p10-v9-rec-positional — 위치 레코드, C# 9.0
using System;

public record R(int P1, string P2 = "xyz");

class App
{
    static void Main()
    {
        R r = new R(12);                      // primary constructor
        Console.WriteLine(r.P1 + " " + r.P2); // init-only properties
        (int p1, string p2) = r;              // Deconstruct
        Console.WriteLine($"p1: {p1}, p2: {p2}");
        R named = new R(P2: "abc", P1: 1);    // parameter names
        Console.WriteLine(named);
        R both = new R(3) { P2 = "set" };     // init in initializer
        Console.WriteLine(both);
    }
}
