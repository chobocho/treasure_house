// 슬라이드 p2-v1-utf16 — string 은 UTF-16 코드 단위의 열, C# 1.0
using System;

class App
{
    static void Main()
    {
        string s = "A\u00E9\uD83D\uDE00";     // A, e-acute, one emoji
        Console.WriteLine("Length = " + s.Length);
        for (int i = 0; i < s.Length; i++)
        {
            Console.WriteLine(i + ": U+" + ((int)s[i]).ToString("X4"));
        }
        Console.WriteLine(Char.IsSurrogate(s[2]));
        Console.WriteLine(sizeof(char));
    }
}
