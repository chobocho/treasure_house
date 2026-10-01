// 슬라이드 p2-v1-string — 바뀌지 않는 문자열, C# 1.0
using System;

class App
{
    static void Main()
    {
        string s = "csharp";
        s.ToUpper();                          // result thrown away
        Console.WriteLine(s);
        string t = s.ToUpper();
        Console.WriteLine(t);

        string a = "one";
        string b = a;
        b += "-two";                          // b: a new string
        Console.WriteLine(a + " / " + b);

        Console.WriteLine(s[0] + " " + s.Length);
        Console.WriteLine(s.Replace("sharp", "#") + " " + s);
        Console.WriteLine(("" == String.Empty) + " " + "".Length);
    }
}
