// 슬라이드 p3-v2-nullable-why — '값 없음' 을 따로 들고 다니기, C# 1.0
using System;

class App
{
    // C# 1 style: a bool result plus an out parameter
    static bool TryAge(string s, out int age)
    {
        age = 0;
        if (s.Length == 0) return false;
        age = int.Parse(s);
        return true;
    }

    static void Main()
    {
        int age;
        if (TryAge("", out age)) Console.WriteLine(age);
        else Console.WriteLine("no age");
        Console.WriteLine(age);           // still an int: 0
    }
}
