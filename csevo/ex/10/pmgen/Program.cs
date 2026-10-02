// 슬라이드 p10-v9-partial — 확장된 partial 메서드, C# 9.0
using System;

interface INamed { string GetName(); }

// The half a person writes: declarations only.
partial class Parser : INamed
{
    public partial bool TryParse(string s, out int value);
    internal partial string Describe();
    public virtual partial string GetName();
}

class App
{
    static void Main()
    {
        var p = new Parser();
        bool ok = p.TryParse("42", out int v);
        Console.WriteLine(ok + " " + v + " " + p.Describe());
        INamed n = p;
        Console.WriteLine(n.GetName());
    }
}
