// 슬라이드 p9-v8-nrt-override — 재정의의 nullable 어긋남, C# 8.0
#nullable enable
using System;

abstract class Base
{
    public abstract string Find(string key);
    public abstract string Name(string? key);
}

class Strict : Base
{
    public override string? Find(string key) => null;   // return
    public override string Name(string key) => key;     // parameter
}

class Loose : Base
{
    public override string Find(string? key) => key ?? "-";
    public override string Name(string? key) => key ?? "-";
}

class App
{
    static void Main()
    {
        Base a = new Strict(), b = new Loose();
        Console.WriteLine((a.Find("k") ?? "null") + " " + b.Find("f")
            + " " + b.Name(null));
    }
}
