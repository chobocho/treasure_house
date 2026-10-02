// 슬라이드 p6-v5-fe-later — 뒤 버전의 foreach 도 새 변수, C# 7.3
using System;
using System.Collections.Generic;

class App
{
    static void Main()
    {
        var pairs = new[] { ("a", 1), ("b", 2), ("c", 3) };
        var fs = new List<Func<string>>();

        // C# 7.0: deconstruction declares two fresh variables per pass.
        foreach (var (name, n) in pairs)
            fs.Add(() => name + n);

        // C# 7.3: a ref iteration variable aliases the array element.
        int[] nums = { 1, 2, 3 };
        foreach (ref int r in nums.AsSpan())
            r *= 10;

        foreach (var f in fs) Console.Write(f() + " ");
        Console.WriteLine(string.Join(",", nums));
    }
}
