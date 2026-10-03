// 슬라이드 p11-v10-rs-limits — record struct 가 거절하는 것, C# 10.0
using System;

record struct A(ref int X);                 // ref parameter
record struct C(int X)
{
    public C Clone() => this;               // member named Clone
}

class App
{
    static void Main() => Console.WriteLine(new C(1));
}
