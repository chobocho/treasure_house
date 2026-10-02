// 슬라이드 p9-v8-ro-warn — readonly 멤버 안의 숨은 복사, C# 8.0
using System;

struct Counter
{
    public int N;

    public void Bump() => N++;              // not readonly

    public readonly int BumpAndRead()
    {
        Bump();                             // runs on a copy of this
        return N;
    }
}

class App
{
    static void Main()
    {
        var c = new Counter();
        Console.WriteLine(c.BumpAndRead());
        Console.WriteLine(c.N);
    }
}
