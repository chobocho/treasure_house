// 슬라이드 p3-v2-add-trap — T 끼리 더할 수 없다, C# 2.0
using System;

class App
{
    static T Sum<T>(T[] xs)
    {
        T total = default(T);
        foreach (T x in xs)
        {
            total = total + x;
        }
        return total;
    }

    static void Main()
    {
        Console.WriteLine(Sum(new int[] { 1, 2, 3 }));
    }
}
