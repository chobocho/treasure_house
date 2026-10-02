// 슬라이드 p8-v7_1-default-nrt — default 와 nullable 참조 형식, C# 7.1
using System;

class App
{
    static string Name(bool known) => known ? "Ada" : default;

    static void Main()
    {
        string s = default;
        Console.WriteLine((s == null) + " " + (Name(false) == null));
    }
}
