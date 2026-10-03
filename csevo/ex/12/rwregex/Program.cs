// 슬라이드 p12-v11-raw-regex — 같은 정규식, 세 가지 리터럴, C# 11.0
using System;
using System.Text.RegularExpressions;

class App
{
    static void Main()
    {
        string regular = "\"(\\w+)\\\\(\\d+)\"";
        string verbatim = @"""(\w+)\\(\d+)""";
        string raw = """
            "(\w+)\\(\d+)"
            """;
        Console.WriteLine(raw);
        Console.WriteLine(regular == verbatim && verbatim == raw);
        Match m = Regex.Match("""key "tea\42" end""", raw);
        Console.WriteLine(m.Groups[1].Value + " " + m.Groups[2].Value);
    }
}
