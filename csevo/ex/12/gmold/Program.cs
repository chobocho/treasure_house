// 슬라이드 p12-v11-math-why — 연산자로는 추상화할 수 없던 Sum, C# 10.0
using System;

class App
{
    // T has no operator + : no constraint could say "T has +"
    static T Sum<T>(T[] xs)
    {
        T s = default(T);
        foreach (T x in xs) s = s + x;
        return s;
    }

    static void Main() =>
        Console.WriteLine(Sum(new[] { 1, 2, 3 }));
}
