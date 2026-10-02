// 슬라이드 p10-v9-pat-andor — and 와 or, C# 9.0
using System;

class App
{
    // whats-new's IsLetter: and binds tighter than or
    static bool IsLetter(char c) =>
        c is >= 'a' and <= 'z' or >= 'A' and <= 'Z';

    static bool IsSmall(int i) => i is 0 or 1 or 2;

    static void Main()
    {
        foreach (char c in "aZ5_")
            Console.Write(c + ":" + IsLetter(c) + " ");
        Console.WriteLine();
        Console.WriteLine(IsSmall(2) + " " + IsSmall(3));
    }
}
