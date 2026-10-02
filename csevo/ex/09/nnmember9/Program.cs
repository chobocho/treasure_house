// 슬라이드 p9-v8-nrt-membernotnull — MemberNotNull 은 C# 9, C# 9.0
#nullable enable
using System;
using System.Diagnostics.CodeAnalysis;

class Conn
{
    string name;

    public Conn() { Reset(); }               // no CS8618

    [MemberNotNull(nameof(name))]
    void Reset() { name = "default"; }

    public int Len => name.Length;
}

class App
{
    static void Main()
    {
        Console.WriteLine(new Conn().Len);
    }
}
