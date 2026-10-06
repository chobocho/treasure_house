// 슬라이드 p14-v13-es-where — \e 가 통하는 리터럴, C# 13
using System;
using System.Text;

class Program
{
    static string Hex(string s)
        => Convert.ToHexString(Encoding.UTF8.GetBytes(s));

    static void Main()
    {
        int n = 31;
        Console.WriteLine("char         " + (int)'\e');
        Console.WriteLine("string       " + Hex("\e[0m"));
        Console.WriteLine("interpolated " + Hex($"\e[{n}m"));
        Console.WriteLine("utf-8        "
            + Convert.ToHexString("\e[0m"u8));
        Console.WriteLine("verbatim     " + Hex(@"\e"));
        Console.WriteLine("raw          " + Hex("""\e"""));
#if UPPER
        Console.WriteLine('\E');
#endif
    }
}
