// 슬라이드 p15-v14-sp-infer — 스팬을 거치는 형식 추론, C# 14
using System;

class Program
{
    static T First<T>(ReadOnlySpan<T> s) => s[0];
    static void Fill<T>(Span<T> s, T value) => s.Fill(value);
    static string Kind<T>(ReadOnlySpan<T> s) => typeof(T).Name;

    static void Main()
    {
        int[] nums = [5, 6, 7];
        string[] words = ["x", "y"];
        Console.WriteLine(First(nums) + " " + First(words));
        Fill(nums, 0);                       // T = int
        Console.WriteLine(string.Join(",", nums));
        Console.WriteLine(Kind(words) + " " + Kind(nums.AsSpan()));
#if MIXED
        object o = "z";
        Fill(words, o);                      // Span<T>: exact inference
#endif
    }
}
