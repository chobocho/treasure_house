// 슬라이드 p15-v14-pe-break — 반환 형식 partial 의 깨지는 변경, C# 14
using System;

class partial
{
    public override string ToString() => "a partial object";
}

class Factory
{
#if FIX
    @partial Make() => new partial();
#else
    partial Make() => new partial();       // a method in C# 13
#endif

    static void Main() => Console.WriteLine(new Factory().Make());
}
