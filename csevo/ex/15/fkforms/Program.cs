// 슬라이드 p15-v14-fk-forms — field 를 쓰는 접근자의 꼴, C# 14
using System;

class Doc
{
    static int computed;
    static string Compute() { computed++; return "title"; }

    public string Title => field ??= Compute();          // lazy
    public int Version { get => field; set => field = value + 1; }
    public string Tag { set => field = value.ToUpper(); } // set only
    public string Shout => Tag2 ?? "(none)";
    string Tag2 => field;                                // never set
    public int Count
    {
        get; private set => field = Math.Max(field, value);
    }

    static void Main()
    {
        var d = new Doc();
        Console.WriteLine(d.Title + " " + d.Title
            + " computed=" + computed);
        d.Version = 1;
        Console.WriteLine("Version " + d.Version);
        d.Tag = "x";
        d.Count = 5; d.Count = 3;
        Console.WriteLine("Count " + d.Count + " " + d.Shout);
    }
}
