// 슬라이드 p9-v8-nrt-bang-idiom — null! 과 default! 와 !!, C# 8.0
#nullable enable
using System;

class Service
{
    // set later by Init(); null! silences CS8618
    public string Name = null!;
    public string Tag = default!;
    public void Init() { Name = "svc"; Tag = "t"; }
}

class App
{
    static void Main()
    {
        var s = new Service();
        Console.WriteLine(s.Name == null);   // still null before Init
        s.Init();
        int? n = 3;
        Console.WriteLine(s.Name + s.Tag + n!.Value);  // ! on int?: ok
#if BAD
        string? m = "x";
        string t = m!!;                      // two of them
#endif
    }
}
