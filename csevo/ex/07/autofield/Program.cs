// 슬라이드 p7-v6-auto-field14 — field 와 속성 초기화자, C# 14.0
using System;

class Tag
{
    public string Name
    {
        get;
        set => field = value.Trim().ToLowerInvariant();
    } = "  Draft ";               // goes to the field, not the setter

    public Tag()
    {
    }

    public Tag(string name)
    {
        Name = name;              // goes through the setter
    }
}

class Program
{
    static void Main()
    {
        Console.WriteLine("[" + new Tag().Name + "]");
        Console.WriteLine("[" + new Tag("  Final ").Name + "]");
    }
}
