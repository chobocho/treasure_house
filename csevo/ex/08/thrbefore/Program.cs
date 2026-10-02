// 슬라이드 p8-v7-throw-before — throw 가 문장뿐이던 C# 6, C# 6
using System;

class App
{
    static string name;

    static void SetName(string value)
    {
        if (value == null)
            throw new ArgumentNullException("value");
        name = value;
    }

    static string Initial()
    {
        if (name.Length == 0)
            throw new InvalidOperationException("empty");
        return name.Substring(0, 1);
    }

    static void Main()
    {
        SetName("Ada");
        Console.WriteLine(Initial());
    }
}
