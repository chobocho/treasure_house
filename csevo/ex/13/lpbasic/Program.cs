// 슬라이드 p13-v12-lambda-params — 람다의 params 배열, C# 12
using System;

class Program
{
    static void Main()
    {
        var counter = (params int[] xs) => xs.Length;
        Console.WriteLine(counter() + " " + counter(1, 2, 3));
        Console.WriteLine(counter(new[] { 4, 5 }));   // an array, too

        var join = (string sep, params string[] parts) =>
            string.Join(sep, parts);
        Console.WriteLine(join("-", "a", "b", "c"));
        Console.WriteLine(counter.GetType().Name);
    }
}
