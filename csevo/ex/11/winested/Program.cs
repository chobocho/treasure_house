// 슬라이드 p11-v10-wi-nested — 안쪽 구조체의 멤버를 바꾸려면, C# 10.0
using System;

record struct Point(int X, int Y);
record struct Line(Point From, Point To);

class App
{
    static void Main()
    {
        var a = new Line(new Point(0, 0), new Point(5, 5));
        var b = a with { To = a.To with { Y = 9 } };  // nested with
        Console.WriteLine(b);
#if BAD
        var c = a with { To.Y = 9 };
#endif
    }
}
