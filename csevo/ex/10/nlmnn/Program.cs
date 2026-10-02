// 슬라이드 p10-v9-nl-mnn — MemberNotNull 과 MemberNotNullWhen, C# 9.0
using System;
using System.Diagnostics.CodeAnalysis;

class Loader
{
    public string? Text { get; private set; }

    [MemberNotNullWhen(true, nameof(Text))]
    public bool Loaded => Text != null;

    [MemberNotNull(nameof(Text))]
    public void Load(string s)
    {
        Text = s;
#if BAD
        if (s.Length == 0) return;          // exits with Text set...
        Text = null;                        // ...then cleared
#endif
    }
}

class App
{
    static void Main()
    {
        var a = new Loader();
        if (a.Loaded)
            Console.WriteLine(a.Text.Length);    // no CS8602
        a.Load("hello");
        Console.WriteLine(a.Text.Length);        // no CS8602
    }
}
