// 슬라이드 p7-v6-nullcond-userop — 사용자 정의 == 를 안 본다, C# 6.0
using System;

class Handle
{
    public bool Destroyed;
    public string Name = "h1";

    // "destroyed" handles claim to be equal to null
    public static bool operator ==(Handle a, Handle b)
    {
        bool an = (object)a == null || a.Destroyed;
        bool bn = (object)b == null || b.Destroyed;
        if (an || bn) return an && bn;
        return ReferenceEquals(a, b);
    }
    public static bool operator !=(Handle a, Handle b)
    { return !(a == b); }
    public override bool Equals(object o) { return base.Equals(o); }
    public override int GetHashCode() { return 0; }
}

class App
{
    static void Main()
    {
        var h = new Handle { Destroyed = true };
        Console.WriteLine("h == null   " + (h == null));
        Console.WriteLine("h?.Name     " + (h?.Name ?? "(skipped)"));
        string viaEq = h != null ? h.Name : "(skipped)";
        Console.WriteLine("h != null ? " + viaEq);
    }
}
