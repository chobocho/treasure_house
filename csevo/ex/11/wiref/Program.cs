// 슬라이드 p11-v10-wi-ref — 참조를 담은 구조체의 with, C# 10.0
using System;

struct Team
{
    public string Name;
    public string[] Members;                // a reference
}

class App
{
    static void Main()
    {
        var a = new Team
            { Name = "red", Members = new[] { "ann", "bob" } };
        var b = a with { Name = "blue" };
        b.Members[0] = "cid";               // shared array
        Console.WriteLine(a.Name + " " + string.Join(",", a.Members));
        Console.WriteLine(b.Name + " " + string.Join(",", b.Members));
        Console.WriteLine(ReferenceEquals(a.Members, b.Members));
        var c = a with { Members = (string[])a.Members.Clone() };
        c.Members[1] = "dan";
        Console.WriteLine(string.Join(",", a.Members) + " / "
            + string.Join(",", c.Members));
    }
}
