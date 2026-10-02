// 슬라이드 p5-v4-dyn-struct — 상자에 든 구조체, C# 4.0
using System;

struct Counter
{
    public int N;
    public void Inc() { N++; }
}

class Program
{
    static void Main()
    {
        object o = new Counter();
        ((Counter)o).Inc();              // unboxed copy
        Console.WriteLine("object : " + ((Counter)o).N);

        dynamic d = new Counter();
        d.Inc();
        d.Inc();
        Console.WriteLine("dynamic: " + d.N);
        d.N = 10;
        Console.WriteLine("dynamic: " + d.N);
    }
}
