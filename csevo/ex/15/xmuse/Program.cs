// 슬라이드 p15-v14-xm-use — null 수신자, 대리자, 속성 패턴, C# 14
using System;

static class Ext
{
    extension(string s)
    {
        public bool IsBlank => s == null || s.Trim().Length == 0;
        public string Wrap(string w) => w + s + w;
    }
}

class Program
{
    static void Main()
    {
        string none = null;
        Console.WriteLine(none.IsBlank + " " + "  ".IsBlank);
        Func<string, string> f = "x".Wrap;          // receiver bound
        Console.WriteLine(f("*") + " " + f.Target);
        Func<string, string, string> g = Ext.Wrap;  // static form
        Console.WriteLine(g("y", "|"));
        object o = " ";
        if (o is string { IsBlank: true }) Console.WriteLine("pattern");
        Console.WriteLine(nameof(Ext.get_IsBlank) + " "
            + nameof(Ext.Wrap));
#if NAMEOF
        Console.WriteLine(nameof(none.IsBlank));
#elif DYN
        dynamic d = "z";
        Console.WriteLine(d.IsBlank);
#endif
    }
}
