// 슬라이드 p3-v2-yield-break — yield break 로 끝내기, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static IEnumerable<string> Lines(string[] all)
    {
        foreach (string s in all)
        {
            if (s == "END") yield break;  // MoveNext now returns false
            if (s.Length == 0) continue;
            yield return s;
        }
        Console.WriteLine("(ran off the end)");
    }

    static void Main()
    {
        string[] a = new string[] { "a", "", "b", "END", "c" };
        foreach (string s in Lines(a)) Console.WriteLine(s);
        string[] b = new string[] { "x" };
        foreach (string s in Lines(b)) Console.WriteLine(s);
    }
}
