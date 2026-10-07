// 슬라이드 p15-v14-fk-null — field 의 nullable 분석, C# 14
using System;

class C
{
    public C() { }      // no warning about Lazy here

    public string Lazy => field ??= Load();
    static string Load() => "loaded";

#if STRICT
    public string Strict { get => field; set => field = value; }
#endif
#if EMPTYSET
    public string Bad
    {
        get => field;
        set { }
    }
#endif
}

class Program
{
    static void Main()
    {
        var c = new C();
        Console.WriteLine(c.Lazy.Length);
    }
}
