// 슬라이드 p3-v2-shadow-t — 바깥 T 를 가리는 메서드의 T, C# 2.0
using System;

class Holder<T>
{
    public T Value;

    public string Describe<T>(T other)    // a new, different T
    {
        return typeof(T).Name;
    }
}

class App
{
    static void Main()
    {
        Holder<int> h = new Holder<int>();
        h.Value = 1;
        Console.WriteLine(h.Describe("s") + " " + h.Value);
    }
}
