// 슬라이드 p8-v7-outv-init73 — 초기화자 안의 out var, C# 7.3
using System;

class B
{
    public B(int i, out int j) { j = i * 2; }
}

class D : B
{
    public D(int i) : base(i, out var j)    // a constructor initializer
    {
        Console.WriteLine("j = " + j);
    }
}

class App
{
    static void Main()
    {
        new D(21);
    }
}
