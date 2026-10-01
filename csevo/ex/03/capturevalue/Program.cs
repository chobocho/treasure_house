// 슬라이드 p3-v2-capture-value — 구조체 변수와 그 사본, C# 2.0
using System;

struct Point { public int X; }

delegate void D();

class App
{
    static D Printer(Point p)            // p is a copy
    {
        return delegate { Console.WriteLine("param " + p.X); };
    }

    static void Main()
    {
        Point pt;
        pt.X = 1;
        D local = delegate { Console.WriteLine("local " + pt.X); };
        D param = Printer(pt);
        Point copy = pt;
        D viaCopy = delegate { Console.WriteLine("copy  " + copy.X); };

        pt.X = 2;                        // change the original
        local();
        param();
        viaCopy();
    }
}
