// 슬라이드 p13-v12-ld-later — 뒤 버전: 형식 없는 수식어, C# 14
using System;

delegate bool TryParse<T>(string text, out T result);
delegate int Count(params int[] xs);

class Program
{
    static void Main()
    {
        TryParse<int> parse1 = (text, out result) =>
            Int32.TryParse(text, out result);
        Console.WriteLine(parse1("42", out int n) + " " + n);
        Count c = xs => xs.Length;          // params comes from Count
        Console.WriteLine(c(1, 2, 3));
#if BAD
        Count bad = (params xs) => xs.Length;
#endif
    }
}
