// 슬라이드 p8-sum-cs8 — C# 8 이 7.x 위에 올린 것, C# 8.0
using System;

struct Temp
{
    public double C;
    public Temp(double c) { C = c; }
    public readonly double F => C * 9 / 5 + 32;   // a readonly member
}

ref struct Scope
{
    public void Dispose() { Console.WriteLine("disposed"); }
}

class App
{
    static void Main()
    {
        Span<int> s = stackalloc[] { 1, 2, 3, 4, 5 };
        Span<int> mid = s[1..^1];                 // a range on a Span
        Console.WriteLine(mid.Length + " " + mid[0]);
        Console.WriteLine(new Temp(100).F);
        using (var sc = new Scope())              // Dispose by pattern
        {
            Console.WriteLine("in scope");
        }
    }
}
