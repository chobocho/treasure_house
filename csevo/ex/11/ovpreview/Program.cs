// 슬라이드 p11-v10-preview — C# 10 의 미리 보기 기능 둘, C# 10.0
using System;

class TagAttribute<T> : Attribute { }        // generic attribute

interface IZero<T> where T : IZero<T>
{
    static abstract T Zero { get; }          // static abstract member
}

struct Num : IZero<Num>
{
    public static Num Zero => default;
}

[Tag<int>]
class App
{
    static void Main() => Console.WriteLine(Num.Zero);
}
