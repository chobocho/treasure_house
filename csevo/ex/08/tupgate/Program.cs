// 슬라이드 p8-v7-tuple-gate — 튜플 형식과 튜플 리터럴, C# 7.0
using System;

class App
{
    // a tuple return type with element names
    static (string first, string last) Split(string name)
    {
        int i = name.IndexOf(' ');
        return (name.Substring(0, i), name.Substring(i + 1));
    }

    static void Main()
    {
        var n = Split("Anders Hejlsberg");
        Console.WriteLine(n.last + ", " + n.first);
        Console.WriteLine(n.Item1);         // default names still work
        Console.WriteLine(n);
    }
}
