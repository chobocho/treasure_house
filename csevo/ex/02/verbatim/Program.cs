// 슬라이드 p2-v1-verbatim — 축자 문자열 @"…", C# 1.0
using System;

class App
{
    static void Main()
    {
        string a = "C:\temp\new";             // \t and \n are escapes
        string b = @"C:\temp\new";            // \ is just a char
        Console.WriteLine("[" + a + "] " + a.Length);
        Console.WriteLine("[" + b + "] " + b.Length);

        string q = @"say ""hi""";             // "" is one quote
        Console.WriteLine(q);

        string two = @"line 1
line 2";                                      // newline kept as is
        Console.WriteLine(two.Split('\n').Length + " lines");
        Console.WriteLine(@"C:\temp" == "C:\\temp");
    }
}
