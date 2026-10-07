// 슬라이드 p15-v14-sp-udc — 상속을 거치는 사용자 정의 변환, C# 14
using System;

class Base
{
    public string M(Span<string> s) => "Base";
    public string M(int i) => "Base";
}

class Derived : Base
{
    public static implicit operator Derived(ReadOnlySpan<string> r)
        => new Derived();
    public static implicit operator Derived(long l) => new Derived();

    public string M(Derived s) => "Derived";
}

class Program
{
    static void Main()
    {
        Span<string> span = [];
        var d = new Derived();
        Console.WriteLine("d.M(span) -> " + d.M(span));
        Console.WriteLine("d.M(1)    -> " + d.M(1));
    }
}
