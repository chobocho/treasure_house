// 슬라이드 p9-v8-shadow-tp — 형식 매개변수를 가리면 경고, C# 8.0
using System;

class App
{
    static void Show<T>(T value)
    {
        Inner(42);

        void Inner<T>(T other)                  // hides Show's T
            => Console.WriteLine(typeof(T).Name + " " + other);

        Console.WriteLine(typeof(T).Name + " " + value);
    }

    static void Main() => Show("text");
}
