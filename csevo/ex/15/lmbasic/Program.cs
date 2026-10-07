// 슬라이드 p15-v14-lambdamod — 형식 없는 매개변수에 한정자, C# 14
using System;

delegate bool TryParse<T>(string text, out T result);

class Program
{
    static void Show<T>(TryParse<T> parse, string s) =>
        Console.WriteLine(parse(s, out T v) ? "ok " + v : "fail");

    static void Main()
    {
        // C# 13: every parameter needs its type once one has a modifier
        TryParse<int> p13 = (string text, out int result) =>
            int.TryParse(text, out result);
        // C# 14: modifiers without types
        TryParse<int> p14 = (text, out result) =>
            int.TryParse(text, out result);
        TryParse<double> d14 = (text, out result) =>
            double.TryParse(text, out result);
        Show(p13, "12");
        Show(p14, "x");
        Show(d14, "2.5");
    }
}
