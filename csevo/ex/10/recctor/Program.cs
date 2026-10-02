// 슬라이드 p10-v9-rec-ctor — 다른 생성자는 this(...) 를 거친다, C# 9.0
using System;

record Point(int X, int Y)
{
    public Point(int both) : this(both, both) { }   // must chain
#if BAD
    public Point(string s) { }                      // no this(...)
#endif
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Point(7));
        Console.WriteLine(new Point(1, 2));
    }
}
