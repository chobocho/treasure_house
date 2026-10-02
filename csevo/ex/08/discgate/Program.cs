// 슬라이드 p8-v7-discard — 버리기 _, C# 7.0
using System;

class App
{
    static int Log(string s)
    {
        Console.WriteLine(s);
        return s.Length;
    }

    static void Main()
    {
        _ = Log("called for its side effect");  // standalone discard
    }
}
