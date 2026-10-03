// 슬라이드 p12-v11-raw — 원시 문자열 리터럴, C# 11.0
using System;

class App
{
    static void Main()
    {
        string one = """C:\temp\new "file".txt""";   // single line
        string json = """
            {
              "name": "Ada",
              "path": "C:\\temp"
            }
            """;                                   // multi line
        Console.WriteLine(one);
        Console.WriteLine(json);
        Console.WriteLine(json.Length);
    }
}
