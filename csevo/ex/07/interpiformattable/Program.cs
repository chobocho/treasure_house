// 슬라이드 p7-v6-interp-target — 형식은 받는 쪽이 정한다, C# 6.0
using System;

class App
{
    static string Kind(object o)
    {
        return o.GetType().Name;
    }

    static void Main()
    {
        int x = 1;
        var v = $"{x}";                    // no target type: string
        string s = $"{x}";
        object o = $"{x}";                 // object: still string
        IFormattable i = $"{x}";
        FormattableString f = $"{x}";

        Console.WriteLine("var               " + Kind(v));
        Console.WriteLine("string            " + Kind(s));
        Console.WriteLine("object            " + Kind(o));
        Console.WriteLine("IFormattable      " + Kind(i));
        Console.WriteLine("FormattableString " + Kind(f));
        Console.WriteLine("cast              " +
            Kind((IFormattable)$"{x}"));
    }
}
