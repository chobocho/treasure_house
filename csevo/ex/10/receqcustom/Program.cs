// 슬라이드 p10-v9-rec-eqcustom — Equals(R) 를 직접 쓰면, C# 9.0
using System;

record Name(string Value)
{
    public virtual bool Equals(Name other) =>
        other != null && string.Equals(Value, other.Value,
            StringComparison.OrdinalIgnoreCase);
}

class App
{
    static void Main()
    {
        Name a = new Name("Ann"), b = new Name("ANN");
        Console.WriteLine(a == b);           // uses our Equals
        Console.WriteLine(a.Equals((object)b));
        Console.WriteLine(a.GetHashCode() == b.GetHashCode());
    }
}
