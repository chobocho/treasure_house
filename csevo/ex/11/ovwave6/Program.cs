// 슬라이드 p11-v10-wave6 — 경고 웨이브 6(CS8826), C# 10.0
using System;

partial class Shape
{
    public partial string Name(int sides);
}

partial class Shape
{
    public partial string Name(int count) => count + " sides";
}

class App
{
    static void Main() =>
        Console.WriteLine(new Shape().Name(sides: 3));
}
