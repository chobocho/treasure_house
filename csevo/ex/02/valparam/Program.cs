// 슬라이드 p2-v1-valparam — 값 전달은 복사, C# 1.0
using System;

struct PointS { public int X; }
class PointC { public int X; }

class App
{
    static void Move(PointS p) { p.X += 10; }
    static void Move(PointC p) { p.X += 10; }

    static PointS Shifted(PointS p)
    {
        p.X += 10;               // changes the local copy
        return p;                // ...and hands back a new copy
    }

    static void Main()
    {
        PointS s = new PointS();
        PointC c = new PointC();
        Move(s);
        Move(c);
        Console.WriteLine("after Move: s.X=" + s.X + " c.X=" + c.X);
        s = Shifted(s);
        Console.WriteLine("after Shifted: s.X=" + s.X);
    }
}
