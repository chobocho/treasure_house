// 슬라이드 p14-v13-ii-trap — 초기화자 안의 ^ 는 지금의 길이로, C# 13
using System;
using System.Collections.Generic;

class Program
{
    static void Main()
    {
        var a = new List<int>([1, 2, 3]) { [^1] = 9 };
        Console.WriteLine(string.Join(" ", a));
#if DICT
        var d = new Dictionary<int, string> { [^1] = "last" };
#endif
        var b = new List<int> { [^1] = 5 };      // Count is 0 here
        Console.WriteLine(string.Join(" ", b));
    }
}
