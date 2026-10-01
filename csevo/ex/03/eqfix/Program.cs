// 슬라이드 p3-v2-eq-fix — T 를 비교하는 세 가지 길, C# 2.0
using System;
using System.Collections.Generic;

class App
{
    static bool Same<T>(T a, T b)
    {
        return EqualityComparer<T>.Default.Equals(a, b);
    }

    static bool SameRef<T>(T a, T b) where T : class
    {
        return a == b;                    // reference comparison only
    }

    static bool IsNull<T>(T x)
    {
        return x == null;                 // allowed with no constraint
    }

    static void Main()
    {
        string s1 = "ab";
        string s2 = new string(new char[] { 'a', 'b' });
        Console.WriteLine(s1 == s2);
        Console.WriteLine(Same(s1, s2));
        Console.WriteLine(SameRef(s1, s2));
        Console.WriteLine(Same(3, 3));
        Console.WriteLine(IsNull(0) + " " + IsNull<string>(null));
    }
}
