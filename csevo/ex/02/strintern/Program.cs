// 슬라이드 p2-v1-strintern — 문자열 == 과 인턴, C# 1.0
using System;

class App
{
    static void Main()
    {
        string a = "hello";
        string b = "hel" + "lo";              // constant: folded
        char[] cs = { 'h', 'e', 'l', 'l', 'o' };
        string c = new string(cs);            // built at run time

        Console.WriteLine("a == c          " + (a == c));
        Console.WriteLine("a.Equals(c)     " + a.Equals(c));
        Console.WriteLine("Ref(a, b)       " + ReferenceEquals(a, b));
        Console.WriteLine("Ref(a, c)       " + ReferenceEquals(a, c));
        string d = String.Intern(c);
        Console.WriteLine("Ref(a, Intern)  " + ReferenceEquals(a, d));
        bool known = String.IsInterned(c) != null;
        Console.WriteLine("IsInterned(c)   " + known);
    }
}
