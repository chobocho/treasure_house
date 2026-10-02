// 슬라이드 p8-v7-throw — throw 식, C# 7.0
using System;

class App
{
    static string name;

    // the three places the proposal allows
    static void SetName(string value) =>
        name = value ?? throw new ArgumentNullException("value");

    static string Initial() =>
        name.Length > 0 ? name.Substring(0, 1)
                        : throw new InvalidOperationException("empty");

    static void Reset() => throw new NotSupportedException();

    static void Try(Action a)
    {
        try { a(); Console.WriteLine("ok: " + name); }
        catch (Exception e) { Console.WriteLine(e.GetType().Name); }
    }

    static void Main()
    {
        Try(() => SetName("Ada"));
        Try(() => SetName(null));
        Try(() => Console.WriteLine(Initial()));
        Try(() => SetName(""));
        Try(() => Console.WriteLine(Initial()));
        Try(Reset);
    }
}
