// 슬라이드 p3-v2-generic-methods — 제네릭 메서드와 형식 유추, C# 2.0
using System;

class App
{
    static void Swap<T>(ref T a, ref T b)
    {
        T t = a;
        a = b;
        b = t;
    }

    static T[] Repeat<T>(T value, int n)
    {
        T[] r = new T[n];
        for (int i = 0; i < n; i++)
        {
            r[i] = value;
        }
        return r;
    }

    static void Main()
    {
        int a = 1, b = 2;
        Swap<int>(ref a, ref b);          // type argument written out
        Console.WriteLine(a + " " + b);
        Swap(ref a, ref b);               // T inferred from arguments
        Console.WriteLine(a + " " + b);
        string[] r = Repeat("ab", 3);     // T = string
        Console.WriteLine(string.Join("-", r));
        Console.WriteLine(Repeat(1.5, 2).GetType());
    }
}
