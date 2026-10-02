// 슬라이드 p7-v6-autoinit-this — 초기화자에서 this 는 못 쓴다, C# 6.0
using System;

class Box
{
    static int defaultSize = 4;

    public int Size { get; set; } = defaultSize;     // static: fine
#if BAD
    public int Twice { get; set; } = Size * 2;       // instance: no
#endif
    public int Area { get { return Size * Size; } }  // runs later: fine
}

class Program
{
    static void Main()
    {
        Box b = new Box();
        Console.WriteLine(b.Size + " " + b.Area);
    }
}
