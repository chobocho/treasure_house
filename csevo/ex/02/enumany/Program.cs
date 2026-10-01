// 슬라이드 p2-v1-enumany — 어떤 정수든 열거형 값이 된다, C# 1.0
using System;

enum Color { Red, Green, Blue }

class App
{
    static string Name(Color c)
    {
        switch (c)
        {
            case Color.Red: return "red";
            case Color.Green: return "green";
            case Color.Blue: return "blue";
            default: return "?? " + c;
        }
    }

    static void Main()
    {
        Color c = (Color)42;             // no check at all
        Console.WriteLine(c);
        Console.WriteLine(Enum.IsDefined(typeof(Color), c));
        Console.WriteLine(Name(c));

        Color zero = 0;                  // literal 0 converts
        Console.WriteLine(zero);
        Color last = Color.Blue;
        last++;                          // no wrap, no check
        Console.WriteLine(last + " " + Name(last));
    }
}
