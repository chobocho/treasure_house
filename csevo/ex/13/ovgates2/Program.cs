// 슬라이드 p13-v12-gates-demo2 — 선언에 쓰는 C# 12 기능 둘, C# 12.0
using System;
using Pair = (int A, int B);                // using type alias

class Box(int v)                            // primary constructor
{
    public int V => v;
}

class App
{
    static void Main()
    {
        Pair p = (1, 2);
        Console.WriteLine($"{p.A} {p.B} {new Box(3).V}");
    }
}
