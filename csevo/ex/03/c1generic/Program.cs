// 슬라이드 p3-v2-c1-generic-call — 꺾쇠 없는 제네릭 호출, C# 1.0
using System;

class App
{
    static void Main()
    {
        int[] xs = new int[] { 3, 1, 2 };
        Array.Resize(ref xs, 4);          // Array.Resize<T>, T inferred
        Array.Sort(xs);
        Console.WriteLine(xs.Length + " " + xs[0] + " " + xs[3]);
        Console.WriteLine(Array.IndexOf(xs, 3));
    }
}
