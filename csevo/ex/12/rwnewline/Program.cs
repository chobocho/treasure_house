// 슬라이드 p12-v11-raw-newline — 내용 속 줄바꿈은 소스의 것, C# 11.0
using System;

class App
{
    static void Main()
    {
        string s = """
            a
            b
            """;
        Console.WriteLine(s.Length + " " + s.Contains('\r'));
        Console.WriteLine("""a\nb""".Length);         // no escapes
        string crlf = s.ReplaceLineEndings("\r\n");
        Console.WriteLine(crlf.Length + " " + crlf.Contains('\r'));
        Console.WriteLine(s == "a" + Environment.NewLine + "b");
    }
}
