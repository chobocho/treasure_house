// 슬라이드 p15-v14-xm-iface — 인터페이스의 기본 구현과 확장 속성, C# 14
using System;

interface IShape
{
    double Area { get; }
    string Kind => "shape";                 // C# 8 default member
}

static class ShapeExt
{
    extension(IShape s)
    {
        public bool IsLarge => s.Area > 10;  // C# 14 extension
        public string Label => s.Kind + ":" + s.Area;
    }
}

class Square : IShape
{
    public double Side;
    public double Area => Side * Side;
}

class Program
{
    static void Main()
    {
        var sq = new Square { Side = 4 };
        Console.WriteLine(sq.IsLarge + " " + sq.Label);
        IShape s = sq;
        Console.WriteLine(s.Kind);
#if DIM
        Console.WriteLine(sq.Kind);          // only through IShape
#endif
    }
}
