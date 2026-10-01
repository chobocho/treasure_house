// 슬라이드 p3-v2-constraints — 형식 매개변수 제약, C# 2.0
using System;

class App
{
    // the constraint is what lets the body call CompareTo
    static T Max<T>(T a, T b) where T : IComparable<T>
    {
        return a.CompareTo(b) >= 0 ? a : b;
    }

    static void Main()
    {
        Console.WriteLine(Max(3, 7));
        Console.WriteLine(Max("pear", "apple"));
        Console.WriteLine(Max(2.5, -1.0));
    }
}
