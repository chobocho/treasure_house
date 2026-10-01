// 슬라이드 p2-v1-equals — 구조체의 Equals 는 값 비교, C# 1.0
using System;

struct PointS
{
    public int X, Y;
    public PointS(int x, int y) { X = x; Y = y; }
}

class PointC
{
    public int X, Y;
    public PointC(int x, int y) { X = x; Y = y; }
}

class App
{
    static void Main()
    {
        PointS a = new PointS(1, 2), b = new PointS(1, 2);
        PointC c = new PointC(1, 2), d = new PointC(1, 2);
        Console.WriteLine("struct Equals: " + a.Equals(b));
        Console.WriteLine("class  Equals: " + c.Equals(d));
        Console.WriteLine("class  ==    : " + (c == d));
        PointC e = c;
        Console.WriteLine("same object  : " + (c == e));
    }
}
