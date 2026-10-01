// 슬라이드 p2-v1-rostruct — readonly 구조체 필드의 복사, C# 1.0
using System;

struct Counter
{
    public int N;
    public void Bump() { N++; }
}

class Holder
{
    public readonly Counter Ro;
    public Counter Rw;

    public void BumpBoth()
    {
        Ro.Bump();                            // works on a copy
        Rw.Bump();                            // works on the field
    }
}

class App
{
    static void Main()
    {
        Holder h = new Holder();
        h.BumpBoth();
        h.BumpBoth();
        Console.WriteLine("readonly " + h.Ro.N + ", other " + h.Rw.N);
    }
}
