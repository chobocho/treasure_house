// 슬라이드 p11-v10-st-assign — 초기화자 없는 필드는 C# 10 에서, C# 10.0
using System;

struct S
{
    public int X = 1;
    public object Y;
    public S() { }                          // Y is never assigned
}

class App
{
    static void Main()
    {
        var s = new S();
        Console.WriteLine(s.X + " " + (s.Y ?? "null"));
    }
}
