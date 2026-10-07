// 슬라이드 p15-v14-xm-value — 값 형식 수신자는 복사본이다, C# 14
using System;

struct Point { public int X, Y; }

static class PointExt
{
    extension(Point p)                     // by value: a copy
    {
        public void Reset() { p.X = 0; p.Y = 0; }
        public int Left { get => p.X; set => p.X = value; }
    }

    extension(ref Point p)                 // by reference
    {
        public void Clear() { p.X = 0; p.Y = 0; }
        public int First { get => p.X; set => p.X = value; }
    }
}

class Program
{
    static void Main()
    {
        var pt = new Point { X = 3, Y = 4 };
        pt.Reset();                        // the copy is reset
        pt.Left = 9;                       // no diagnostic, lost
        Console.WriteLine(pt.X + "," + pt.Y);
        pt.First = 7;
        Console.WriteLine(pt.X + "," + pt.Y);
        pt.Clear();
        Console.WriteLine(pt.X + "," + pt.Y);
    }
}
