// 슬라이드 p3-v2-bool3 — bool? 의 세 값 논리, C# 2.0
using System;

class App
{
    static string S(bool? b)
    {
        return b.HasValue ? b.Value.ToString() : "null";
    }

    static void Main()
    {
        bool? t = true;
        bool? f = false;
        bool? u = null;
        Console.WriteLine("u & f = " + S(u & f));
        Console.WriteLine("u & t = " + S(u & t));
        Console.WriteLine("u | t = " + S(u | t));
        Console.WriteLine("u | f = " + S(u | f));
        Console.WriteLine("!u    = " + S(!u));
        Console.WriteLine("u == true: " + (u == true));
    }
}
