// 슬라이드 p4-v3-autoprop-field14 — 접근자 안에서 field 키워드, C# 14
using System;

class Person
{
    public string Name
    {
        get;
        set { field = value.Trim(); }    // the backing field by keyword
    }
}

class App
{
    static void Main()
    {
        Person p = new Person();
        p.Name = "  Ann  ";
        Console.WriteLine("[" + p.Name + "]");
    }
}
