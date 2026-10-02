// 슬라이드 p9-v8-nrt-fool — 메서드 안을 들여다보지 않는 분석, C# 8.0
#nullable enable
using System;

class Box
{
    public string? Name = "box";
}

class App
{
    static readonly Box box = new Box();

    static void Clear() => box.Name = null;

    static void Main()
    {
        if (box.Name != null)
        {
            Clear();                       // the analysis trusts us
            Console.WriteLine(box.Name.Length);   // no warning
        }
    }
}
