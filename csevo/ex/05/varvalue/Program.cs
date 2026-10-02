// 슬라이드 p5-v4-var-value — 값 형식에는 변성이 없다, C# 4.0
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        IEnumerable<string> words = new List<string>();
        IEnumerable<object> ok = words;          // reference conversion
        Console.WriteLine(ok is IEnumerable<object>);
        IEnumerable<int> nums = new List<int>();
        Console.WriteLine(nums is IEnumerable<object>);
#if BAD
        Take(nums);                              // would need boxing
#endif
    }

    static void Take(IEnumerable<object> items) { }
}
