// 슬라이드 p13-v12-ld-named — 이름 붙인 인수는 대리자의 이름으로, C# 12
using System;

class Program
{
    static string Pad(string s, int width = 6, char fill = '.') =>
        s.PadLeft(width, fill);

    static void Main()
    {
        var pad = (string s, int width = 6, char fill = '.') =>
            s.PadLeft(width, fill);
        Console.WriteLine(pad("ab"));
        Console.WriteLine(pad("ab", arg3: '*'));   // synthesized names
        var pad2 = Pad;                            // a method group
        Console.WriteLine(pad2("ab", arg3: '-'));
        Console.WriteLine(Pad("ab", fill: '+'));   // the method itself
#if BAD
        Console.WriteLine(pad("ab", fill: '*'));
#endif
    }
}
