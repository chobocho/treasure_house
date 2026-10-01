// 슬라이드 p2-v1-enum — 열거형과 바탕 형식, C# 1.0
using System;

enum Color { Red, Green, Blue }
enum Size : byte { Small = 1, Medium, Large = 10 }

class App
{
    static void Main()
    {
        Color c = Color.Green;
        Console.WriteLine(c + " = " + (int)c);
        Console.WriteLine(Size.Medium + " = " + (byte)Size.Medium);
        Console.WriteLine(Enum.GetUnderlyingType(typeof(Color)));
        Console.WriteLine(Enum.GetUnderlyingType(typeof(Size)));
        Console.WriteLine(sizeof(Size));

        Color p = (Color)Enum.Parse(typeof(Color), "Blue");
        Color q = (Color)Enum.Parse(typeof(Color), "blue", true);
        Console.WriteLine(p + " " + (p == q));
        Console.WriteLine(Color.Red < Color.Blue);
        Console.WriteLine(Color.Red + 2);
    }
}
