// 슬라이드 p12-v11-raw-format — 원시 보간의 형식 문자열, C# 11.0
using System;

class App
{
    static void Main()
    {
        double price = 3.5;
        string item = "tea";
        FormattableString fs = $$"""
            {"item": "{{item,-5}}", "price": {{price:F2}}}
            """;
        Console.WriteLine(fs.Format);
        Console.WriteLine(fs.ArgumentCount);
        Console.WriteLine(fs.ToString());
        Console.WriteLine($$"""{{{12:X}}}""");
        Console.WriteLine($"{{{12:X}}}");
    }
}
