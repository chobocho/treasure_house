// 슬라이드 p9-v8-ro-copy — in 매개변수와 readonly 멤버, C# 8.0
using System;

struct V
{
    public int X;

    // both write the static field S while running; neither writes this
    public int ReadPlain() { App.S.X = 99; return X; }
    public readonly int ReadRo() { App.S.X = 99; return X; }
}

class App
{
    public static V S;

    static int Plain(in V v) => v.ReadPlain();   // hidden copy of v
    static int Ro(in V v) => v.ReadRo();         // no copy

    static void Main()
    {
        S.X = 1;
        Console.WriteLine("plain member    sees " + Plain(in S));
        S.X = 1;
        Console.WriteLine("readonly member sees " + Ro(in S));
    }
}
