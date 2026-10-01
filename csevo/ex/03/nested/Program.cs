// 슬라이드 p3-v2-nested — 제네릭 클래스 안의 중첩 형식, C# 2.0
using System;

class Outer<T>
{
    public class Inner
    {
        public T Value;                   // Inner sees Outer's T
    }
}

class App
{
    static void Main()
    {
        Outer<int>.Inner a = new Outer<int>.Inner();
        a.Value = 5;
        Outer<string>.Inner b = new Outer<string>.Inner();
        b.Value = "x";
        Console.WriteLine(a.GetType());
        Console.WriteLine(b.GetType());
        Type open = typeof(Outer<>.Inner);
        Console.WriteLine(open.GetGenericArguments().Length);
    }
}
