// 슬라이드 p7-v6-interp-escape — 중괄호와 따옴표, C# 6.0
using System;

class App
{
    static void Main()
    {
        int x = 7;
        string[] tags = { "a", "b" };

        Console.WriteLine($"{{x}} = {x}");           // {{ and }}
        Console.WriteLine($"{{{x}}}");               // {{ {x} }}
        Console.WriteLine($"\"{x}\" \\{x}");         // escapes as usual
        Console.WriteLine($"{"quoted"} {tags[0] + "!"}");
        Console.WriteLine($"{string.Join("+", tags)}");
        Console.WriteLine($"{new { x }}");           // { } in a hole
        Console.WriteLine($@"C:\{x}\""q""");         // verbatim form
    }
}
