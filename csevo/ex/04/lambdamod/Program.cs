// 슬라이드 p4-v3-lambda-mod — 형식 없이 out 매개변수, C# 14
using System;

delegate bool TryParse(string s, out int value);

class App
{
    static void Main()
    {
        // C# 3: with a modifier, every parameter needs its type
        TryParse a = (string s, out int v) => int.TryParse(s, out v);
        // C# 14: the modifier alone is enough
        TryParse b = (s, out v) => int.TryParse(s, out v);
        int n;
        Console.WriteLine(a("12", out n) + " " + n);
        Console.WriteLine(b("x", out n) + " " + n);
    }
}
