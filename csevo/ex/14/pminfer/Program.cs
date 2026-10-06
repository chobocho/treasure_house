// 슬라이드 p14-v13-pm-infer — 배열 하나를 넘기면 T 는 무엇인가, C# 13
using System;

class Program
{
    static void Concat<T>(params ReadOnlySpan<T> items) =>
        Console.WriteLine(typeof(T).Name + " x" + items.Length);

    static void Main()
    {
        int[] arr = { 4, 5 };
        Concat(arr);                // T inferred from arr itself
        Concat<int>(arr);           // explicit T: normal form
        Concat(4, 5);
    }
}
