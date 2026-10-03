// 슬라이드 p11-v10-rs-custom — Equals 만 직접 쓰면, C# 10.0
using System;

record struct Name(string Value)
{
    public bool Equals(Name other) =>
        string.Equals(Value, other.Value,
            StringComparison.OrdinalIgnoreCase);
#if BAD
    public static bool operator ==(Name a, Name b) => a.Equals(b);
#endif
}

class App
{
    static void Main()
    {
        var a = new Name("Ann");
        var b = new Name("ANN");
        Console.WriteLine(a == b);
        Console.WriteLine(a.GetHashCode() == b.GetHashCode());
    }
}
